using Microsoft.AspNetCore.Builder;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;

var builder = WebApplication.CreateBuilder(args);

// Controllers
builder.Services.AddControllers();

// (Optional) Swagger for easy testing in browser
builder.Services.AddEndpointsApiExplorer();

var app = builder.Build();
app.UseHttpsRedirection();

// IMPORTANT: maps attribute-routed controllers like [Route("api/algorithms")]
app.MapControllers();

// Simple health endpoint
app.MapGet("/health", () => Results.Ok(new { status = "ok" }));

app.Run();