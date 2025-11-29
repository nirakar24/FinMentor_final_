using Microsoft.Extensions.Options;
using SetuDemo.Models;
using System.Net.Http.Headers;
using System.Text.Json;
using System.Text;
using SetuDemo.Dtos;

namespace SetuDemo.Services
{
    public class FiuClient : IFiuClient
    {
        private readonly IHttpClientFactory _httpFactory;
        private readonly FiuOptions _options;
        private readonly JsonSerializerOptions _json = new JsonSerializerOptions { PropertyNamingPolicy = JsonNamingPolicy.CamelCase };
        private readonly SemaphoreSlim _tokenLock = new SemaphoreSlim(1, 1);
        private string? _cachedToken;
        private DateTime _tokenExpiryUtc = DateTime.MinValue;

        public FiuClient(IHttpClientFactory factory, IOptions<FiuOptions> opt)
        {
            _httpFactory = factory;
            _options = opt.Value;
        }

        public async Task<string> GetAccessTokenAsync(CancellationToken ct = default)
        {
            if (!string.IsNullOrEmpty(_cachedToken) && DateTime.UtcNow < _tokenExpiryUtc.AddSeconds(-_options.TokenCacheBufferSeconds))
                return _cachedToken;

            await _tokenLock.WaitAsync(ct);
            try
            {
                if (!string.IsNullOrEmpty(_cachedToken) && DateTime.UtcNow < _tokenExpiryUtc.AddSeconds(-_options.TokenCacheBufferSeconds))
                    return _cachedToken;

                var client = _httpFactory.CreateClient("fiu");
                // Use absolute token endpoint (orgservice)
                var tokenEndpoint = _options.TokenEndpoint;
                var payload = new { clientID = _options.ClientId, grant_type = "client_credentials", secret = _options.ClientSecret };
                using var req = new HttpRequestMessage(HttpMethod.Post, tokenEndpoint)
                {
                    Content = new StringContent(JsonSerializer.Serialize(payload), Encoding.UTF8, "application/json")
                };

                // optionally vendor expects header "client: bridge" - uncomment if needed
                // req.Headers.Add("client","bridge");

                var resp = await client.SendAsync(req, ct);
                var raw = await resp.Content.ReadAsStringAsync(ct);
                if (!resp.IsSuccessStatusCode)
                {
                    throw new InvalidOperationException($"Token request failed {(int)resp.StatusCode}: {raw}");
                }

                using var doc = JsonDocument.Parse(raw);
                string token = "";
                if (doc.RootElement.TryGetProperty("access_token", out var at)) token = at.GetString()!;
                else if (doc.RootElement.TryGetProperty("aa_token", out var at2)) token = at2.GetString()!;
                else throw new InvalidOperationException("Token response missing access_token. Raw: " + raw);

                int expiresIn = 3600;
                if (doc.RootElement.TryGetProperty("expires_in", out var exp) && exp.TryGetInt32(out var g)) expiresIn = g;
                _cachedToken = token;
                _tokenExpiryUtc = DateTime.UtcNow.AddSeconds(expiresIn);
                return _cachedToken;
            }
            finally
            {
                _tokenLock.Release();
            }
        }

        private HttpRequestMessage PrepareRequest(HttpMethod method, string url, object? body = null, CancellationToken ct = default)
        {
            var req = new HttpRequestMessage(method, url);
            if (body != null)
                req.Content = new StringContent(JsonSerializer.Serialize(body, _json), Encoding.UTF8, "application/json");
            return req;
        }

        private async Task<HttpRequestMessage> PrepareAuthorizedRequestAsync(HttpMethod method, string url, object? body = null, CancellationToken ct = default)
        {
            var client = _httpFactory.CreateClient("fiu");
            var token = await GetAccessTokenAsync(ct);
            var req = PrepareRequest(method, url, body, ct);
            req.Headers.Authorization = new AuthenticationHeaderValue("Bearer", token);
            // exact header used by Postman / Setu
            req.Headers.Remove("x-product-instance-id");
            req.Headers.Add("x-product-instance-id", _options.ProductInstanceId);
            return req;
        }

