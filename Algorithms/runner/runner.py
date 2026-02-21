import argparse
import importlib.util
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple


def eprint(*args: Any) -> None:
    print(*args, file=sys.stderr)


def load_module_from_path(module_name: str, file_path: Path):
    spec = importlib.util.spec_from_file_location(module_name, str(file_path))
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load module spec from: {file_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[attr-defined]
    return module


def case_to_call_args(case: Dict[str, Any]) -> Tuple[List[Any], Dict[str, Any]]:
    """
    Supports a few simple case shapes:

    1) {"args": [...], "expected": ...}
    2) {"kwargs": {...}, "expected": ...}
    3) {"input": [...], "expected": ...}     -> treated as args
    4) {"input": {...}, "expected": ...}     -> treated as kwargs
    5) {"input": <single>, "expected": ...}  -> treated as one positional arg
    """
    if "args" in case:
        args = case["args"]
        if not isinstance(args, list):
            raise ValueError(f"'args' must be a list, got {type(args)}")
        return args, {}

    if "kwargs" in case:
        kwargs = case["kwargs"]
        if not isinstance(kwargs, dict):
            raise ValueError(f"'kwargs' must be a dict, got {type(kwargs)}")
        return [], kwargs

    if "input" in case:
        inp = case["input"]
        if isinstance(inp, list):
            return inp, {}
        if isinstance(inp, dict):
            return [], inp
        return [inp], {}

    raise ValueError("Case must include one of: args, kwargs, or input")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--id", required=True, help="Algorithm id, e.g. 'two_sum'")
    ap.add_argument("--algo-dir", required=True, help="Directory containing algorithm .py files")
    ap.add_argument("--data-dir", required=True, help="Directory containing data .json files")
    args = ap.parse_args()

    algo_id = args.id

    algo_dir = Path(args.algo_dir).resolve()
    data_dir = Path(args.data_dir).resolve()

    algo_file = (algo_dir / f"{algo_id}.py").resolve()
    data_file = (data_dir / f"{algo_id}.json").resolve()

    if not algo_file.exists():
        eprint(f"Algorithm file not found: {algo_file}")
        return 2

    if not data_file.exists():
        eprint(f"Data file not found: {data_file}")
        return 3

    # Load test data
    try:
        data = json.loads(data_file.read_text(encoding="utf-8"))
    except Exception as ex:
        eprint(f"Failed to parse JSON data file {data_file}: {ex}")
        return 4

    cases = data.get("cases")
    if not isinstance(cases, list):
        eprint(f"Data file must contain a top-level 'cases' list. Got: {type(cases)}")
        return 5

    # Import algorithm module by file path
    try:
        module = load_module_from_path(f"algo_{algo_id}", algo_file)
    except Exception as ex:
        eprint(f"Failed to import algorithm module {algo_file}: {ex}")
        return 6

    # Require a solve() function for v1
    solve = getattr(module, "solve", None)
    if not callable(solve):
        eprint(f"Algorithm file must define a callable solve(...). Not found in: {algo_file}")
        return 7

    results: List[Dict[str, Any]] = []
    started = time.time()

    for i, case in enumerate(cases):
        if not isinstance(case, dict):
            results.append({
                "index": i,
                "pass": False,
                "error": f"Case must be an object/dict, got {type(case)}",
            })
            continue

        expected = case.get("expected", None)

        try:
            call_args, call_kwargs = case_to_call_args(case)
            t0 = time.time()
            actual = solve(*call_args, **call_kwargs)
            dt_ms = int((time.time() - t0) * 1000)

            passed = (actual == expected) if "expected" in case else True

            results.append({
                "index": i,
                "input": case.get("input", None),
                "args": case.get("args", None),
                "kwargs": case.get("kwargs", None),
                "expected": expected,
                "actual": actual,
                "pass": passed,
                "time_ms": dt_ms,
            })
        except Exception as ex:
            results.append({
                "index": i,
                "input": case.get("input", None),
                "args": case.get("args", None),
                "kwargs": case.get("kwargs", None),
                "expected": expected,
                "pass": False,
                "error": str(ex),
            })

    total_ms = int((time.time() - started) * 1000)

    out = {
        "algorithm_id": algo_id,
        "case_count": len(results),
        "passed_count": sum(1 for r in results if r.get("pass") is True),
        "failed_count": sum(1 for r in results if r.get("pass") is False),
        "total_time_ms": total_ms,
        "cases": results,
    }

    print(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())