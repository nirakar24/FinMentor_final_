using System.Text.Json.Serialization;

namespace SetuDemo.Dtos
{
    public class DataRangeDto
    {
        [JsonPropertyName("from")]
        public string From { get; set; } = "";

        [JsonPropertyName("to")]
        public string To { get; set; } = "";
    }
}
