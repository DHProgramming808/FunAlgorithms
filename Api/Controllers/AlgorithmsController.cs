using Microsoft.AspNetCore.Mvc;
using System.Diagnostics;
using System.Text;
using System.Text.Json;
using System;
using System.IO;
using System.Linq;

namespace Api.Controllers;

[ApiController]
[Route("api/algorithms")]
public class AlgorithmsController : ControllerBase
{
    private static readonly string RepoRoot =
        Path.GetFullPath(Path.Combine(AppContext.BaseDirectory, "..", "..", "..", ".."));

    private static readonly string PyDir = Path.Combine(RepoRoot, "Algorithms", "python");
    private static readonly string DataDir = Path.Combine(RepoRoot, "Algorithms", "data");

    [HttpGet("{id}/run")]
    public async Task<IActionResult> Run([FromRoute] string id)
    {
        // 1) Validate ID to prevent path traversal / weird filenames
        if (!IsSafeId(id))
            return BadRequest(new { error = "Invalid algorithm id." });

        // 2) Resolve paths
        var pyFile = Path.Combine(PyDir, $"{id}.py");
        var dataFile = Path.Combine(DataDir, $"{id}.json");

        if (!System.IO.File.Exists(pyFile))
            return NotFound(new { error = $"Algorithm '{id}' not found." });

        if (!System.IO.File.Exists(dataFile))
            return NotFound(new { error = $"Data file for '{id}' not found." });

        // 3) Run python
        var result = await RunPython(id);

        if (!result.Success)
            return StatusCode(500, new { error = "Python execution failed.", details = result.Error });

        // 4) Ensure python returned valid JSON (optional but nice)
        try
        {
            using var doc = JsonDocument.Parse(result.Stdout);
            return Content(result.Stdout, "application/json", Encoding.UTF8);
        }
        catch
        {
            return StatusCode(500, new { error = "Python did not return valid JSON.", raw = result.Stdout });
        }
    }

    [HttpGet("{id}/code")]
    public IActionResult GetCode([FromRoute] string id)
    {
        if (!IsSafeId(id))
            return BadRequest(new { error = "Invalid algorithm id." });

        var pyFile = Path.Combine(PyDir, $"{id}.py");
        if (!System.IO.File.Exists(pyFile))
            return NotFound(new { error = $"Algorithm '{id}' not found." });

        var bytes = System.IO.File.ReadAllBytes(pyFile);

        return File(
            bytes,
            "text/plain; charset=utf-8",
            $"{id}.py"
        );
    }

    [HttpGet]
    public IActionResult ListAlgorithms()
    {
        if (!Directory.Exists(PyDir))
            return Ok(new { algorithms = Array.Empty<string>() });

        var ids = Directory.EnumerateFiles(PyDir, "*.py", SearchOption.TopDirectoryOnly)
            .Select(Path.GetFileNameWithoutExtension)
            .Where(name => !string.IsNullOrWhiteSpace(name))
            // optional: hide private/helper files like _runner.py if you ever place them here
            .Where(name => !name.StartsWith("_"))
            // enforce the same safety rules you use for routing
            .Where(IsSafeId)
            .OrderBy(name => name, StringComparer.OrdinalIgnoreCase)
            .ToArray();

        return Ok(new { algorithms = ids });
    }

    private static bool IsSafeId(string id)
    {
        // allow letters, numbers, underscore, dash only
        // (tighten/loosen as you like)
        foreach (var ch in id)
        {
            if (!(char.IsLetterOrDigit(ch) || ch == '_' || ch == '-'))
                return false;
        }
        return id.Length > 0 && id.Length <= 64;
    }

    private static async Task<(bool Success, string Stdout, string Error)> RunPython(string algorithmId)
    {
        // Uses `python` from PATH. You can swap to `python3` if needed.
        var runnerPath = Path.Combine(RepoRoot, "Algorithms", "runner", "runner.py");

        if (!System.IO.File.Exists(runnerPath))
            return (false, "", $"Runner not found at: {runnerPath}");

        // Uses `python` from PATH. Swap to python3 if needed.
        var psi = new ProcessStartInfo
        {
            FileName = "python",
            Arguments =
                $"\"{runnerPath}\" " +
                $"--id \"{algorithmId}\" " +
                $"--algo-dir \"{PyDir}\" " +
                $"--data-dir \"{DataDir}\"",
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            UseShellExecute = false,
            CreateNoWindow = true,
        };

        using var p = Process.Start(psi);
        if (p == null) return (false, "", "Failed to start python process.");

        var stdout = await p.StandardOutput.ReadToEndAsync();
        var stderr = await p.StandardError.ReadToEndAsync();
        await p.WaitForExitAsync();

        if (p.ExitCode != 0)
            return (false, stdout, stderr);

        return (true, stdout, stderr);
    }
}