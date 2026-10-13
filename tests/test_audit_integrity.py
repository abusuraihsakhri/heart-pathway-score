"""HMAC audit integrity regression tests."""
from agents.base import AuditTrail


def test_hmac_ledger_detects_signature_tampering():
    audit = AuditTrail(secret_key="testing-only")
    audit.log("supervisor", "staff", "evaluation", {"status": "ok"})
    audit.log("supervisor", "staff", "evaluation", {"status": "ok"})
    assert audit.verify_integrity()
    audit.logs[0]["payload_hash"] = "f" * 64
    assert not audit.verify_integrity()


def test_log_accessor_is_copy():
    audit = AuditTrail(secret_key="testing-only")
    audit.log("supervisor", "staff", "evaluation", {"status": "ok"})
    audit.get_trail()[0]["actor"] = "attacker"
    assert audit.verify_integrity()
    assert audit.get_trail()[0]["actor"] == "supervisor"
