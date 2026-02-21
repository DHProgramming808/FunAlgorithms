import argparse
import json
from pathlib import Path

def solve(x: int, y: int) -> int:
    return x + y

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    args = ap.parse_args()

    data_path = Path(args.data)
    cases = json.loads(data_path.read_text(encoding="utf-8"))

    results = []
    for c in cases["cases"]:
        x = c["x"]
        y = c["y"]
        expected = c["expected"]
        actual = solve(x, y)
        results.append({
            "input": {"x": x, "y": y},
            "expected": expected,
            "actual": actual,
            "pass": actual == expected
        })

    out = {
        "algorithm_id": data_path.stem,
        "count": len(results),
        "cases": results
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()