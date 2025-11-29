using MongoDB.Bson.Serialization.Attributes;
using MongoDB.Bson;

namespace SetuDemo.Models
{
    public class TransactionDocument
    {
        [BsonId]
        public ObjectId Id { get; set; }

        [BsonElement("transaction_id")]
        public string TransactionId { get; set; } = "";

        [BsonElement("account_id")]
        public string AccountId { get; set; } = "";

        [BsonElement("timestamp")]
        public DateTime Timestamp { get; set; }

        [BsonElement("amount")]
        public decimal Amount { get; set; }

        [BsonElement("currency")]
        public string Currency { get; set; } = "INR";

        [BsonElement("raw_description")]
        public string RawDescription { get; set; } = "";

        [BsonElement("merchant_name")]
        public string MerchantName { get; set; } = "";

        [BsonElement("source")]
        public string Source { get; set; } = "SETU";

        [BsonElement("imported_at")]
        public DateTime ImportedAt { get; set; } = DateTime.UtcNow;

        [BsonElement("mobile_number")]
        public string MobileNumber { get; set; } = "";

        [BsonElement("type")]
        public string Type { get; set; } = "";

        [BsonElement("current_balance")]
        public decimal? CurrentBalance { get; set; }
    }
}
