"""
fuzz_api.py — Dynamic Application Security Testing (DAST) API fuzzer.

Tests the FastAPI server endpoints against malformed inputs, SQL injection attempts,
oversized inputs, and type mismatches, ensuring no uncaught 500 crashes.
"""

from __future__ import annotations

import sys
from fastapi.testclient import TestClient
from pipeline.src.api_server import app

client = TestClient(app)


def run_fuzz_scan() -> int:
    print("====================================================")
    print("STARTING DAST SECURITY SCAN: API FUZZER")
    print("====================================================")

    fuzz_payloads = [
        {"indicator": "a" * 10000, "value": 10.0},  # Oversized field
        {"indicator": "spot_price", "value": "string-instead-of-float"},  # Type mismatch
        {"indicator": "spot_price", "value": None},  # Null value validation
        {"indicator": "spot_price'; DROP TABLE anomalies;--", "value": 100.0},  # SQL injection test
        {"indicator": "<script>alert('xss')</script>", "value": 200.0},  # XSS payload
        {"indicator": "", "value": -1.0},  # Empty string bounds
        {},  # Empty object
    ]

    failed = False
    for payload in fuzz_payloads:
        try:
            response = client.post("/api/v1/webhooks/financial", json=payload)
            # The API should reject these with 422 Unprocessable Entity or process them cleanly (200),
            # but it MUST NEVER crash with a 500 Internal Server Error.
            if response.status_code == 500:
                print(f"[-] CRITICAL: Server crashed with 500 on payload: {payload}")
                failed = True
            else:
                print(f"[+] PASS: Payload rejected or processed cleanly ({response.status_code})")
        except Exception as exc:
            print(f"[-] CRITICAL: Client raised uncaught exception on payload {payload}: {exc}")
            failed = True

    print("====================================================")
    if failed:
        print("DAST SCAN FAILED: Vulnerabilities or crashes detected.")
        return 1
    else:
        print("DAST SCAN PASSED: Zero uncaught 500 crashes detected.")
        return 0


if __name__ == "__main__":
    sys.exit(run_fuzz_scan())
