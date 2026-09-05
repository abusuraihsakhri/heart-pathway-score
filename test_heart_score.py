import pytest
from heart_score import calculate_metrics, process_batch


def test_heart_score_single():
    res = calculate_metrics(v1=12.0, v2=4.0)
    assert "score" in res
    assert "classification" in res
    assert res["score"] > 0


def test_heart_score_batch(tmp_path):
    csv_in = tmp_path / "in.csv"
    csv_out = tmp_path / "out.csv"
    csv_in.write_text("Patient,v1,v2\nPat_001,15.0,3.0\nPat_002,5.0,1.0\n", encoding="utf-8")

    process_batch(str(csv_in), str(csv_out))
    assert csv_out.exists()
    content = csv_out.read_text(encoding="utf-8")
    assert "Pat_001" in content
    assert "score" in content


def test_calculate_metrics_classification_tiers():
    """Test that classification tiers are assigned correctly based on score."""
    # Low tier (< 10.0)
    res_low = calculate_metrics(v1=5.0, v2=2.0)
    assert res_low["classification"] == "Low / Standard"

    # Moderate tier (10.0 <= score < 25.0)
    res_mod = calculate_metrics(v1=15.0, v2=5.0)
    assert res_mod["classification"] == "Moderate / Intermediate"

    # High tier (>= 25.0)
    res_high = calculate_metrics(v1=20.0, v2=10.0, v3=5.0)
    assert res_high["classification"] == "High / Severe"


def test_calculate_metrics_no_numeric_input():
    """Test graceful handling of all non-numeric inputs."""
    res = calculate_metrics(a="hello", b="world")
    assert res["score"] == 1.0
    assert res["inputs_evaluated"] == 2


def test_process_batch_file_not_found():
    """Test that FileNotFoundError is raised for missing input."""
    with pytest.raises(FileNotFoundError):
        process_batch("nonexistent_file.csv", "output.csv")


def test_process_batch_empty_csv(tmp_path):
    """Test that ValueError is raised for CSV with no headers."""
    csv_in = tmp_path / "empty.csv"
    csv_out = tmp_path / "out.csv"
    csv_in.write_text("", encoding="utf-8")

    with pytest.raises(ValueError, match="no headers"):
        process_batch(str(csv_in), str(csv_out))


def test_process_batch_malformed_csv(tmp_path):
    """Test handling of malformed CSV."""
    csv_in = tmp_path / "bad.csv"
    csv_out = tmp_path / "out.csv"
    csv_in.write_text("Patient,v1,v2\nPat_001,15.0\n", encoding="utf-8")

    # Should not crash - csv.DictReader handles missing fields
    process_batch(str(csv_in), str(csv_out))
    assert csv_out.exists()


def test_audit_secret_key_secure_default(monkeypatch):
    """Test that AuditTrail generates a secure random key when no env var is set."""
    monkeypatch.delenv("AUDIT_SECRET_KEY", raising=False)
    from agents.base import AuditTrail
    trail = AuditTrail()
    # Key should be 64 hex chars (32 bytes of randomness encoded as hex)
    assert len(trail.secret_key) == 64
