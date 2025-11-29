namespace SetuDemo.Models
{
    public class FiuOptions
    {
        public string BaseUrl { get; set; } = "";
        public string ProductInstanceId { get; set; } = "";
        public string ClientId { get; set; } = "";
        public string ClientSecret { get; set; } = "";
        public string TokenEndpoint { get; set; } = ""; // absolute URL for org login
        public int TokenCacheBufferSeconds { get; set; } = 60;
        public int PollingIntervalSeconds { get; set; } = 3;
        public int PollingMaxAttempts { get; set; } = 60;
    }
}