        public async Task<(string consentId, string consentUrl)> CreateConsentAsync(CreateConsentRequestDto req, CancellationToken ct = default)
        {
            // build vendor consent body
            var body = new
            {
                consentDuration = new { unit = "MONTH", value = req.ConsentDurationMonths.ToString() },
                vua = req.Vua,
                dataRange = new { from = req.DataRange.From, to = req.DataRange.To },
                context = Array.Empty<object>()
            };

            var httpReq = await PrepareAuthorizedRequestAsync(HttpMethod.Post, "/v2/consents", body, ct);
            var client = _httpFactory.CreateClient("fiu");
            var resp = await client.SendAsync(httpReq, ct);
            var raw = await resp.Content.ReadAsStringAsync(ct);
            if (!resp.IsSuccessStatusCode)
                throw new InvalidOperationException($"CreateConsent failed {(int)resp.StatusCode}: {raw}");

            using var doc = JsonDocument.Parse(raw);
            // Try multiple locations for id and url
            string id = ExtractString(doc, new[] { "id", "data.id", "consentId", "data.consentId" });
            string url = ExtractString(doc, new[] { "url", "consentUrl", "data.consentUrl", "data.url", "redirectUrl" });

            return (id, url);
        }

        public async Task<string> GetConsentStatusAsync(string consentId, CancellationToken ct = default)
        {
            var httpReq = await PrepareAuthorizedRequestAsync(HttpMethod.Get, $"/v2/consents/{consentId}", null, ct);
            var client = _httpFactory.CreateClient("fiu");
            var resp = await client.SendAsync(httpReq, ct);
            var raw = await resp.Content.ReadAsStringAsync(ct);
            if (!resp.IsSuccessStatusCode)
                throw new InvalidOperationException($"GetConsentStatus failed {(int)resp.StatusCode}: {raw}");

            using var doc = JsonDocument.Parse(raw);
            // status often under data.status or status
            return ExtractString(doc, new[] { "data.status", "status" }) ?? "UNKNOWN";
        }

        /*  public async Task<string> CreateSessionAsync(string consentId, string fromDate, string toDate, CancellationToken ct = default)
          {
              var body = new
              {
                  consentId = consentId,
                  dataRange = new { from = fromDate, to = toDate },
                  format = "json"
              };

              var httpReq = await PrepareAuthorizedRequestAsync(HttpMethod.Post, "/v2/sessions", body, ct);
              var client = _httpFactory.CreateClient("fiu");
              var resp = await client.SendAsync(httpReq, ct);
              var raw = await resp.Content.ReadAsStringAsync(ct);
              if (!resp.IsSuccessStatusCode)
                  throw new InvalidOperationException($"CreateSession failed {(int)resp.StatusCode}: {raw}");

              using var doc = JsonDocument.Parse(raw);
              string sessionId = ExtractString(doc, new[] { "id", "data.id", "sessionId" });
              return sessionId;
          }*/


        public async Task<(string sessionId, string status, string rawResponse)> CreateSessionAsync(string consentId, string fromIso, string toIso, CancellationToken ct = default)
        {
            var body = new
            {
                consentId = consentId,
                dataRange = new { from = fromIso, to = toIso },
                format = "json"
            };

            var req = await PrepareAuthorizedRequestAsync(HttpMethod.Post, "/v2/sessions", body, ct);
            var client = _httpFactory.CreateClient("fiu");
            var resp = await client.SendAsync(req, ct);
            var raw = await resp.Content.ReadAsStringAsync(ct);
            if (!resp.IsSuccessStatusCode)
                throw new InvalidOperationException($"CreateSession failed {(int)resp.StatusCode}: {raw}");

            using var doc = JsonDocument.Parse(raw);
            // id may be at root.id or data.id depending on envelope
            string sessionId = ExtractString(doc, new[] { "id", "data.id", "sessionId" }) ?? throw new InvalidOperationException("session id not found");
            string status = ExtractString(doc, new[] { "status", "data.status" }) ?? "PENDING";
            return (sessionId, status, raw);
        }

