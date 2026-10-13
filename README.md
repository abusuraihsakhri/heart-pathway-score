# HEART Score & HEART Pathway

A small, dependency-free reference calculator for the five-component HEART chest-pain score and conditional HEART Pathway low-risk criteria. Available as a browser-only calculator and Python CLI/CSV module.

**Clinical limitation:** This is a research/educational reference, not a clinically validated medical device or discharge decision system. Suspected STEMI, unstable patients and other time-critical presentations require clinical evaluation irrespective of the displayed score. Use locally adopted chest-pain algorithms, clinician ECG interpretation and assay-specific serial troponin protocols.

## Browser calculator

The static interface is in `web/`. To run locally:

```sh
python -m http.server 8080 --directory web
```

Open `http://localhost:8080/`. It runs on ordinary browsers with JavaScript modules (recent Chrome, Firefox, Safari and Edge), including mobile browsers. No Python interpreter, API service, cookies, storage or external runtime dependencies are required. The static app performs calculations locally and makes no network requests with input data.

## Scoring

Each HEART component contributes 0–2 points.

| Component | 0 points | 1 point | 2 points |
| --- | --- | --- | --- |
| History | Slight/nonspecific | Moderately suspicious | Highly suspicious |
| ECG | Normal | Nonspecific abnormality | Significant ST deviation |
| Age (years) | <45 | 45–64 | ≥65 |
| Risk factors | 0 | 1–2 | ≥3 or established coronary artery disease |
| Initial troponin / assay URL | ≤1 | >1 and <3 | ≥3 |

HEART total is 0–10: **low** 0–3, **intermediate** 4–6, **high** 7–10. For this reference implementation, Pathway low-risk criteria additionally require **HEAR ≤3**, **no ischemic ECG findings**, **no prior CAD**, **negative serial troponins according to the local protocol**, and **an initial troponin at or below its assay upper reference limit**. If serial results or ischemic ECG status are not provided, the Pathway returns **Not assessed**. A positive criterion does not authorize discharge.

The clinical HEART and HEART Pathway variants differ between studies and local protocols, especially regarding troponin assay/timing. Verify applicability before use.

References:
- <https://pmc.ncbi.nlm.nih.gov/articles/PMC6005932/>
- <https://www.jacc.org/doi/10.1016/j.jacc.2018.12.046>
- <https://pmc.ncbi.nlm.nih.gov/articles/PMC7908281/>

## Python CLI and CSV

The core `heart_score.py` requires only the Python standard library. CLI examples use **synthetic** observations without identifiable patient data:

```sh
python heart_score.py single --history 0 --ecg 0 --age 44 --risk-factors 0 --troponin-ratio 0.5 --prior-cad no --serial-negative yes --ischemic-ecg no
python heart_score.py batch -i sample.csv -o results.csv
```

Required CSV columns are `history,ecg,age,risk_factors,troponin_ratio,prior_cad`. Optional columns are `serial_troponins_negative,ischemic_ecg`. Boolean values accept `yes/no` or `true/false`. The output appends `score,hear_score,classification,heart_pathway` and keeps existing input columns. Incomplete or invalid rows fail explicitly; the input file is never overwritten.

The former generic `--v1/--v2/--v3` weighted-sum interface was removed because it did not implement HEART scoring and could misclassify clinical cases.

## Optional legacy audit framework

`agents/`, `cli.py`, `simulator.py`, `enrichment.py` and the FastAPI endpoints are retained for backward compatibility and technical demonstrations. **These are generic audit/simulation functions, not clinical HEART decision algorithms**, and their configurable thresholds do not represent established clinical standards. The mock chat provider does not perform language-model or clinical inference.

To run these modules:

```sh
python -m pip install -r requirements.txt
python -m pytest -q
node --test web/score.test.mjs
python cli.py audit --task-id TEST-01 --target TEST-TARGET --primary 12 --secondary 4
python cli.py serve --host 127.0.0.1 --port 8000
```

The API uses volatile in-memory audit records and an HMAC signing key. A random key is generated at startup unless `AUDIT_SECRET_KEY` is set. The pattern-based identifier guard is **not comprehensive PHI deidentification**. Do not submit personal health information to the legacy API, mock chat or sample scripts. The API is not authenticated or designed for open Internet exposure.

## Docker

Build the optional API with `docker build -t heart-pathway-score .`; run it with `docker compose up --build` (Compose binds to loopback by default). Docker is not required for the web calculator.

## Development and testing

Python 3.10+ and Node.js 22+ (only for JavaScript tests) are supported targets. GitHub Actions tests Python calculation, existing agent modules, and JavaScript component boundaries. Browser calculation uses plain ECMAScript modules without npm dependencies.

## Privacy and license

Browser calculations stay in the local tab; no automatic storage, submission or telemetry. Local CSVs are processed on the user's machine. The optional local API may keep non-identifying audit metadata in process memory; it should not be used with sensitive clinical data. See [LICENSE](LICENSE) for MIT license terms.
