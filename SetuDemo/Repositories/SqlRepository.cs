using Microsoft.EntityFrameworkCore;
using SetuDemo.Data;
using SetuDemo.Models;
using SetuDemo.Models.Entities;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;

namespace SetuDemo.Repositories
{
    public class SqlRepository : IMongoRepository
    {
        private readonly AppDbContext _context;

        public SqlRepository(AppDbContext context)
        {
            _context = context;
        }

        public Task EnsureIndexesAsync()
        {
            // Indexes are handled by EF Core migrations
            return Task.CompletedTask;
        }

        public async Task<ConsentRecord?> GetActiveConsentByMobileAsync(string mobileNumber, CancellationToken ct = default)
        {
            var consent = await _context.Consents
                .Include(c => c.User)
                .Where(c => c.User.MobileNumber == mobileNumber)
                .OrderByDescending(c => c.CreatedAt)
                .FirstOrDefaultAsync(ct);

            if (consent == null) return null;

            return new ConsentRecord
            {
                ConsentId = consent.ConsentId,
                Vua = consent.Vua,
                Status = consent.Status,
                CreatedAt = consent.CreatedAt,
                MobileNumber = consent.User.MobileNumber,
                DataRange = new Dtos.DataRangeDto
                {
                    From = consent.DataRangeFrom.ToString("yyyy-MM-ddTHH:mm:ssZ"),
                    To = consent.DataRangeTo.ToString("yyyy-MM-ddTHH:mm:ssZ")
                }
            };
        }

        public async Task<ConsentRecord?> GetConsentByIdAsync(string consentId, CancellationToken ct = default)
        {
            var consent = await _context.Consents
                .Include(c => c.User)
                .FirstOrDefaultAsync(c => c.ConsentId == consentId, ct);

            if (consent == null) return null;

            return new ConsentRecord
            {
                ConsentId = consent.ConsentId,
                Vua = consent.Vua,
                Status = consent.Status,
                CreatedAt = consent.CreatedAt,
                MobileNumber = consent.User.MobileNumber,
                DataRange = new Dtos.DataRangeDto
                {
                    From = consent.DataRangeFrom.ToString("yyyy-MM-ddTHH:mm:ssZ"),
                    To = consent.DataRangeTo.ToString("yyyy-MM-ddTHH:mm:ssZ")
                }
            };
        }

        public async Task<List<TransactionDocument>> GetRecentTransactionsAsync(string mobileNumber, int limit = 50, CancellationToken ct = default)
        {
            // First, try to find a consent with this mobile number
            var consent = await _context.Consents
                .Include(c => c.User)
                .Where(c => c.User.MobileNumber == mobileNumber)
                .OrderByDescending(c => c.CreatedAt)
                .FirstOrDefaultAsync(ct);

            if (consent != null)
            {
                // Get all transactions from accounts created around the consent time (within 1 hour)
                var consentTime = consent.CreatedAt;
                var txs = await _context.Transactions
                    .Include(t => t.Account)
                    .ThenInclude(a => a.User)
                    .Where(t => t.Account.CreatedAt >= consentTime.AddHours(-1) && t.Account.CreatedAt <= consentTime.AddHours(1))
                    .OrderByDescending(t => t.TransactionTimestamp)
                    .Take(limit)
                    .ToListAsync(ct);

                return txs.Select(MapToDocument).ToList();
            }
            else
            {
                // Fallback: get transactions for this user's mobile number only
                var txs = await _context.Transactions
                    .Include(t => t.Account)
                    .ThenInclude(a => a.User)
                    .Where(t => t.Account.User.MobileNumber == mobileNumber)
                    .OrderByDescending(t => t.TransactionTimestamp)
                    .Take(limit)
                    .ToListAsync(ct);

                return txs.Select(MapToDocument).ToList();
            }
        }

        public async Task<List<TransactionDocument>> GetRecentTransactionsAsync(int limit = 50, CancellationToken ct = default)
        {
            var txs = await _context.Transactions
                .Include(t => t.Account)
                .ThenInclude(a => a.User)
                .OrderByDescending(t => t.TransactionTimestamp)
                .Take(limit)
                .ToListAsync(ct);

            return txs.Select(MapToDocument).ToList();
        }

