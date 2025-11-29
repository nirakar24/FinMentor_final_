using Microsoft.AspNetCore.Mvc;
using Microsoft.Extensions.Options;
using SetuDemo.Dtos;
using SetuDemo.Models;
using SetuDemo.Repositories;
using SetuDemo.Services;
using System.Text.Json;

namespace SetuDemo.Controllers
{
    [ApiController]
    [Route("api/[controller]")]
    public class ConsentsController : ControllerBase
    {
        private readonly IFiuClient _fiu;
        private readonly IMongoRepository _repo;
        private readonly FiuOptions _options;
        private readonly ILogger<ConsentsController> _logger;

        public ConsentsController(IFiuClient fiu, IMongoRepository repo, IOptions<FiuOptions> opt, ILogger<ConsentsController> logger)
        {
            _fiu = fiu;
            _repo = repo;
            _options = opt.Value;
            _logger = logger;
        }

        // 1) Create consent: accepts mobile@onemoney (vua) + dataRange
        [HttpPost]
        public async Task<IActionResult> CreateConsent([FromBody] CreateConsentRequestDto req, CancellationToken ct)
        {
            if (req == null || string.IsNullOrWhiteSpace(req.Vua))
                return BadRequest("vua is required");

            try
            {
                // call FIU to create consent
                (string consentId, string consentUrl) = await _fiu.CreateConsentAsync(req, ct);

                // persist consent
                var rec = new ConsentRecord
                {
                    ConsentId = consentId,
                    Vua = req.Vua,
                    DataRange = req.DataRange,
                    Status = "CREATED",
                    CreatedAt = DateTime.UtcNow
                };
                await _repo.InsertConsentRecordAsync(rec, ct);

                return Ok(new { consent_id = consentId, consent_url = consentUrl });
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "CreateConsent failed for vua={vua}", req?.Vua);
                return StatusCode(500, new { error = "CreateConsent failed", details = ex.Message });
            }
        }

