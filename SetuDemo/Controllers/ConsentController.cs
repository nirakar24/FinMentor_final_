using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using SetuDemo.Data;
using SetuDemo.Dtos;

namespace SetuDemo.Controllers
{
    [Route("api/[controller]")]
    [ApiController]
    public class ConsentController : ControllerBase
    {
        private readonly AppDbContext _context;

        public ConsentController(AppDbContext context)
        {
            _context = context;
        }

        [HttpGet("data")]
        public async Task<IActionResult> GetConsentData(
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

            // Get consent for this mobile number
            var consent = await _context.Consents
                .Include(c => c.User)
                .Where(c => c.User.MobileNumber == mobileNumber)
                .OrderByDescending(c => c.CreatedAt)
                .FirstOrDefaultAsync(ct);

            if (consent == null)
                return NotFound($"No consent found for mobile number: {mobileNumber}");

            // Get all users whose accounts have this consent mobile
            var users = await _context.Users
                .Include(u => u.Accounts)
                    .ThenInclude(a => a.Transactions)
                .Where(u => u.Accounts.Any(a => a.LinkReferenceNumber != null))
                .ToListAsync(ct);

            // Filter users to only those with accounts linked to this consent
            var relevantUsers = users
                .Where(u => u.Accounts.Any(a => 
                    // Check if this account belongs to this consent (via mobile or other linking)
                    u.MobileNumber == mobileNumber || 
                    u.Accounts.Any(acc => acc.CreatedAt >= consent.CreatedAt.AddMinutes(-5) && 
                                         acc.CreatedAt <= consent.CreatedAt.AddMinutes(5))
                ))
                .Select(u => new UserWithAccountsDto
                {
                    UserId = u.Id,
                    MobileNumber = u.MobileNumber,
                    Name = u.Name,
                    Email = u.Email,
                    PAN = u.PAN,
                    Address = u.Address,
                    DateOfBirth = u.DateOfBirth,
                    Accounts = u.Accounts
                        .Select(a => new AccountWithTransactionsDto
                        {
                            AccountId = a.Id,
                            MaskedAccountNumber = a.MaskedAccountNumber,
                            AccountType = a.AccountType,
                            Status = a.Status,
                            Branch = a.Branch,
                            IFSC = a.IFSC,
                            Currency = a.Currency,
                            CurrentBalance = a.CurrentBalance,
                            Transactions = a.Transactions
                                .Where(t => (!from.HasValue || t.TransactionTimestamp >= from.Value) &&
                                           (!to.HasValue || t.TransactionTimestamp <= to.Value))
                                .Select(t => new TransactionDto
                                {
                                    TransactionId = t.Id,
                                    TransactionRefId = t.TransactionId,
                                    Amount = t.Amount,
                                    Type = t.Type,
                                    TransactionTimestamp = t.TransactionTimestamp,
                                    Narration = t.Narration,
                                    Mode = t.Mode,
                                    BalanceAfterTransaction = t.BalanceAfterTransaction,
                                    ReferenceNumber = t.ReferenceNumber,
                                    ValueDate = t.ValueDate
                                })
                                .OrderByDescending(t => t.TransactionTimestamp)
                                .ToList()
                        })
                        .ToList()
                })
                .ToList();

            var response = new ConsentDataResponseDto
            {
                Consent = new ConsentInfoDto
                {
                    ConsentId = consent.ConsentId,
                    Status = consent.Status,
                    DataRange = new DataRangeDto
                    {
                        From = consent.DataRangeFrom.ToString("yyyy-MM-ddTHH:mm:ssZ"),
                        To = consent.DataRangeTo.ToString("yyyy-MM-ddTHH:mm:ssZ")
                    },
                    CreatedAt = consent.CreatedAt
                },
                MobileNumber = mobileNumber,
                Users = relevantUsers
            };

            // Calculate counts
            var usersCount = relevantUsers.Count;
            var accountsCount = relevantUsers.Sum(u => u.Accounts.Count);
            var transactionsCount = relevantUsers.Sum(u => u.Accounts.Sum(a => a.Transactions.Count));

            return Ok(new
            {
                ConsentCount = 1,
                UsersCount = usersCount,
                AccountsCount = accountsCount,
                TransactionsCount = transactionsCount,
                Data = response
            });
        }

