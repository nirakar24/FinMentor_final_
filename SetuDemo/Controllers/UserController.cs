using Microsoft.AspNetCore.Mvc;
using SetuDemo.Models;
using SetuDemo.Repositories;
using SetuDemo.Services;

namespace SetuDemo.Controllers
{
    [Route("api/[controller]")]
    [ApiController]
    public class UserController : ControllerBase
    {
        private readonly IMongoRepository _repo;
        private readonly IFiuClient _fiuClient;
        private readonly ILogger<UserController> _logger;

        public UserController(IMongoRepository repo, IFiuClient fiuClient, ILogger<UserController> logger)
        {
            _repo = repo;
            _fiuClient = fiuClient;
            _logger = logger;
        }

        [HttpPost("onboard")]
        public async Task<IActionResult> OnboardUser([FromBody] OnboardUserRequest request, CancellationToken ct)
        {
            if (string.IsNullOrWhiteSpace(request.MobileNumber))
                return BadRequest("Mobile number is required.");

            // 1. Check for existing consent
            var existingConsent = await _repo.GetActiveConsentByMobileAsync(request.MobileNumber, ct);

            // Check if consent exists and is valid (e.g., not expired, status is ACTIVE/READY)
            // For simplicity, we assume if it exists and status is READY/ACTIVE, it's good.
            // Also checking date range validity as per requirement "valid date range < current date"
            // Interpreting "valid date range < current date" as "Consent Expiry is in the future" or similar.
            // The user said: "if the consent data is in valid date range < current date". This is slightly ambiguous.
            // I will assume it means "If we have a valid consent that covers the current period".
            
            bool isConsentValid = existingConsent != null && 
                                  (existingConsent.Status == "READY" || existingConsent.Status == "ACTIVE" || existingConsent.Status == "CREATED") &&
                                  DateTime.Parse(existingConsent.DataRange.To) > DateTime.UtcNow;

            if (isConsentValid)
            {
                _logger.LogInformation("Found valid consent {ConsentId} for mobile {Mobile}", existingConsent!.ConsentId, request.MobileNumber);

                // 2. Create Session for last 1 month
                var now = DateTime.UtcNow;
                var from = now.AddYears(-1);
                var to = now;

                try 
                {
                    var sessionResp = await _fiuClient.CreateSessionAsync(existingConsent.ConsentId, from.ToString("O"), to.ToString("O"), ct);
                    
                    // 3. Fetch Data
                    var (transactions, accounts) = await _fiuClient.GetSessionDataAsync(sessionResp.sessionId, ct);

                    _logger.LogInformation("Fetched {AccountCount} accounts and {TransactionCount} transactions from FIU", 
                        accounts.Count, transactions.Count);

                    // 4. Store Account Details FIRST (transactions need accounts to exist)
                    // Each account uses its holder's mobile number (from holder profile)
                    // But we also track the consent's mobile for querying purposes
                    foreach (var acc in accounts)
                    {
                        acc.ConsentMobile = request.MobileNumber; // Track consent mobile for querying
                        await _repo.UpsertAccountAsync(acc, ct);
                    }

                    // 5. Store Transactions with Mobile Number
                    var txDocs = transactions.Select(t => new TransactionDocument
                    {
                        TransactionId = t.TransactionId,
                        AccountId = t.AccountId,
                        Timestamp = DateTime.Parse(t.Date),
                        Amount = t.Amount,
                        Currency = t.Currency,
                        RawDescription = t.Description,
                        MerchantName = t.Merchant,
                        Source = "SETU",
                        ImportedAt = DateTime.UtcNow,
                        MobileNumber = request.MobileNumber,
                        Type = t.Type,
                        CurrentBalance = t.CurrentBalance
                    }).ToList();

                    _logger.LogInformation("Attempting to insert {TransactionCount} transactions", txDocs.Count);

                    await _repo.UpsertTransactionsAsync(txDocs, ct);

                    return Ok(new { 
                        Message = "Transactions fetched successfully", 
                        AccountsCount = accounts.Count,
                        TransactionsFetched = txDocs.Count,
                        Accounts = accounts.Select(a => new { a.MaskedAccountNumber, a.AccountType }).ToList()
                    });
                }
                catch (Exception ex)
                {
                    _logger.LogError(ex, "Error fetching data for consent {ConsentId}", existingConsent.ConsentId);
                    return StatusCode(500, new { Error = "Failed to fetch data", Details = ex.Message });
                }
            }
            else
            {
                _logger.LogInformation("No valid consent found for mobile {Mobile}. Creating new consent.", request.MobileNumber);

                // 5. Create New Consent (2 years: 1 year back, 1 year forward)
                // User said: "prev year to current year and currentyear to next year 2024 to 2026"
                // So roughly -1 year to +1 year from now.
                var now = DateTime.UtcNow;
                var from = now.AddYears(-1);
                var to = now.AddYears(1);

                try
                {
                    var reqDto = new SetuDemo.Dtos.CreateConsentRequestDto
                    {
                        Vua = $"{request.MobileNumber}@onemoney", // Assuming a default VUA handle
                        DataRange = new SetuDemo.Dtos.DataRangeDto 
                        { 
                            From = from.ToString("O"), 
                            To = to.ToString("O") 
                        }
                    };

                    var (consentId, consentUrl) = await _fiuClient.CreateConsentAsync(reqDto, ct);

                    // Store Consent Record
                    var newConsent = new ConsentRecord
                    {
                        ConsentId = consentId,
                        Vua = reqDto.Vua,
                        MobileNumber = request.MobileNumber,
                        DataRange = reqDto.DataRange,
                        Status = "CREATED",
                        CreatedAt = DateTime.UtcNow
                    };

                    await _repo.InsertConsentRecordAsync(newConsent, ct);

                    return Ok(new 
                    { 
                        Message = "Consent created. Please approve.", 
                        ConsentId = consentId, 
                        Url = consentUrl 
                    });
                }
                catch (Exception ex)
                {
                    _logger.LogError(ex, "Error creating consent for mobile {Mobile}", request.MobileNumber);
                    return StatusCode(500, new { Error = "Failed to create consent", Details = ex.Message });
                }
            }
        }


