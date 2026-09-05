# Heart Pathway Score

> **Domain:** Clinical Decision Support & Biomedical Computing
> **Reference Guidelines & Standards:** `Standard Clinical Formulations & ISO/IEC Quality Frameworks`

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)
![Audit Trail](https://img.shields.io/badge/Audit-HMAC--SHA256_Tamper--Evident-brightgreen.svg)
![Zero-PHI Guard](https://img.shields.io/badge/Guard-Zero--PHI_Outbound-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)

</div>

---

## 📖 What It Does

HEART Score & HEART Pathway for Chest Pain
Stratifies emergency department chest pain patients for safe early discharge vs admission.

The project provides:
- **Core algorithm** (`heart_score.py`): Zero-dependency Python implementation for single and batch evaluation
- **Enterprise agent framework** (`agents/`): Multi-worker evaluation with PHI protection and cryptographic audit trails
- **FastAPI REST API** (`agents/api.py`): REST endpoints for task processing and audit log retrieval
- **CLI** (`cli.py`): Command-line interface for single/batch processing and interactive chat

Author: Dr. Abu Suraih Sakhri
License: MIT

---

## 🚀 Installation

### Prerequisites
- Python 3.10, 3.11, or 3.12
- pip

### Install Dependencies
```bash
pip install -r requirements.txt
```

---

## ⚙️ Core Capability & Algorithmic Modules

### `heart_score.py` - Core Algorithm
- **`calculate_metrics(**kwargs)`**: Evaluates numeric inputs and returns a weighted score with clinical classification
- **`process_single(args)`**: Processes a single evaluation from command-line arguments
- **`process_batch(input_csv, output_csv)`**: Batch processes CSV records and appends score/classification columns

### `agents/` - Enterprise Framework
- **Supervisor Orchestrator**: Coordinates multi-worker evaluation with consensus dossier generation
- **Specialized Workers**: InvariantQC, SafetyEscalation, ProtocolConformance workers for domain-specific analysis
- **PHI Guard**: Zero-PHI outbound interceptor with regex-based pattern detection (MRN, SSN, phone, email)
- **Audit Trail**: HMAC-SHA256 tamper-evident chained audit log for all operations
- **FastAPI Server**: REST API with `/health`, `/metrics`, `/api/audit`, `/api/chat`, `/api/audit/logs` endpoints

---

## 📐 Algorithm

The core scoring algorithm computes a weighted sum of input parameters:

```python
score = primary_val + Σ(val * (1/idx) for idx, val in enumerate(other_vals, start=2))
rounded_score = round(score, 2)
```

Classification tiers:
- **Low / Standard**: score < 10.0
- **Moderate / Intermediate**: 10.0 ≤ score < 25.0
- **High / Severe**: score ≥ 25.0

---

## 💻 Usage

### Core Module (heart_score.py)

#### Single Evaluation
```bash
python heart_score.py single --v1 14.5 --v2 4.2 --v3 1.8
```

#### Batch CSV Processing
```bash
python heart_score.py batch -i sample.csv -o results.csv
```

### Enterprise CLI (cli.py)

#### Single Audit Evaluation
```bash
python cli.py audit --task-id TASK-01 --target SPECIMEN-01 --primary 28.5 --secondary 14.2
```

#### Batch Processing
```bash
python cli.py batch -i sample.csv -o results.csv
```

#### Supervisory Chat
```bash
python cli.py chat "Explain the HEART pathway criteria"
```

#### Verify Audit Integrity
```bash
python cli.py verify-audit
```

#### Launch REST API Server
```bash
python cli.py serve --host 127.0.0.1 --port 8000
```

### Input Data Schema

| Field | Description | Requirement |
|:------|:------------|:------------|
| `Patient_ID` | Unique patient or specimen identifier | Required |
| `v1` | Primary measurement parameter | Required |
| `v2` | Secondary measurement parameter | Required |
| `v3` | Tertiary measurement parameter | Optional |

---

## 🛡️ Security Architecture

* **Zero-PHI Outbound Interceptor:** Active regex inspection blocking SSNs, MRNs, phone numbers, emails, and patient identifiers
* **Tamper-Evident HMAC-SHA256 Audit Trail:** Chained, cryptographically signed logs for every evaluation
* **Secure Key Generation:** Audit keys are generated using `secrets.token_hex(32)` when not provided via `AUDIT_SECRET_KEY` environment variable
* **Input Validation:** CSV processing validates file existence, headers, and handles malformed data gracefully

---

## 🧪 Testing

Run the full test suite:

```bash
pytest -v
```

Execute high-throughput batch simulation:

```bash
python simulator.py --tasks 100
```

---

## 🐳 Container Deployment

### Docker Build & Run
```bash
docker build -t heart-pathway-score .
docker run -p 8000:8000 heart-pathway-score
```

### Docker Compose
```bash
# Copy and configure environment
cp .env.example .env
# Edit .env to set AUDIT_SECRET_KEY (generate with: python -c "import secrets; print(secrets.token_hex(32))")
docker compose up -d
```

---

## 📁 Project Structure

```
heart-pathway-score/
├── heart_score.py          # Core scoring algorithm
├── cli.py                  # Enterprise CLI
├── simulator.py            # High-throughput simulation
├── enrichment.py           # Enrichment feature engines
├── requirements.txt        # Python dependencies
├── Dockerfile              # Container build
├── docker-compose.yml      # Compose configuration
├── .env.example            # Environment variable template
├── sample.csv              # Sample input data
├── agents/                 # Enterprise agent framework
│   ├── __init__.py
│   ├── api.py             # FastAPI server
│   ├── base.py            # Security, PHI Guard, Audit Trail
│   ├── models.py          # Pydantic schemas
│   ├── supervisor.py      # Supervisor orchestrator
│   ├── workers.py         # Specialized worker agents
│   ├── llm_factory.py     # LLM client factory
│   ├── learning.py        # Bayesian calibration engine
│   ├── metrics.py         # Prometheus metrics
│   └── streamer.py        # WebSocket telemetry
├── tests/                  # Test suite
│   ├── test_heart_pathway_score.py
│   └── test_enrichment.py
├── web/                    # Operations console
│   └── index.html
└── .github/workflows/      # CI/CD
    └── ci.yml
```
