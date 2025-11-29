using SetuDemo.Dtos;
using SetuDemo.Models;
using System.Text.Json;

namespace SetuDemo.Services
{
    public interface IFiuClient
    {
        Task<string> GetAccessTokenAsync(CancellationToken ct = default);
        Task<(string consentId, string consentUrl)> CreateConsentAsync(CreateConsentRequestDto req, CancellationToken ct = default);
        Task<string> GetConsentStatusAsync(string consentId, CancellationToken ct = default);
        /* Task<string> CreateSessionAsync(string consentId, string fromDate, string toDate, CancellationToken ct = default);*/

        Task<(string sessionId, string status, string rawResponse)> CreateSessionAsync(string consentId, string fromIso, string toIso, CancellationToken ct = default);

        Task<(List<FetchedTransaction> transactions, List<AccountRecord> accounts)> GetSessionDataAsync(string sessionId, CancellationToken ct = default);

        Task<(string status, JsonDocument sessionDoc)> GetSessionAsync(string sessionId, CancellationToken ct = default);
    }
}
