namespace SetuDemo.Dtos
{
    public class ConsentDataResponseDto
    {
        public ConsentInfoDto Consent { get; set; } = null!;
        public string MobileNumber { get; set; } = "";
        public List<UserWithAccountsDto> Users { get; set; } = new();
    }

    public class ConsentInfoDto
    {
        public string ConsentId { get; set; } = "";
        public string Status { get; set; } = "";
        public DataRangeDto DataRange { get; set; } = null!;
        public DateTime CreatedAt { get; set; }
    }

    public class UserWithAccountsDto
    {
        public int UserId { get; set; }
        public string MobileNumber { get; set; } = "";
        public string? Name { get; set; }
        public string? Email { get; set; }
        public string? PAN { get; set; }
        public string? Address { get; set; }
        public DateTime? DateOfBirth { get; set; }
        public List<AccountWithTransactionsDto> Accounts { get; set; } = new();
    }

    public class AccountWithTransactionsDto
    {
        public int AccountId { get; set; }
        public string MaskedAccountNumber { get; set; } = "";
        public string? AccountType { get; set; }
        public string? Status { get; set; }
        public string? Branch { get; set; }
        public string? IFSC { get; set; }
        public string? Currency { get; set; }
        public decimal? CurrentBalance { get; set; }
        public List<TransactionDto> Transactions { get; set; } = new();
    }

    public class TransactionDto
    {
        public int TransactionId { get; set; }
        public string TransactionRefId { get; set; } = "";
        public decimal Amount { get; set; }
        public string? Type { get; set; }
        public DateTime TransactionTimestamp { get; set; }
        public string? Narration { get; set; }
        public string? Mode { get; set; }
        public decimal? BalanceAfterTransaction { get; set; }
        public string? ReferenceNumber { get; set; }
        public DateTime? ValueDate { get; set; }
    }
}
