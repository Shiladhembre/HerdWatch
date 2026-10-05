"""Read-only/live authentication-boundary smoke checks. Never creates user data."""
import csv
import io
from pathlib import Path
from uuid import uuid4

import httpx
from PIL import Image


def main():
    rows = []
    with httpx.Client(base_url="http://127.0.0.1:8000", timeout=20) as client:
        spec = client.get("/openapi.json").json()
        for path, expected in [("/", 404), ("/docs", 200), ("/openapi.json", 200), ("/health", 200)]:
            response = client.get(path)
            rows.append(["GET", path, expected, response.status_code,
                         "PASS" if response.status_code == expected else "FAIL", "live readiness/public route"])
            if path == "/health":
                print("Health:", response.json())
        for path, operations in spec["paths"].items():
            for method, operation in operations.items():
                if method not in {"get", "post", "patch", "delete"}:
                    continue
                if not operation.get("security"):
                    continue
                actual_path = path
                for parameter in operation.get("parameters", []):
                    if parameter["in"] == "path":
                        actual_path = actual_path.replace("{" + parameter["name"] + "}", str(uuid4()))
                response = client.request(method, actual_path)
                rows.append([method.upper(), path, 401, response.status_code,
                             "PASS" if response.status_code == 401 else "FAIL", "missing-token boundary only; CRUD unverified"])
        for origin, expected in [("http://localhost:5173", 200), ("https://untrusted.example", 400)]:
            response = client.options("/api/v1/predict/image", headers={
                "Origin": origin, "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "authorization,content-type"})
            ok = response.status_code == expected and (
                response.headers.get("access-control-allow-origin") == origin if expected == 200
                else "access-control-allow-origin" not in response.headers)
            rows.append(["OPTIONS", "/api/v1/predict/image", expected, response.status_code,
                         "PASS" if ok else "FAIL", origin])
        buffer = io.BytesIO()
        Image.new("RGB", (224, 224), (128, 64, 32)).save(buffer, "JPEG")
        for path, kwargs in [
            ("/api/v1/predict/disease", {"json": {"symptoms": {f"G{i:02}": 0 for i in range(1, 19)}}}),
            ("/api/v1/predict/image", {"files": {"file": ("qa-synthetic.jpg", buffer.getvalue(), "image/jpeg")}}),
        ]:
            response = client.post(path, **kwargs)
            rows.append(["POST", path, 401, response.status_code,
                         "PASS" if response.status_code == 401 else "FAIL", "valid payload; no session; inference blocked"])
        print("OpenAPI operations:", sum(method in {"get", "post", "patch", "delete"}
              for operations in spec["paths"].values() for method in operations))
    destination = Path(__file__).resolve().parents[2] / "QA_ENDPOINT_RESULTS.csv"
    with destination.open("w", newline="", encoding="utf-8") as output:
        writer = csv.writer(output)
        writer.writerow(["Method", "Route", "Expected status", "Actual status", "Result", "Scope"])
        writer.writerows(rows)
    print("HTTP checks:", len(rows), "passed:", sum(row[4] == "PASS" for row in rows),
          "failed:", sum(row[4] == "FAIL" for row in rows))
    print("Saved:", destination.name)


if __name__ == "__main__":
    main()
