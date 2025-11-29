namespace SetuDemo.Models
{
    public class MongoOptions
    {
        public string ConnectionString { get; set; } = "mongodb://localhost:27017";
        public string Database { get; set; } = "finmentor";
        public string TransactionsCollection { get; set; } = "transactions";
        public string ConsentsCollection { get; set; } = "consents";
        public string AccountsCollection { get; set; } = "accounts";
    }
}
