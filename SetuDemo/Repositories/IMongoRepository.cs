using SetuDemo.Models;

namespace SetuDemo.Repositories
{
    public interface IMongoRepository
    {
        Task EnsureIndexesAsync();
        Task UpsertTransactionsAsync(IEnumerable<TransactionDocument> transactions, CancellationToken ct = default);
        Task InsertConsentRecordAsync(ConsentRecord rec, CancellationToken ct = default);
        Task<ConsentRecord?> GetConsentByIdAsync(string consentId, CancellationToken ct = default);
        Task<ConsentRecord?> GetActiveConsentByMobileAsync(string mobileNumber, CancellationToken ct = default);
        Task UpdateConsentStatusAsync(string consentId, string status, CancellationToken ct = default);
        Task<List<TransactionDocument>> GetRecentTransactionsAsync(string mobileNumber, int limit = 50, CancellationToken ct = default);
        Task<List<TransactionDocument>> GetRecentTransactionsAsync(int limit = 50, CancellationToken ct = default);
        Task<List<TransactionDocument>> GetTransactionsByDateRangeAsync(string mobileNumber, DateTime from, DateTime to, CancellationToken ct = default);
        Task UpsertAccountAsync(AccountRecord account, CancellationToken ct = default);
        Task<ConsentRecord?> GetConsentDataWithDetailsAsync(string mobileNumber, CancellationToken ct = default);
    }
}
