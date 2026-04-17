#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import statistics
import time
import urllib.error
import urllib.request
from pathlib import Path


def call_endpoint(endpoint: str, api_key: str, payload: dict, timeout: int) -> dict:
    started = time.time()
    req = urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            return {"status": resp.status, "body": body, "elapsed": round(time.time() - started, 2)}
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            body = json.loads(raw)
        except Exception:
            body = raw
        return {"status": exc.code, "body": body, "elapsed": round(time.time() - started, 2)}


def percentile(values: list[float], ratio: float) -> float:
    ordered = sorted(values)
    if not ordered:
        return 0.0
    idx = max(0, min(len(ordered) - 1, int(round((len(ordered) - 1) * ratio))))
    return ordered[idx]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--endpoint", required=True)
    parser.add_argument("--api-key", required=True)
    parser.add_argument("--cases", default=str(Path(__file__).with_name("sample_eval_cases.json")))
    parser.add_argument("--timeout", type=int, default=180)
    args = parser.parse_args()

    test_cases = json.loads(Path(args.cases).read_text(encoding="utf-8"))
    summaries = []
    for case in test_cases:
        result = call_endpoint(args.endpoint, args.api_key, case["payload"], args.timeout)
        summary = {"name": case["name"], "status": result["status"], "elapsed": result["elapsed"]}
        print(json.dumps(summary, ensure_ascii=False))
        summaries.append(summary)

    latencies = [item["elapsed"] for item in summaries]
    print(json.dumps({
        "total": len(summaries),
        "ok": sum(1 for item in summaries if item["status"] == 200),
        "p50_s": round(statistics.median(latencies), 2) if latencies else None,
        "p95_s": round(percentile(latencies, 0.95), 2) if latencies else None,
        "max_s": round(max(latencies), 2) if latencies else None,
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
