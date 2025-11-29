using System;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace SetuDemo.Models.Entities
{
    public class Consent
    {
        [Key]
        [DatabaseGenerated(DatabaseGeneratedOption.Identity)]
        public int Id { get; set; }

        public int UserId { get; set; }

        [ForeignKey("UserId")]
        public User User { get; set; } = null!;

        [Required]
        [MaxLength(100)]
        public string ConsentId { get; set; } = "";

        [MaxLength(100)]
        public string Vua { get; set; } = "";

        [MaxLength(20)]
        public string Status { get; set; } = "CREATED";

        public DateTime DataRangeFrom { get; set; }
        public DateTime DataRangeTo { get; set; }

        public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
        public DateTime? Expiry { get; set; }
    }
}