        public async Task<List<TransactionDocument>> GetTransactionsByDateRangeAsync(string mobileNumber, DateTime from, DateTime to, CancellationToken ct = default)
        {
            // First, try to find a consent with this mobile number
            var consent = await _context.Consents
                .Include(c => c.User)
                .Where(c => c.User.MobileNumber == mobileNumber)
                .OrderByDescending(c => c.CreatedAt)
                .FirstOrDefaultAsync(ct);

            if (consent != null)
            {
                // Get all transactions from accounts created around the consent time (within 1 hour)
                var consentTime = consent.CreatedAt;
                var txs = await _context.Transactions
                    .Include(t => t.Account)
                    .ThenInclude(a => a.User)
                    .Where(t => t.Account.CreatedAt >= consentTime.AddHours(-1) && 
                               t.Account.CreatedAt <= consentTime.AddHours(1) &&
                               t.TransactionTimestamp >= from && 
                               t.TransactionTimestamp <= to)
                    .OrderByDescending(t => t.TransactionTimestamp)
                    .ToListAsync(ct);

                return txs.Select(MapToDocument).ToList();
            }
            else
            {
                // Fallback: get transactions for this user's mobile number only
                var txs = await _context.Transactions
                    .Include(t => t.Account)
                    .ThenInclude(a => a.User)
                    .Where(t => t.Account.User.MobileNumber == mobileNumber && 
                           t.TransactionTimestamp >= from && 
                           t.TransactionTimestamp <= to)
                    .OrderByDescending(t => t.TransactionTimestamp)
                    .ToListAsync(ct);

                return txs.Select(MapToDocument).ToList();
            }
        }

        public async Task InsertConsentRecordAsync(ConsentRecord rec, CancellationToken ct = default)
        {
            var user = await GetOrCreateUserAsync(rec.MobileNumber, ct);

            var consent = new Consent
            {
                UserId = user.Id,
                ConsentId = rec.ConsentId,
                Vua = rec.Vua,
                Status = rec.Status,
                CreatedAt = rec.CreatedAt,
                DataRangeFrom = DateTime.Parse(rec.DataRange.From),
                DataRangeTo = DateTime.Parse(rec.DataRange.To)
            };

            _context.Consents.Add(consent);
            await _context.SaveChangesAsync(ct);
        }

        public async Task UpdateConsentStatusAsync(string consentId, string status, CancellationToken ct = default)
        {
            var consent = await _context.Consents.FirstOrDefaultAsync(c => c.ConsentId == consentId, ct);
            if (consent != null)
            {
                consent.Status = status;
                await _context.SaveChangesAsync(ct);
            }
        }

        public async Task UpsertAccountAsync(AccountRecord account, CancellationToken ct = default)
        {
            // Use holder's mobile number from the account's holder profile
            var mobileNumber = account.HolderMobile ?? account.MobileNumber;
            
            if (string.IsNullOrEmpty(mobileNumber))
            {
                throw new InvalidOperationException("Account must have either HolderMobile or MobileNumber");
            }
            
            var user = await GetOrCreateUserAsync(mobileNumber, ct);

            // Update user with holder profile data
            if (!string.IsNullOrEmpty(account.HolderName)) user.Name = account.HolderName;
            if (!string.IsNullOrEmpty(account.HolderEmail)) user.Email = account.HolderEmail;
            if (!string.IsNullOrEmpty(account.HolderPAN)) user.PAN = account.HolderPAN;
            if (!string.IsNullOrEmpty(account.HolderAddress)) user.Address = account.HolderAddress;
            if (!string.IsNullOrEmpty(account.HolderDOB) && DateTime.TryParse(account.HolderDOB, out var dob)) user.DateOfBirth = dob;

            // Try to find by FiuAccountId first, then by MaskedAccountNumber
            Account? existing = null;
            
            if (!string.IsNullOrEmpty(account.AccountId))
            {
                existing = await _context.Accounts
                    .FirstOrDefaultAsync(a => a.FiuAccountId == account.AccountId && a.UserId == user.Id, ct);
            }

            if (existing == null)
            {
                existing = await _context.Accounts
                    .FirstOrDefaultAsync(a => a.MaskedAccountNumber == account.MaskedAccountNumber && a.UserId == user.Id, ct);
            }

            if (existing == null)
            {
                existing = new Account
                {
                    UserId = user.Id,
                    FiuAccountId = account.AccountId,
                    MaskedAccountNumber = account.MaskedAccountNumber,
                    LinkReferenceNumber = account.LinkReferenceNumber,
                    AccountType = account.AccountType,
                    FIAddress = account.FIAddress,
                    // Account summary fields
                    CurrentBalance = account.CurrentBalance,
                    Currency = account.Currency ?? "INR",
                    Branch = account.Branch,
                    IFSC = account.IFSCCode,
                    MICR = account.MICRCode,
                    Status = account.Status,
                    Facility = account.Facility,
                    ODLimit = account.ODLimit,
                    DrawingLimit = account.DrawingLimit,
                    CreatedAt = DateTime.UtcNow
                };
                _context.Accounts.Add(existing);
            }
            else
            {
                // Update fields
                if (!string.IsNullOrEmpty(account.AccountId)) existing.FiuAccountId = account.AccountId;
                existing.LinkReferenceNumber = account.LinkReferenceNumber;
                existing.AccountType = account.AccountType;
                existing.FIAddress = account.FIAddress;
                
                // Update account summary fields
                if (account.CurrentBalance.HasValue) existing.CurrentBalance = account.CurrentBalance;
                if (!string.IsNullOrEmpty(account.Currency)) existing.Currency = account.Currency;
                if (!string.IsNullOrEmpty(account.Branch)) existing.Branch = account.Branch;
                if (!string.IsNullOrEmpty(account.IFSCCode)) existing.IFSC = account.IFSCCode;
                if (!string.IsNullOrEmpty(account.MICRCode)) existing.MICR = account.MICRCode;
                if (!string.IsNullOrEmpty(account.Status)) existing.Status = account.Status;
                if (!string.IsNullOrEmpty(account.Facility)) existing.Facility = account.Facility;
                if (account.ODLimit.HasValue) existing.ODLimit = account.ODLimit;
                if (account.DrawingLimit.HasValue) existing.DrawingLimit = account.DrawingLimit;
                
                existing.UpdatedAt = DateTime.UtcNow;
            }

            await _context.SaveChangesAsync(ct);
        }

