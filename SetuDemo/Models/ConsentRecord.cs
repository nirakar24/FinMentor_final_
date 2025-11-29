using MongoDB.Bson.Serialization.Attributes;
using MongoDB.Bson;
using SetuDemo.Dtos;

namespace SetuDemo.Models
{
    public class ConsentRecord
    {
        [BsonId]
        public ObjectId Id { get; set; }

        [BsonElement("consent_id")]
        public string ConsentId { get; set; } = "";

        [BsonElement("vua")]
        public string Vua { get; set; } = "";

        [BsonElement("data_range")]
        public DataRangeDto DataRange { get; set; } = new DataRangeDto();

        [BsonElement("status")]
        public string Status { get; set; } = "CREATED";

        [BsonElement("created_at")]
        public DateTime CreatedAt { get; set; } = DateTime.UtcNow;

        [BsonElement("mobile_number")]
        public string MobileNumber { get; set; } = "";
    }

}
