using System.Text.Json.Serialization;

namespace SetuDemo.Dtos
{
    public class CreateConsentRequestDto
    {
        [JsonPropertyName("vua")]
        public string Vua { get; set; } = ""; // e.g. "7039663536@onemoney"

        [JsonPropertyName("dataRange")]
        public DataRangeDto DataRange { get; set; } = new();

        [JsonPropertyName("consentDurationMonths")]
        public int ConsentDurationMonths { get; set; } = 24;
    }
}
