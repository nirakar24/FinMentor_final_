using System;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace SetuDemo.Models.Entities
{
    public class Transaction
    {
        [Key]
        [DatabaseGenerated(DatabaseGeneratedOption.Identity)]
        public int Id { get; set; }

        public int AccountId { get; set; }

        [ForeignKey("AccountId")]
        public Account Account { get; set; } = null!;

        [Required]
        [MaxLength(100)]
        public string TransactionId { get; set; } = "";

        public decimal Amount { get; set; }

        [MaxLength(20)]
        public string? Type { get; set; } // CREDIT/DEBIT

        [MaxLength(20)]
        public string? Mode { get; set; } // UPI, CASH, etc.

        public string? Narration { get; set; }

        [MaxLength(100)]
        public string? ReferenceNumber { get; set; }

        public DateTime TransactionTimestamp { get; set; }

        public DateTime? ValueDate { get; set; }

        public decimal? BalanceAfterTransaction { get; set; }

        public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
    }
}
