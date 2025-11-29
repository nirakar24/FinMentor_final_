using Microsoft.Extensions.Options;
using MongoDB.Driver;
using SetuDemo.Models;

namespace SetuDemo.Repositories
{
    public class MongoRepository : IMongoRepository
    {
        private readonly IMongoCollection<TransactionDocument> _txCol;
        private readonly IMongoCollection<ConsentRecord> _consentCol;
        private readonly IMongoCollection<AccountRecord> _accCol;

        public MongoRepository(IMongoClient client, IOptions<MongoOptions> opt)
        {
            var o = opt.Value;
            var db = client.GetDatabase(o.Database);
            _txCol = db.GetCollection<TransactionDocument>(o.TransactionsCollection);
            _consentCol = db.GetCollection<ConsentRecord>(o.ConsentsCollection);
            _accCol = db.GetCollection<AccountRecord>(o.AccountsCollection);
        }

        public async Task EnsureIndexesAsync()
        {
            var txIndex = Builders<TransactionDocument>.IndexKeys.Ascending(x => x.TransactionId);
            await _txCol.Indexes.CreateOneAsync(new CreateIndexModel<TransactionDocument>(txIndex, new CreateIndexOptions { Unique = true }));
            var consentIndex = Builders<ConsentRecord>.IndexKeys.Ascending(x => x.ConsentId);
            await _consentCol.Indexes.CreateOneAsync(new CreateIndexModel<ConsentRecord>(consentIndex, new CreateIndexOptions { Unique = true }));
        }

        public async Task UpsertTransactionsAsync(IEnumerable<TransactionDocument> transactions, CancellationToken ct = default)
        {
            var models = new List<WriteModel<TransactionDocument>>();
            foreach (var t in transactions)
            {
                var filter = Builders<TransactionDocument>.Filter.Eq(x => x.TransactionId, t.TransactionId);
                var update = Builders<TransactionDocument>.Update
                    .SetOnInsert(x => x.TransactionId, t.TransactionId)
                    .Set(x => x.AccountId, t.AccountId)
                    .Set(x => x.Timestamp, t.Timestamp)
                    .Set(x => x.Amount, t.Amount)
                    .Set(x => x.Currency, t.Currency)
                    .Set(x => x.RawDescription, t.RawDescription)
                    .Set(x => x.MerchantName, t.MerchantName)
                    .Set(x => x.Source, t.Source)
                    .Set(x => x.ImportedAt, t.ImportedAt)
                    .Set(x => x.MobileNumber, t.MobileNumber);

                models.Add(new UpdateOneModel<TransactionDocument>(filter, update) { IsUpsert = true });
            }

            if (models.Count > 0)
            {
                await _txCol.BulkWriteAsync(models, cancellationToken: ct);
            }
        }

        public async Task InsertConsentRecordAsync(ConsentRecord rec, CancellationToken ct = default)
        {
            var filter = Builders<ConsentRecord>.Filter.Eq(x => x.ConsentId, rec.ConsentId);
            var existing = await _consentCol.Find(filter).FirstOrDefaultAsync(ct);
            if (existing == null)
                await _consentCol.InsertOneAsync(rec, cancellationToken: ct);
        }

        public async Task<ConsentRecord?> GetConsentByIdAsync(string consentId, CancellationToken ct = default)
        {
            return await _consentCol.Find(x => x.ConsentId == consentId).FirstOrDefaultAsync(ct);
        }

        public async Task<ConsentRecord?> GetActiveConsentByMobileAsync(string mobileNumber, CancellationToken ct = default)
        {
            // Find the most recent consent for this mobile number
            // You might want to add status checks (e.g. ACTIVE or READY) depending on your logic
            // For now, we just get the latest created one.
            return await _consentCol.Find(x => x.MobileNumber == mobileNumber)
                .SortByDescending(x => x.CreatedAt)
                .FirstOrDefaultAsync(ct);
        }

        public async Task UpdateConsentStatusAsync(string consentId, string status, CancellationToken ct = default)
        {
            var update = Builders<ConsentRecord>.Update.Set(x => x.Status, status);
            await _consentCol.UpdateOneAsync(x => x.ConsentId == consentId, update, cancellationToken: ct);
        }

        public async Task<List<TransactionDocument>> GetRecentTransactionsAsync(string mobileNumber, int limit = 50, CancellationToken ct = default)
        {
            return await _txCol.Find(x => x.MobileNumber == mobileNumber)
                .SortByDescending(x => x.Timestamp)
                .Limit(limit)
                .ToListAsync(ct);
        }

        public async Task<List<TransactionDocument>> GetRecentTransactionsAsync(int limit = 50, CancellationToken ct = default)
        {
            return await _txCol.Find(FilterDefinition<TransactionDocument>.Empty)
                .SortByDescending(x => x.Timestamp)
                .Limit(limit)
                .ToListAsync(ct);
        }

        public async Task<List<TransactionDocument>> GetTransactionsByDateRangeAsync(string mobileNumber, DateTime from, DateTime to, CancellationToken ct = default)
        {
            var filter = Builders<TransactionDocument>.Filter.And(
                Builders<TransactionDocument>.Filter.Eq(x => x.MobileNumber, mobileNumber),
                Builders<TransactionDocument>.Filter.Gte(x => x.Timestamp, from),
                Builders<TransactionDocument>.Filter.Lte(x => x.Timestamp, to)
            );

            return await _txCol.Find(filter)
                .SortByDescending(x => x.Timestamp)
                .ToListAsync(ct);
        }

        public async Task UpsertAccountAsync(AccountRecord account, CancellationToken ct = default)
        {
            var filter = Builders<AccountRecord>.Filter.Eq(x => x.MobileNumber, account.MobileNumber);
            await _accCol.ReplaceOneAsync(filter, account, new ReplaceOptions { IsUpsert = true }, ct);
        }

        public async Task<ConsentRecord?> GetConsentDataWithDetailsAsync(string mobileNumber, CancellationToken ct = default)
        {
            // For MongoDB, just return the consent - the controller will build the structure
            return await GetActiveConsentByMobileAsync(mobileNumber, ct);
        }
    }
}
