"""Clinical scoring regression tests including exact boundary conditions."""
import csv
import json
import subprocess
import sys

import pytest
from heart_score import calculate_metrics, process_batch


def case(**changes):
    values = dict(
        history=0, ecg=0, age=44, risk_factors=0,
        troponin_ratio=0.5, prior_cad=False,
    )
    values.update(changes)
    return calculate_metrics(**values)


def test_zero_score_and_incomplete_pathway():
    outcome = case()
    assert outcome["score"] == 0
    assert outcome["hear_score"] == 0
    assert outcome["classification"] == "Low (0-3)"
    assert outcome["heart_pathway"] == "Not assessed"


@pytest.mark.parametrize("age,points", [(44, 0), (45, 1), (64, 1), (65, 2)])
def test_age_boundaries(age, points):
    assert case(age=age)["components"]["age"] == points


@pytest.mark.parametrize("risks,cad,points", [
    (0, False, 0), (1, False, 1), (2, False, 1),
    (3, False, 2), (0, True, 2),
])
def test_risk_factor_and_cad_scoring(risks, cad, points):
    assert case(risk_factors=risks, prior_cad=cad)["components"]["risk_factors"] == points


@pytest.mark.parametrize("ratio,points", [
    (0.0, 0), (1.0, 0), (1.001, 1), (2.999, 1), (3.0, 2),
])
def test_troponin_cutoffs(ratio, points):
    assert case(troponin_ratio=ratio)["components"]["troponin"] == points


def test_maximum_and_tiers():
    assert case(history=2, ecg=2, age=65, risk_factors=3, troponin_ratio=3)["score"] == 10
    assert case(history=2, ecg=1)["classification"] == "Low (0-3)"
    assert case(history=2, ecg=2)["classification"] == "Intermediate (4-6)"
    assert case(history=2, ecg=2, age=65, risk_factors=1)["classification"] == "High (7-10)"


def test_pathway_requires_confirmations():
    fields = dict(serial_troponins_negative=True, ischemic_ecg=False)
    assert case(**fields)["heart_pathway"] == "Low-risk criteria met"
    assert case(**fields, prior_cad=True)["heart_pathway"] == "Low-risk criteria not met"
    assert case(**fields, ischemic_ecg=True)["heart_pathway"] == "Low-risk criteria not met"
    assert case(**fields, ecg=2)["heart_pathway"] == "Low-risk criteria not met"
    assert case(**fields, serial_troponins_negative=False)["heart_pathway"] == "Low-risk criteria not met"
    assert case(**fields, troponin_ratio=1.1)["heart_pathway"] == "Low-risk criteria not met"
    assert case(**fields, history=2, ecg=2)["heart_pathway"] == "Low-risk criteria not met"
    assert case(serial_troponins_negative=True)["heart_pathway"] == "Not assessed"


@pytest.mark.parametrize("change", [
    {"history": 3}, {"ecg": -1}, {"age": -1}, {"age": 44.5},
    {"risk_factors": -2}, {"troponin_ratio": float("nan")},
    {"troponin_ratio": float("inf")}, {"troponin_ratio": -0.1},
    {"prior_cad": None}, {"prior_cad": "unknown"},
    {"serial_troponins_negative": "uncertain"},
])
def test_invalid_inputs_raise(change):
    with pytest.raises(ValueError):
        case(**change)


def test_missing_components_rejected():
    with pytest.raises(TypeError):
        calculate_metrics(v1=20, v2=5)


def test_process_batch(tmp_path):
    src, dst = tmp_path / "in.csv", tmp_path / "out.csv"
    src.write_text(
        "Patient_ID,history,ecg,age,risk_factors,troponin_ratio,prior_cad,serial_troponins_negative,ischemic_ecg\n"
        "PT-001,0,0,44,0,0.5,no,yes,no\n"
        "PT-002,2,2,65,3,3.0,yes,no,yes\n", encoding="utf-8"
    )
    process_batch(str(src), str(dst))
    with dst.open(newline="") as handle:
        records = list(csv.DictReader(handle))
    assert [int(record["score"]) for record in records] == [0, 10]
    assert records[0]["heart_pathway"] == "Low-risk criteria met"
    assert records[1]["heart_pathway"] == "Low-risk criteria not met"


def test_process_batch_rejects_incomplete_input(tmp_path):
    source = tmp_path / "in.csv"
    output = tmp_path / "out.csv"
    with pytest.raises(FileNotFoundError):
        process_batch(str(source), str(output))
    source.write_text("", encoding="utf-8")
    with pytest.raises(ValueError, match="no headers"):
        process_batch(str(source), str(output))
    source.write_text("history,ecg\n0,0\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Missing required"):
        process_batch(str(source), str(output))
    assert not output.exists()


def test_batch_prevents_partial_results_and_overwrite(tmp_path):
    source = tmp_path / "in.csv"
    output = tmp_path / "out.csv"
    source.write_text(
        "history,ecg,age,risk_factors,troponin_ratio,prior_cad\n"
        "0,0,50,1,0.1,no\n"
        "0,0,50,1,unexpected,no\n", encoding="utf-8"
    )
    with pytest.raises(ValueError, match="row 3"):
        process_batch(str(source), str(output))
    assert not output.exists()
    with pytest.raises(ValueError, match="must differ"):
        process_batch(str(source), str(source))


def test_cli_json_output():
    command = [sys.executable, "heart_score.py", "single", "--history", "0",
        "--ecg", "0", "--age", "44", "--risk-factors", "0",
        "--troponin-ratio", "0.5", "--prior-cad", "no",
        "--serial-negative", "yes", "--ischemic-ecg", "no"]
    res = subprocess.run(command, capture_output=True, text=True, check=True)
    assert json.loads(res.stdout)["heart_pathway"] == "Low-risk criteria met"


def test_audit_secret_key_secure_default(monkeypatch):
    monkeypatch.delenv("AUDIT_SECRET_KEY", raising=False)
    from agents.base import AuditTrail
    assert len(AuditTrail().secret_key) == 64
