using Microsoft.Extensions.Options;
using MongoDB.Driver;
using SetuDemo;
using SetuDemo.Models;
using SetuDemo.Repositories;
using SetuDemo.Services;
using Microsoft.EntityFrameworkCore;

var builder = WebApplication.CreateBuilder(args);

// Add config
builder.Configuration.AddJsonFile("appsettings.json", optional: false, reloadOnChange: true);

// Options
builder.Services.Configure<FiuOptions>(builder.Configuration.GetSection("Fiu"));
builder.Services.Configure<MongoOptions>(builder.Configuration.GetSection("Mongo"));

// HttpClient for FIU calls (base will be BaseUrl)
builder.Services.AddHttpClient("fiu", (sp, client) =>
{
    var opt = sp.GetRequiredService<IOptions<FiuOptions>>().Value;
    client.BaseAddress = new Uri(opt.BaseUrl);
    client.Timeout = TimeSpan.FromSeconds(60);
});

// Mongo
// Database Configuration
var useSql = builder.Configuration.GetValue<bool>("UseSql");

if (useSql)
{
    var connectionString = builder.Configuration.GetConnectionString("DefaultConnection");
    builder.Services.AddDbContext<SetuDemo.Data.AppDbContext>(options =>
        options.UseMySql(connectionString, Microsoft.EntityFrameworkCore.ServerVersion.AutoDetect(connectionString)));
    
    builder.Services.AddScoped<IMongoRepository, SqlRepository>();
}
else
{
    builder.Services.AddSingleton<IMongoClient>(sp =>
    {
        var m = sp.GetRequiredService<IOptions<MongoOptions>>().Value;
        return new MongoClient(m.ConnectionString);
    });
    builder.Services.AddScoped<IMongoRepository, MongoRepository>();
}

// FIU client & controller services
builder.Services.AddScoped<IFiuClient, FiuClient>();

builder.Services.AddControllers();
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();

var app = builder.Build();

// ensure indexes
using (var scope = app.Services.CreateScope())
{
    var repo = scope.ServiceProvider.GetRequiredService<IMongoRepository>();
    await repo.EnsureIndexesAsync();
}

if (app.Environment.IsDevelopment())
{
    app.UseDeveloperExceptionPage();
    app.UseSwagger();
    app.UseSwaggerUI();
}

app.UseRouting();
app.MapControllers();
app.Run();