        public async Task<(List<FetchedTransaction> transactions, List<AccountRecord> accounts)> GetSessionDataAsync(string sessionId, CancellationToken ct = default)
        {
            var httpReq = await PrepareAuthorizedRequestAsync(HttpMethod.Get, $"/v2/sessions/{sessionId}", null, ct);
            var client = _httpFactory.CreateClient("fiu");
            var resp = await client.SendAsync(httpReq, ct);
            var raw = await resp.Content.ReadAsStringAsync(ct);
            if (!resp.IsSuccessStatusCode)
                throw new InvalidOperationException($"GetSession failed {(int)resp.StatusCode}: {raw}");

            using var doc = JsonDocument.Parse(raw);
            var root = doc.RootElement;
            if (root.ValueKind == JsonValueKind.Object && root.TryGetProperty("data", out var dr) && dr.ValueKind == JsonValueKind.Object) root = dr;

            var txList = new List<FetchedTransaction>();
            var accList = new List<AccountRecord>();

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
                                // Try to extract account details from 'accInner' (data -> account)
                                JsonElement accountSource = default;
                                bool foundAccountSource = false;

                                if (dataObj.TryGetProperty("account", out var accInner) && accInner.ValueKind == JsonValueKind.Object)
                                {
                                    accountSource = accInner;
                                    foundAccountSource = true;
                                }
                                else
                                {
                                    // Fallback: try to find account details directly in dataObj
                                    accountSource = dataObj;
                                    foundAccountSource = true; 
                                }

                                // Extract Account Record if we have a source
                                var accRec = new AccountRecord();
                                if (foundAccountSource)
                                {
                                    accRec.AccountId = GetElementString(accountSource, new[] { "id", "accountId", "account_id" }) ?? "";
                                    accRec.MaskedAccountNumber = GetElementString(accountSource, new[] { "maskedAccNumber", "maskedAccountNumber", "accountNumber" }) ?? "";
                                    accRec.AccountType = GetElementString(accountSource, new[] { "type", "accountType" }) ?? "";
                                    accRec.LinkReferenceNumber = GetElementString(accountSource, new[] { "linkRefNumber", "linkReferenceNumber", "linkedAccRef" }) ?? "";
                                    accRec.FIAddress = GetElementString(accountSource, new[] { "fiAddress", "fipId" }) ?? "";

                                    // Filter: Only process deposit accounts
                                    if (!string.Equals(accRec.AccountType, "deposit", StringComparison.OrdinalIgnoreCase))
                                    {
                                        continue; // Skip non-deposit accounts
                                    }

                                    // Extract holder profile from profile.holders.holder[0]
                                    if (accountSource.TryGetProperty("profile", out var profile) && 
                                        profile.TryGetProperty("holders", out var holders) &&
                                        holders.TryGetProperty("holder", out var holderArr) && 
                                        holderArr.ValueKind == JsonValueKind.Array)
                                    {
                                        var holderList = holderArr.EnumerateArray().ToList();
                                        if (holderList.Count > 0)
                                        {
                                            var holder = holderList[0];
                                            accRec.HolderName = GetElementString(holder, new[] { "name" });
                                            accRec.HolderEmail = GetElementString(holder, new[] { "email" });
                                            accRec.HolderPAN = GetElementString(holder, new[] { "pan" });
                                            accRec.HolderAddress = GetElementString(holder, new[] { "address" });
                                            accRec.HolderDOB = GetElementString(holder, new[] { "dob" });
                                            accRec.HolderMobile = GetElementString(holder, new[] { "mobile", "mobileNumber", "phone" });
                                        }
                                    }

                                    // Extract account summary
                                    if (accountSource.TryGetProperty("summary", out var summary))
                                    {
                                        accRec.CurrentBalance = summary.TryGetProperty("currentBalance", out var cb) && decimal.TryParse(cb.GetString(), out var bal) ? bal : (decimal?)null;
                                        accRec.Currency = GetElementString(summary, new[] { "currency" });
                                        accRec.Branch = GetElementString(summary, new[] { "branch" });
                                        accRec.IFSCCode = GetElementString(summary, new[] { "ifscCode" });
                                        accRec.MICRCode = GetElementString(summary, new[] { "micrCode" });
                                        accRec.Status = GetElementString(summary, new[] { "status" });
                                        accRec.Facility = GetElementString(summary, new[] { "facility" });
                                        accRec.ODLimit = summary.TryGetProperty("currentODLimit", out var od) && decimal.TryParse(od.GetString(), out var odVal) ? odVal : (decimal?)null;
                                        accRec.DrawingLimit = summary.TryGetProperty("drawingLimit", out var dl) && decimal.TryParse(dl.GetString(), out var dlVal) ? dlVal : (decimal?)null;
                                        accRec.OpeningDate = GetElementString(summary, new[] { "openingDate" });
                                        accRec.BalanceDateTime = GetElementString(summary, new[] { "balanceDateTime" });
                                    }
                                }

                                // Find transactions array
                                JsonElement txArr = default;
                                bool foundTxs = false;

                                // Path 1: data -> account -> transactions -> transaction
                                if (dataObj.TryGetProperty("account", out var accObj) && accObj.ValueKind == JsonValueKind.Object &&
                                    accObj.TryGetProperty("transactions", out var txsObj) && txsObj.ValueKind == JsonValueKind.Object &&
                                    txsObj.TryGetProperty("transaction", out var tArr))
                                {
                                    txArr = tArr;
                                    foundTxs = true;
                                }
                                // Path 2: data -> transactions -> transaction
                                else if (dataObj.TryGetProperty("transactions", out var txsObj2) && txsObj2.ValueKind == JsonValueKind.Object &&
                                         txsObj2.TryGetProperty("transaction", out var tArr2))
                                {
                                    txArr = tArr2;
                                    foundTxs = true;
                                }

                                if (foundTxs && txArr.ValueKind == JsonValueKind.Array)
                                {
                                     foreach (var t in txArr.EnumerateArray())
                                     {
                                         var ft = new FetchedTransaction
                                         {
                                             TransactionId = GetElementString(t, new[] { "txnId", "transactionId", "id", "transaction_id" }) ?? Guid.NewGuid().ToString(),
                                             // Use account's LinkReferenceNumber as AccountId for reliable linking
                                             AccountId = accRec.LinkReferenceNumber,
                                             Date = GetElementString(t, new[] { "transactionTimestamp", "date", "transactionDate", "txnDate" }) ?? DateTime.UtcNow.ToString("o"),
                                             Amount = t.TryGetProperty("amount", out var a) && a.ValueKind != JsonValueKind.Null ? (decimal.TryParse(a.GetString(), out var amt) ? amt : 0m) : 0m,
                                             Currency = GetElementString(t, new[] { "currency" }) ?? "INR",
                                             Description = GetElementString(t, new[] { "narration", "rawDescription", "description" }) ?? "",
                                             Merchant = GetElementString(t, new[] { "merchant_name", "merchant", "payee" }) ?? "",
                                             Type = GetElementString(t, new[] { "type", "txnType", "transactionType" }) ?? "",
                                             CurrentBalance = t.TryGetProperty("currentBalance", out var cb) && cb.ValueKind != JsonValueKind.Null ? (decimal.TryParse(cb.GetString(), out var bal) ? bal : (decimal?)null) : null
                                         };
                                         txList.Add(ft);
                                     }


                                     // Check if we already added this account
                                     // Use MaskedAccountNumber as primary identifier if AccountId is empty
                                     bool isDuplicate = false;
                                     if (!string.IsNullOrEmpty(accRec.AccountId))
                                     {
                                         // If AccountId exists, check by AccountId
                                         isDuplicate = accList.Any(x => x.AccountId == accRec.AccountId);
                                     }
                                     else
                                     {
                                         // If AccountId is empty, check by MaskedAccountNumber
                                         isDuplicate = accList.Any(x => x.MaskedAccountNumber == accRec.MaskedAccountNumber);
                                     }
                                     
                                     if (!isDuplicate)
                                     {
                                         accList.Add(accRec);
                                     }
                                 }
                                }
                            }
                        }
                    }
                }


            // Fallback for flat structure if needed
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
                        Merchant = GetElementString(t, new[] { "merchant_name", "merchant", "payee" }) ?? "",
                        Type = GetElementString(t, new[] { "type", "txnType", "transactionType" }) ?? ""
                    };
                    txList.Add(ft);
                }
            }

            return (txList, accList);
        }

        public async Task<(string status, JsonDocument sessionDoc)> GetSessionAsync(string sessionId, CancellationToken ct = default)
        {
            var req = await PrepareAuthorizedRequestAsync(HttpMethod.Get, $"/v2/sessions/{sessionId}", null, ct);
            var client = _httpFactory.CreateClient("fiu");
            var resp = await client.SendAsync(req, ct);
            var raw = await resp.Content.ReadAsStringAsync(ct);
            if (!resp.IsSuccessStatusCode)
                throw new InvalidOperationException($"GetSession failed {(int)resp.StatusCode}: {raw}");

            var doc = JsonDocument.Parse(raw);
            string status = ExtractString(doc, new[] { "status", "data.status" }) ?? "UNKNOWN";
            return (status, doc);
        }


        #region helpers
        private static string? ExtractString(JsonDocument doc, string[] paths)
        {
            foreach (var p in paths)
            {
                var cur = doc.RootElement;
                var parts = p.Split('.');
                bool ok = true;
                foreach (var part in parts)
                {
                    if (cur.ValueKind == JsonValueKind.Object && cur.TryGetProperty(part, out var next))
                    {
                        cur = next;
                    }
                    else
                    {
                        ok = false; break;
                    }
                }
                if (ok && cur.ValueKind == JsonValueKind.String) return cur.GetString();
            }
            return null;
        }

        private static string? GetElementString(JsonElement el, string[] keys)
        {
            foreach (var k in keys)
            {
                if (el.ValueKind == JsonValueKind.Object && el.TryGetProperty(k, out var v) && v.ValueKind == JsonValueKind.String)
                    return v.GetString();
            }
            return null;
        }
        #endregion
    }
}