        [HttpGet("transactions")]
        public async Task<IActionResult> GetTransactions(
            [FromQuery] string mobileNumber, 
            [FromQuery] DateTime? from = null, 
            [FromQuery] DateTime? to = null, 
            CancellationToken ct = default)
        {
            if (string.IsNullOrWhiteSpace(mobileNumber))
                return BadRequest("Mobile number is required.");

            // Validate date range if provided
            if (from.HasValue && to.HasValue && to < from)
                return BadRequest("'to' date must be greater than or equal to 'from' date.");

            try
            {
                // Get consent for this mobile number
                var consent = await _repo.GetActiveConsentByMobileAsync(mobileNumber, ct);
                
                if (consent == null)
                    return NotFound($"No consent found for mobile number: {mobileNumber}");

                // Use AppDbContext to get hierarchical data (need to inject it)
                // For now, return simple format
                List<TransactionDocument> transactions;
                
                if (from.HasValue && to.HasValue)
                {
                    transactions = await _repo.GetTransactionsByDateRangeAsync(mobileNumber, from.Value, to.Value, ct);
                }
                else
                {
                    transactions = await _repo.GetRecentTransactionsAsync(mobileNumber, int.MaxValue, ct);
                }
                
                return Ok(new { Count = transactions.Count, Transactions = transactions });
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error fetching transaction history for mobile {Mobile}", mobileNumber);
                return StatusCode(500, new { Error = "Failed to fetch transactions", Details = ex.Message });
            }
        }
    }

    public class OnboardUserRequest
    {
        public string MobileNumber { get; set; } = "";
    }

    public class TransactionHistoryRequest
    {
        public string MobileNumber { get; set; } = "";
        public DateTime From { get; set; }
        public DateTime To { get; set; }
    }


}
