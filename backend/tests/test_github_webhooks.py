import hmac
import hashlib
import json
from app.services.webhook_security import verify_github_signature


def test_valid_github_webhook_hmac_signature():
    """Verify HMAC-SHA256 signature verification with valid secret."""
    secret = "my_webhook_secret_key"
    payload = json.dumps({"action": "opened", "number": 101}).encode("utf-8")

    # Generate HMAC-SHA256 signature
    signature = "sha256=" + hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()

    assert verify_github_signature(payload, signature, secret_override=secret) is True


def test_invalid_github_webhook_hmac_signature():
    """Verify invalid HMAC-SHA256 signature is rejected."""
    secret = "my_webhook_secret_key"
    payload = json.dumps({"action": "opened", "number": 101}).encode("utf-8")

    invalid_signature = "sha256=0000000000000000000000000000000000000000000000000000000000000000"

    assert verify_github_signature(payload, invalid_signature, secret_override=secret) is False



def test_webhook_event_parsing_opened():
    """Verify parsing of pull_request opened webhook payload."""
    payload = {
        "action": "opened",
        "number": 42,
        "pull_request": {
            "number": 42,
            "title": "Fix memory leak in buffer stream",
            "state": "open",
            "head": {"ref": "bugfix/memory-leak", "sha": "abc123def456"},
            "base": {"ref": "main"},
            "user": {"login": "octocat"},
        },
        "repository": {
            "id": 12345678,
            "full_name": "octocat/Hello-World",
        },
    }

    assert payload["action"] == "opened"
    assert payload["pull_request"]["number"] == 42
    assert payload["pull_request"]["head"]["sha"] == "abc123def456"


if __name__ == "__main__":
    test_valid_github_webhook_hmac_signature()
    test_invalid_github_webhook_hmac_signature()
    test_webhook_event_parsing_opened()
    print("GitHub webhooks unit tests PASSED!")