        public async Task UpsertTransactionsAsync(IEnumerable<TransactionDocument> transactions, CancellationToken ct = default)
        {
            // Group transactions by AccountId to minimize DB lookups
            var txGroups = transactions.GroupBy(t => t.AccountId);

            foreach (var group in txGroups)
            {
                var accountId = group.Key;
                // Find the account entity by LinkReferenceNumber (which is stored in transaction's AccountId)
                var account = await _context.Accounts.FirstOrDefaultAsync(a => a.LinkReferenceNumber == accountId, ct);
                
                if (account == null)
                {
                    // Fallback: try by FiuAccountId if LinkReferenceNumber didn't match
                    account = await _context.Accounts.FirstOrDefaultAsync(a => a.FiuAccountId == accountId, ct);
                    
                    if (account == null)
                    {
                        // Account not found, skip these transactions
                        continue;
                    }
                }

                foreach (var doc in group)
                {
                    // Check if transaction exists
                    var exists = await _context.Transactions.AnyAsync(t => t.TransactionId == doc.TransactionId, ct);
                    if (!exists)
                    {
                        var tx = new Transaction
                        {
                            AccountId = account.Id,
                            TransactionId = doc.TransactionId,
                            Amount = doc.Amount,
                            Type = doc.Type,
                            TransactionTimestamp = doc.Timestamp,
                            Narration = doc.RawDescription,
                            Mode = doc.Source,
                            BalanceAfterTransaction = doc.CurrentBalance,
                            CreatedAt = DateTime.UtcNow
                        };
                        _context.Transactions.Add(tx);
                    }
                }
            }
            await _context.SaveChangesAsync(ct);
        }

        private async Task<User> GetOrCreateUserAsync(string mobileNumber, CancellationToken ct)
        {
            var user = await _context.Users.FirstOrDefaultAsync(u => u.MobileNumber == mobileNumber, ct);
            if (user == null)
            {
                user = new User { MobileNumber = mobileNumber };
                _context.Users.Add(user);
                await _context.SaveChangesAsync(ct);
            }
            return user;
        }

        private TransactionDocument MapToDocument(Transaction t)
        {
            return new TransactionDocument
            {
                TransactionId = t.TransactionId,
                Amount = t.Amount,
                Timestamp = t.TransactionTimestamp,
                RawDescription = t.Narration ?? "",
                MobileNumber = t.Account.User.MobileNumber,
                // Map other fields
            };
        }

        public async Task<ConsentRecord?> GetConsentDataWithDetailsAsync(string mobileNumber, CancellationToken ct = default)
        {
            // This method is not needed for SQL implementation
            // The controller will build the hierarchical structure directly from SQL queries
            return await GetActiveConsentByMobileAsync(mobileNumber, ct);
        }
    }
}
