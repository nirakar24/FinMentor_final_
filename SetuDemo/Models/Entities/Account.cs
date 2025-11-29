using System;
using System.Collections.Generic;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace SetuDemo.Models.Entities
{
    public class Account
    {
        [Key]
        [DatabaseGenerated(DatabaseGeneratedOption.Identity)]
        public int Id { get; set; }

        public int UserId { get; set; }

        [ForeignKey("UserId")]
        public User User { get; set; } = null!;

        [MaxLength(100)]
        public string? FiuAccountId { get; set; } // The ID returned by FIU (e.g., UUID)

        [MaxLength(50)]
        public string MaskedAccountNumber { get; set; } = "";

        [MaxLength(100)]
        public string? LinkReferenceNumber { get; set; }

        [MaxLength(50)]
        public string? AccountType { get; set; }

        [MaxLength(20)]
        public string? Status { get; set; }

        [MaxLength(100)]
        public string? FIAddress { get; set; }

        [MaxLength(100)]
        public string? Branch { get; set; }

        [MaxLength(20)]
        public string? IFSC { get; set; }

        [MaxLength(20)]
        public string? MICR { get; set; }

        [MaxLength(10)]
        public string Currency { get; set; } = "INR";

        public decimal? CurrentBalance { get; set; }
        public decimal? ODLimit { get; set; }
        public decimal? DrawingLimit { get; set; }

        [MaxLength(50)]
        public string? Facility { get; set; }

        public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
        public DateTime UpdatedAt { get; set; } = DateTime.UtcNow;

        // Navigation properties
        public ICollection<Transaction> Transactions { get; set; } = new List<Transaction>();
    }
}
