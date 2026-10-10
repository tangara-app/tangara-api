"""Tangara API example: quote and persist, submit, then poll. No dependencies."""
import json
import os
from pathlib import Path
import sys
import time
import urllib.error
import urllib.request
import uuid


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def api(method, path, body=None):
    key = os.environ["TANGARA_API_KEY"]
    base = os.environ.get("TANGARA_API_URL", "https://tangara.app/api/v1").rstrip("/")
    request = urllib.request.Request(
        base + path,
        data=None if body is None else json.dumps(body).encode(),
        headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"},
        method=method,
    )
    try:
        with urllib.request.build_opener(NoRedirect).open(request, timeout=30) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        raise RuntimeError(f"HTTP {error.code}: {error.read().decode()}") from None


def show(value):
    print(json.dumps(value, indent=2))


def main():
    command = sys.argv[1] if len(sys.argv) > 1 else ""
    if command == "models":
        return show(api("GET", "/models"))
    if len(sys.argv) != 3 or command not in ("prepare", "submit", "wait"):
        raise ValueError("Usage: video.py models | prepare FILE | submit FILE | wait TASK_UUID")
    argument = sys.argv[2]
    if command == "prepare":
        request = {
            "client_request_id": str(uuid.uuid4()),
            "prompt": os.environ.get("TANGARA_PROMPT", "A hummingbird hovers beside a flower in soft morning light."),
            "profile_id": os.environ.get("TANGARA_PROFILE_ID", "ltx-2.5-720p-v3"),
            "duration_seconds": int(os.environ.get("TANGARA_DURATION_SECONDS", "5")),
            "audio": True,
            "seed": 42,
        }
        for field in ("first_image_id", "last_image_id"):
            if os.environ.get("TANGARA_" + field.upper()):
                request[field] = os.environ["TANGARA_" + field.upper()]
        if request.get("last_image_id") and not request.get("first_image_id"):
            raise ValueError("An end frame requires a first frame")
        quote = api("POST", "/quote", {k: request[k] for k in ("profile_id", "duration_seconds")})
        request["expected_price"] = {k: quote[k] for k in ("version", "amount")}
        fd = os.open(argument, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as output:
            json.dump(request, output, indent=2)
            output.flush()
            os.fsync(output.fileno())
        show(quote)
        print(f"Saved {argument}. Review the quote, then use submit to queue paid generation.")
    elif command == "submit":
        request = json.loads(Path(argument).read_text())
        show(api("POST", "/tasks", request))
    else:
        task_id = str(uuid.UUID(argument))
        deadline = time.monotonic() + 3600
        while time.monotonic() < deadline:
            task = api("GET", "/tasks/" + task_id)
            print(task["result"], task.get("stage", ""), file=sys.stderr)
            if task["result"] == "succeeded":
                return show(api("GET", f"/tasks/{task_id}/result"))
            if task["result"] == "failed":
                raise RuntimeError(task.get("error_message") or "Generation failed")
            time.sleep(5)
        raise TimeoutError("Polling stopped after one hour. The task remains saved; run wait again.")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, RuntimeError) as error:
        sys.exit(str(error))