        // 2) Fetch transactions for consentId: polls for APPROVED, creates session, gets data, stores
        [HttpPost("{consentId}/fetch")]
        public async Task<IActionResult> FetchData(string consentId, CancellationToken ct)
        {
            if (string.IsNullOrEmpty(consentId)) return BadRequest("consentId required");

            // get stored consent
            var stored = await _repo.GetConsentByIdAsync(consentId, ct);
            if (stored == null) return NotFound("consent not found in DB; please create consent first.");

            try
            {
                // 1) Poll consent status until APPROVED (or timeout)
                string consentStatus = "";
                int attempts = 0;
                while (attempts++ < _options.PollingMaxAttempts)
                {
                    consentStatus = await _fiu.GetConsentStatusAsync(consentId, ct);
                    _logger.LogInformation("Consent {consentId} status: {status}", consentId, consentStatus);

                    if (string.Equals(consentStatus, "ACTIVE", StringComparison.OrdinalIgnoreCase))
                    {
                        break;
                    }

                    if (string.Equals(consentStatus, "REJECTED", StringComparison.OrdinalIgnoreCase))
                    {
                        await _repo.UpdateConsentStatusAsync(consentId, "REJECTED", ct);
                        return BadRequest(new { error = "Consent rejected by user" });
                    }

                    await Task.Delay(TimeSpan.FromSeconds(_options.PollingIntervalSeconds), ct);
                }

                if (!string.Equals(consentStatus, "ACTIVE", StringComparison.OrdinalIgnoreCase))
                {
                    return BadRequest(new { error = "Consent not approved in time", status = consentStatus });
                }

                // 2) Create session (fi fetch)
                string fromDate = stored.DataRange.From;
                string toDate = stored.DataRange.To;
                var (sessionId, sessionStatus, rawSessionResp) = await _fiu.CreateSessionAsync(consentId, fromDate, toDate, ct);

                _logger.LogInformation("Created session {sessionId} with initial status {status}", sessionId, sessionStatus);

                // 3) Poll session until transactions appear (COMPLETED / SUCCESS)
                attempts = 0;
                JsonDocument? completedSessionDoc = null;
                while (attempts++ < _options.PollingMaxAttempts)
                {
                    var (sessStatus, sessDoc) = await _fiu.GetSessionAsync(sessionId, ct);
                    _logger.LogInformation("Session {sessionId} poll attempt {attempt} status={status}", sessionId, attempts, sessStatus);

                    if (string.Equals(sessStatus, "COMPLETED", StringComparison.OrdinalIgnoreCase) ||
                        string.Equals(sessStatus, "SUCCESS", StringComparison.OrdinalIgnoreCase) || string.Equals(sessStatus, "FAILED", StringComparison.OrdinalIgnoreCase))
                    {
                        completedSessionDoc = sessDoc;
                        break;
                    }

                    if (string.Equals(sessStatus, "FAILED", StringComparison.OrdinalIgnoreCase))
                    {
                        _logger.LogWarning("Session {sessionId} failed. Raw: {raw}", sessionId, sessDoc.RootElement.ToString());
                        return BadRequest(new { error = "Session failed", sessionId });
                    }

                    await Task.Delay(TimeSpan.FromSeconds(_options.PollingIntervalSeconds), ct);
                }

                if (completedSessionDoc == null)
                {
                    return BadRequest(new { error = "Session did not complete in time", sessionId });
                }

                // 4) Extract transactions. Prefer using FIU client helper; fallback to GetSessionDataAsync
                List<FetchedTransaction> fetched;
                try
                {
                    // Use dedicated endpoint to get parsed transactions if available
                    var (txs, _) = await _fiu.GetSessionDataAsync(sessionId, ct);
                    fetched = txs;
                }
                catch (NotImplementedException)
                {
                    // If GetSessionDataAsync not implemented, attempt to parse from the completedSessionDoc
                    fetched = ParseTransactionsFromSessionDoc(completedSessionDoc);
                }

                if (fetched == null || fetched.Count == 0)
                {
                    return BadRequest(new { error = "No transactions returned by FI", sessionId });
                }

                // 5) Map to docs and upsert
                var docs = fetched.Select(ft =>
                {
                    DateTime ts;
                    if (!DateTime.TryParse(ft.Date, out ts)) ts = DateTime.UtcNow;
                    return new TransactionDocument
                    {
                        TransactionId = ft.TransactionId,
                        AccountId = ft.AccountId,
                        Timestamp = ts,
                        Amount = ft.Amount,
                        Currency = string.IsNullOrWhiteSpace(ft.Currency) ? "INR" : ft.Currency,
                        RawDescription = ft.Description ?? "",
                        MerchantName = ft.Merchant ?? "",
                        Source = "SETU",
                        ImportedAt = DateTime.UtcNow
                    };
                }).ToList();

                await _repo.UpsertTransactionsAsync(docs, ct);
                await _repo.UpdateConsentStatusAsync(consentId, "COMPLETED", ct);

                var recent = await _repo.GetRecentTransactionsAsync(50, ct);
                return Ok(new { inserted = docs.Count, session_id = sessionId, sample = recent.Take(20) });
            }
            catch (OperationCanceledException)
            {
                _logger.LogWarning("FetchData cancelled for consent {consentId}", consentId);
                return StatusCode(499, new { error = "Request cancelled" }); // client closed request
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "FetchData failed for consent {consentId}", consentId);
                return StatusCode(500, new { error = "FetchData failed", details = ex.Message });
            }
        }

        // Local helper: parse transactions from session JsonDocument (tolerant)
        private static List<FetchedTransaction> ParseTransactionsFromSessionDoc(JsonDocument doc)
        {
            var root = doc.RootElement;
            if (root.ValueKind == JsonValueKind.Object && root.TryGetProperty("data", out var d) && d.ValueKind == JsonValueKind.Object) root = d;

            var txList = new List<FetchedTransaction>();

            // Handle nested structure: fips -> accounts -> data -> account -> transactions -> transaction
            if (root.ValueKind == JsonValueKind.Object && root.TryGetProperty("fips", out var fipsArr) && fipsArr.ValueKind == JsonValueKind.Array)
            {
                foreach (var fip in fipsArr.EnumerateArray())
                {
                    if (fip.ValueKind == JsonValueKind.Object && fip.TryGetProperty("accounts", out var accArr) && accArr.ValueKind == JsonValueKind.Array)
                    {
                        foreach (var acc in accArr.EnumerateArray())
                        {
                            if (acc.ValueKind == JsonValueKind.Object && 
                                acc.TryGetProperty("data", out var dataObj) && dataObj.ValueKind == JsonValueKind.Object)
                            {
                                // Check for "account" object wrapper inside data
                                if (dataObj.TryGetProperty("account", out var accInner) && accInner.ValueKind == JsonValueKind.Object &&
                                    accInner.TryGetProperty("transactions", out var txsObj) && txsObj.ValueKind == JsonValueKind.Object &&
                                    txsObj.TryGetProperty("transaction", out var txArr) && txArr.ValueKind == JsonValueKind.Array)
                                {
                                     foreach (var t in txArr.EnumerateArray())
                                     {
                                         var ft = new FetchedTransaction
                                         {
                                             TransactionId = GetElementString(t, new[] { "txnId", "transactionId", "id", "transaction_id" }) ?? Guid.NewGuid().ToString(),
                                             AccountId = GetElementString(t, new[] { "accountId", "account_id" }) ?? "",
                                             Date = GetElementString(t, new[] { "transactionTimestamp", "date", "transactionDate", "txnDate" }) ?? DateTime.UtcNow.ToString("o"),
                                             Amount = t.TryGetProperty("amount", out var a) && a.ValueKind != JsonValueKind.Null ? (decimal.TryParse(a.GetString(), out var amt) ? amt : 0m) : 0m,
                                             Currency = GetElementString(t, new[] { "currency" }) ?? "INR",
                                             Description = GetElementString(t, new[] { "narration", "rawDescription", "description" }) ?? "",
                                             Merchant = GetElementString(t, new[] { "merchant_name", "merchant", "payee" }) ?? ""
                                         };
                                         txList.Add(ft);
                                     }
                                }
                                // Fallback: sometimes transactions might be directly under data (without account wrapper)
                                else if (dataObj.TryGetProperty("transactions", out var txsObj2) && txsObj2.ValueKind == JsonValueKind.Object &&
                                         txsObj2.TryGetProperty("transaction", out var txArr2) && txArr2.ValueKind == JsonValueKind.Array)
                                {
                                     foreach (var t in txArr2.EnumerateArray())
                                     {
                                         var ft = new FetchedTransaction
                                         {
                                             TransactionId = GetElementString(t, new[] { "txnId", "transactionId", "id", "transaction_id" }) ?? Guid.NewGuid().ToString(),
                                             AccountId = GetElementString(t, new[] { "accountId", "account_id" }) ?? "",
                                             Date = GetElementString(t, new[] { "transactionTimestamp", "date", "transactionDate", "txnDate" }) ?? DateTime.UtcNow.ToString("o"),
                                             Amount = t.TryGetProperty("amount", out var a) && a.ValueKind != JsonValueKind.Null ? (decimal.TryParse(a.GetString(), out var amt) ? amt : 0m) : 0m,
                                             Currency = GetElementString(t, new[] { "currency" }) ?? "INR",
                                             Description = GetElementString(t, new[] { "narration", "rawDescription", "description" }) ?? "",
                                             Merchant = GetElementString(t, new[] { "merchant_name", "merchant", "payee" }) ?? ""
                                         };
                                         txList.Add(ft);
                                     }
                                }
                            }
                        }
                    }
                }
            }
            else if (root.ValueKind == JsonValueKind.Object && root.TryGetProperty("transactions", out var txArr) && txArr.ValueKind == JsonValueKind.Array)
            {
                foreach (var t in txArr.EnumerateArray())
                {
                    var ft = new FetchedTransaction
                    {
                        TransactionId = GetElementString(t, new[] { "transactionId", "id", "txnId", "transaction_id" }) ?? Guid.NewGuid().ToString(),
                        AccountId = GetElementString(t, new[] { "accountId", "account_id" }) ?? "",
                        Date = GetElementString(t, new[] { "date", "transactionDate", "txnDate" }) ?? DateTime.UtcNow.ToString("o"),
                        Amount = t.TryGetProperty("amount", out var a) && a.ValueKind != JsonValueKind.Null ? a.GetDecimal() : 0m,
                        Currency = GetElementString(t, new[] { "currency" }) ?? "INR",
                        Description = GetElementString(t, new[] { "rawDescription", "description", "narration" }) ?? "",
                        Merchant = GetElementString(t, new[] { "merchant_name", "merchant", "payee" }) ?? ""
                    };
                    txList.Add(ft);
                }
            }
            return txList;
        }

        private static string? GetElementString(JsonElement el, string[] keys)
        {
            foreach (var k in keys)
            {
                if (el.ValueKind == JsonValueKind.Object && el.TryGetProperty(k, out var v))
                {
                    if (v.ValueKind == JsonValueKind.String) return v.GetString();
                    // sometimes numeric ids or nested structures - convert to string
                    return v.ToString();
                }
            }
            return null;
        }
    }
}
