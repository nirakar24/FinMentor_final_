using System.Text.Json.Serialization;

namespace SetuDemo.Models
{
    // DTO for parsed vendor transaction
    public class FetchedTransaction
    {
        [JsonPropertyName("transactionId")]
        public string TransactionId { get; set; } = "";

        [JsonPropertyName("accountId")]
        public string AccountId { get; set; } = "";

        [JsonPropertyName("date")]
        public string Date { get; set; } = "";

        [JsonPropertyName("amount")]
        public decimal Amount { get; set; }

        [JsonPropertyName("currency")]
        public string Currency { get; set; } = "INR";

        [JsonPropertyName("description")]
        public string Description { get; set; } = "";

        [JsonPropertyName("merchant")]
        public string Merchant { get; set; } = "";

        [JsonPropertyName("type")]
        public string Type { get; set; } = "";

        [JsonPropertyName("currentBalance")]
        public decimal? CurrentBalance { get; set; }
    }
}
