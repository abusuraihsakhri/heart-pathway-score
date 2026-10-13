#!/usr/bin/env python3
"""HEART score and simplified HEART Pathway eligibility assessment.

The five HEART components contribute 0, 1 or 2 points each (total 0-10).
The Pathway assessment additionally requires explicitly documented serial
troponin results, ischemic-ECG status and previous CAD status. This is a
reference implementation, not a validated clinical decision support system.

References:
- https://pmc.ncbi.nlm.nih.gov/articles/PMC6005932/
- https://www.jacc.org/doi/10.1016/j.jacc.2018.12.046
"""
import argparse
import csv
import json
import math
import os
from typing import Any, Dict, Optional


def _number(name: str, value: Any) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{name} must be numeric, not Boolean")
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be a number") from exc
    if not math.isfinite(result):
        raise ValueError(f"{name} must be finite")
    return result


def _integer(name: str, value: Any, minimum: int, maximum: int) -> int:
    number = _number(name, value)
    if not number.is_integer() or not minimum <= number <= maximum:
        raise ValueError(f"{name} must be an integer from {minimum} to {maximum}")
    return int(number)


def _boolean(name: str, value: Any, optional: bool = False) -> Optional[bool]:
    if value is None or value == "":
        if optional:
            return None
        raise ValueError(f"{name} must be explicitly true or false")
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in ("true", "yes", "1"):
            return True
        if normalized in ("false", "no", "0"):
            return False
    raise ValueError(f"{name} must be true or false")


def calculate_metrics(
    *,
    history: Any,
    ecg: Any,
    age: Any,
    risk_factors: Any,
    troponin_ratio: Any,
    prior_cad: Any,
    serial_troponins_negative: Any = None,
    ischemic_ecg: Any = None,
) -> Dict[str, Any]:
    """Calculate the 0-10 HEART score and conditional HEART Pathway status.

    history / ecg: clinician-assigned integer categories (0, 1, 2).
    age: years; <45=0, 45-64=1, >=65=2.
    risk_factors: count; 0=0, 1-2=1, >=3 or prior CAD=2.
    troponin_ratio: first measured concentration / assay upper reference limit;
                    <=1=0, >1 and <3=1, >=3=2.
    prior_cad: explicit yes/no. A known CAD history disqualifies low-risk pathway.
    serial_troponins_negative / ischemic_ecg: explicit yes/no to assess
                    pathway status; omitted values yield 'Not assessed'.
    """
    h = _integer("history", history, 0, 2)
    e = _integer("ecg", ecg, 0, 2)
    a = _integer("age", age, 0, 120)
    risks = _integer("risk_factors", risk_factors, 0, 30)
    ratio = _number("troponin_ratio", troponin_ratio)
    if ratio < 0:
        raise ValueError("troponin_ratio must be non-negative")
    cad = _boolean("prior_cad", prior_cad)
    serial_negative = _boolean("serial_troponins_negative", serial_troponins_negative, optional=True)
    ischemic = _boolean("ischemic_ecg", ischemic_ecg, optional=True)

    age_points = 0 if a < 45 else (1 if a < 65 else 2)
    risk_points = 2 if cad or risks >= 3 else (1 if risks >= 1 else 0)
    troponin_points = 0 if ratio <= 1 else (1 if ratio < 3 else 2)
    hear_score = h + e + age_points + risk_points
    score = hear_score + troponin_points
    risk_tier = "Low (0-3)" if score <= 3 else ("Intermediate (4-6)" if score <= 6 else "High (7-10)")

    if serial_negative is None or ischemic is None:
        pathway = "Not assessed"
    elif hear_score <= 3 and e != 2 and ratio <= 1 and serial_negative and not ischemic and not cad:
        pathway = "Low-risk criteria met"
    else:
        pathway = "Low-risk criteria not met"

    return {
        "tool": "heart-pathway-score",
        "score": score,
        "hear_score": hear_score,
        "classification": risk_tier,
        "heart_pathway": pathway,
        "components": {
            "history": h, "ecg": e, "age": age_points,
            "risk_factors": risk_points, "troponin": troponin_points
        },
        "clinical_recommendation": (
            "Educational risk stratification only. Clinical assessment, serial "
            "troponin timing/assay protocols and applicable chest-pain guidelines "
            "govern management; this output is not a discharge authorization."
        ),
    }


