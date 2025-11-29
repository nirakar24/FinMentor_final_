using MongoDB.Bson.Serialization.Attributes;
using MongoDB.Bson;

namespace SetuDemo.Models
{
    public class AccountRecord
    {
        [BsonId]
        public ObjectId Id { get; set; }

        [BsonElement("account_id")]
        public string AccountId { get; set; } = "";

        [BsonElement("masked_acc_number")]
        public string MaskedAccountNumber { get; set; } = "";

        [BsonElement("account_type")]
        public string AccountType { get; set; } = "";

        [BsonElement("mobile_number")]
        public string MobileNumber { get; set; } = "";

        [BsonElement("consent_mobile")]
        public string? ConsentMobile { get; set; }

        [BsonElement("link_ref_number")]
        public string LinkReferenceNumber { get; set; } = "";

        [BsonElement("fi_address")]
        public string FIAddress { get; set; } = "";

        // Holder Profile fields
        [BsonElement("holder_name")]
        public string? HolderName { get; set; }

        [BsonElement("holder_email")]
        public string? HolderEmail { get; set; }

        [BsonElement("holder_pan")]
        public string? HolderPAN { get; set; }

        [BsonElement("holder_address")]
        public string? HolderAddress { get; set; }

        [BsonElement("holder_dob")]
        public string? HolderDOB { get; set; }

        [BsonElement("holder_mobile")]
        public string? HolderMobile { get; set; }

        // Account Summary fields
        [BsonElement("current_balance")]
        public decimal? CurrentBalance { get; set; }

        [BsonElement("currency")]
        public string? Currency { get; set; }

        [BsonElement("branch")]
        public string? Branch { get; set; }

        [BsonElement("ifsc_code")]
        public string? IFSCCode { get; set; }

        [BsonElement("micr_code")]
        public string? MICRCode { get; set; }

        [BsonElement("status")]
        public string? Status { get; set; }

        [BsonElement("facility")]
        public string? Facility { get; set; }

        [BsonElement("od_limit")]
        public decimal? ODLimit { get; set; }

        [BsonElement("drawing_limit")]
        public decimal? DrawingLimit { get; set; }

        [BsonElement("opening_date")]
        public string? OpeningDate { get; set; }

        [BsonElement("balance_date_time")]
        public string? BalanceDateTime { get; set; }

        [BsonElement("updated_at")]
        public DateTime UpdatedAt { get; set; } = DateTime.UtcNow;
    }
}