        [HttpGet("all")]
        public async Task<IActionResult> GetAllConsents(
            [FromQuery] DateTime? from = null,
            [FromQuery] DateTime? to = null,
            CancellationToken ct = default)
        {
            // Validate date range if provided
            if (from.HasValue && to.HasValue && to < from)
                return BadRequest("'to' date must be greater than or equal to 'from' date.");

            try
            {
                // Get all consents with their users, accounts, and transactions in one query
                var consents = await _context.Consents
                    .Include(c => c.User)
                        .ThenInclude(u => u.Accounts)
                            .ThenInclude(a => a.Transactions)
                    .OrderByDescending(c => c.CreatedAt)
                    .ToListAsync(ct);

                var allConsentData = new List<ConsentDataResponseDto>();

                // Track processed user IDs to avoid duplicates across consents
                var processedUserIds = new HashSet<int>();

                foreach (var consent in consents)
                {
                    var mobileNumber = consent.User.MobileNumber;
                    var consentTime = consent.CreatedAt;

                    // Get users with accounts created around this consent time
                    var consentUsers = await _context.Users
                        .Include(u => u.Accounts)
                            .ThenInclude(a => a.Transactions)
                        .Where(u => u.Accounts.Any(a => 
                            a.CreatedAt >= consentTime.AddMinutes(-5) && 
                            a.CreatedAt <= consentTime.AddMinutes(5)))
                        .ToListAsync(ct);

                    // Filter to only users not already processed and with accounts in this consent's time window
                    var relevantUsers = consentUsers
                        .Where(u => !processedUserIds.Contains(u.Id))
                        .Select(u => new
                        {
                            User = u,
                            // Only include accounts created in this consent's time window
                            ConsentAccounts = u.Accounts
                                .Where(a => a.CreatedAt >= consentTime.AddMinutes(-5) && 
                                           a.CreatedAt <= consentTime.AddMinutes(5))
                                .ToList()
                        })
                        .Where(x => x.ConsentAccounts.Any())
                        .Select(x => new UserWithAccountsDto
                        {
                            UserId = x.User.Id,
                            MobileNumber = x.User.MobileNumber,
                            Name = x.User.Name,
                            Email = x.User.Email,
                            PAN = x.User.PAN,
                            Address = x.User.Address,
                            DateOfBirth = x.User.DateOfBirth,
                            Accounts = x.ConsentAccounts
                                .Select(a => new AccountWithTransactionsDto
                                {
                                    AccountId = a.Id,
                                    MaskedAccountNumber = a.MaskedAccountNumber,
                                    AccountType = a.AccountType,
                                    Status = a.Status,
                                    Branch = a.Branch,
                                    IFSC = a.IFSC,
                                    Currency = a.Currency,
                                    CurrentBalance = a.CurrentBalance,
                                    Transactions = a.Transactions
                                        .Where(t => (!from.HasValue || t.TransactionTimestamp >= from.Value) &&
                                                   (!to.HasValue || t.TransactionTimestamp <= to.Value))
                                        .Select(t => new TransactionDto
                                        {
                                            TransactionId = t.Id,
                                            TransactionRefId = t.TransactionId,
                                            Amount = t.Amount,
                                            Type = t.Type,
                                            TransactionTimestamp = t.TransactionTimestamp,
                                            Narration = t.Narration,
                                            Mode = t.Mode,
                                            BalanceAfterTransaction = t.BalanceAfterTransaction,
                                            ReferenceNumber = t.ReferenceNumber,
                                            ValueDate = t.ValueDate
                                        })
                                        .OrderByDescending(t => t.TransactionTimestamp)
                                        .ToList()
                                })
                                .ToList()
                        })
                        .ToList();

                    // Mark these users as processed
                    foreach (var user in relevantUsers)
                    {
                        processedUserIds.Add(user.UserId);
                    }

                    allConsentData.Add(new ConsentDataResponseDto
                    {
                        Consent = new ConsentInfoDto
                        {
                            ConsentId = consent.ConsentId,
                            Status = consent.Status,
                            DataRange = new DataRangeDto
                            {
                                From = consent.DataRangeFrom.ToString("yyyy-MM-ddTHH:mm:ssZ"),
                                To = consent.DataRangeTo.ToString("yyyy-MM-ddTHH:mm:ssZ")
                            },
                            CreatedAt = consent.CreatedAt
                        },
                        MobileNumber = mobileNumber,
                        Users = relevantUsers
                    });
                }

                // Calculate total counts
                var totalUsersCount = allConsentData.Sum(c => c.Users.Count);
                var totalAccountsCount = allConsentData.Sum(c => c.Users.Sum(u => u.Accounts.Count));
                var totalTransactionsCount = allConsentData.Sum(c => c.Users.Sum(u => u.Accounts.Sum(a => a.Transactions.Count)));

                return Ok(new
                {
                    ConsentCount = allConsentData.Count,
                    UsersCount = totalUsersCount,
                    AccountsCount = totalAccountsCount,
                    TransactionsCount = totalTransactionsCount,
                    Consents = allConsentData
                });
            }
            catch (Exception ex)
            {
                return StatusCode(500, new { Error = "Failed to fetch all consents", Details = ex.Message });
            }
        }
    }
}