def process_single(args: argparse.Namespace) -> None:
    result = calculate_metrics(
        history=args.history, ecg=args.ecg, age=args.age,
        risk_factors=args.risk_factors, troponin_ratio=args.troponin_ratio,
        prior_cad=args.prior_cad, serial_troponins_negative=args.serial_negative,
        ischemic_ecg=args.ischemic_ecg,
    )
    print(json.dumps(result, indent=2))


def process_batch(input_csv: str, output_csv: str) -> None:
    """Process a local CSV; refuse partial/malformed records rather than guess."""
    if not os.path.isfile(input_csv):
        raise FileNotFoundError(f"Input CSV not found: {input_csv}")
    if os.path.abspath(input_csv) == os.path.abspath(output_csv):
        raise ValueError("Input and output CSV paths must differ")
    with open(input_csv, newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle, strict=True)
        headers = list(reader.fieldnames or [])
        required = {"history", "ecg", "age", "risk_factors", "troponin_ratio", "prior_cad"}
        if not headers:
            raise ValueError("Input CSV has no headers")
        if len(set(headers)) != len(headers):
            raise ValueError("Duplicate input CSV columns")
        missing = required.difference(headers)
        if missing:
            raise ValueError("Missing required CSV columns: " + ", ".join(sorted(missing)))
        output_names = ("score", "hear_score", "classification", "heart_pathway")
        if any(name in headers for name in output_names):
            raise ValueError("Input CSV contains reserved output columns")
        results = []
        for line_no, row in enumerate(reader, 2):
            if None in row or any(value is None for value in row.values()):
                raise ValueError(f"CSV row {line_no} has an incorrect number of columns")
            try:
                result = calculate_metrics(**{key: row.get(key) for key in (
                    "history", "ecg", "age", "risk_factors", "troponin_ratio",
                    "prior_cad", "serial_troponins_negative", "ischemic_ecg"
                )})
            except ValueError as exc:
                raise ValueError(f"Invalid CSV row {line_no}: {exc}") from exc
            results.append({**row, **{key: result[key] for key in output_names}})
    with open(output_csv, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers + list(output_names))
        writer.writeheader()
        writer.writerows(results)
    print(f"Processed {len(results)} records -> {output_csv}")


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description="HEART score & conditional HEART Pathway assessment")
    commands = parser.add_subparsers(dest="command", required=True)
    single = commands.add_parser("single", help="Calculate one HEART score")
    single.add_argument("--history", type=int, required=True, choices=(0, 1, 2))
    single.add_argument("--ecg", type=int, required=True, choices=(0, 1, 2))
    single.add_argument("--age", type=int, required=True)
    single.add_argument("--risk-factors", type=int, required=True)
    single.add_argument("--troponin-ratio", type=float, required=True)
    single.add_argument("--prior-cad", choices=("yes", "no"), required=True)
    single.add_argument("--serial-negative", choices=("yes", "no"))
    single.add_argument("--ischemic-ecg", choices=("yes", "no"))
    batch = commands.add_parser("batch", help="Process locally stored CSV")
    batch.add_argument("-i", "--input", required=True)
    batch.add_argument("-o", "--output", default="results.csv")
    args = parser.parse_args(argv)
    try:
        if args.command == "single":
            process_single(args)
        else:
            process_batch(args.input, args.output)
    except (OSError, ValueError, csv.Error) as exc:
        parser.exit(2, f"Error: {exc}\n")


if __name__ == "__main__":
    main()
