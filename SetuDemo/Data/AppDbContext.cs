using Microsoft.EntityFrameworkCore;
using SetuDemo.Models.Entities;

namespace SetuDemo.Data
{
    public class AppDbContext : DbContext
    {
        public AppDbContext(DbContextOptions<AppDbContext> options) : base(options)
        {
        }

        public DbSet<User> Users { get; set; } = null!;
        public DbSet<Account> Accounts { get; set; } = null!;
        public DbSet<Transaction> Transactions { get; set; } = null!;
        public DbSet<Consent> Consents { get; set; } = null!;

        protected override void OnModelCreating(ModelBuilder modelBuilder)
        {
            base.OnModelCreating(modelBuilder);

            // Unique constraints
            modelBuilder.Entity<User>()
                .HasIndex(u => u.MobileNumber)
                .IsUnique();

            modelBuilder.Entity<Consent>()
                .HasIndex(c => c.ConsentId)
                .IsUnique();

            modelBuilder.Entity<Transaction>()
                .HasIndex(t => t.TransactionId)
                .IsUnique();
        }
    }
}
