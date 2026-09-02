# Tb Drug Resistance Agent

> **Domain:** Infectious Disease Surveillance & Microbiology  
> **Reference Guidelines & Standards:** `CLSI M100, EUCAST & CDC NHSN Clinical Standards`

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

**Tb Drug Resistance Agent** is an advanced analytical and computational platform implementing Molecular & Phenotypic MDR/XDR-TB Regimen Advisor.

---

## ⚙️ Key Capabilities & Algorithmic Modules

### 🔬 Analytical Functions

- **`classify_tb_resistance()`**: Classify TB drug resistance pattern.

Args:
    susceptibility: Dict mapping drug name to 'S' or 'R'
    mutations: Optional dict mapping gene to list of detected mutations

Returns:
    Dict with resistance category, details, and clinical implications
- **`get_who_regimen()`**: Get WHO treatment regimen recommendation based on resistance pattern.

Based on WHO consolidated guidelines on TB (2022 update).

Args:
    resistance_category: One of SUSCEPTIBLE, MONO_RESISTANT, INH_MONO_RESISTANT,
                        RIF_MONO_RESISTANT, MDR_TB, PRE_XDR_TB, XDR_TB
    additional_resistance: Dict of additional drug resistance flags

Returns:
    Dict with regimen recommendation, duration, and monitoring
- **`analyze_tb_resistance()`**: Complete TB drug resistance analysis.

Args:
    susceptibility: Dict mapping drug name to 'S' or 'R'
    mutations: Optional dict mapping gene to list of detected mutations

Returns:
    Comprehensive analysis with classification, regimen, and monitoring
- **`load_from_csv()`**: Load TB susceptibility data from CSV and analyze each record.
- **`build_parser()`**: Build the argument parser.

---

## 💻 CLI Quickstart & Usage

### 1. Guided Interactive Mode
```bash
python cli.py
```

### 2. Direct Parameterized Evaluation
```bash
python cli.py --input data.csv
```

### Parameter Reference
- `--interactive`: Launch guided terminal interactive wizard.
- `--input <path>`: Evaluate input from JSON or CSV specification.
- `--json`: Output deterministic structured results in JSON format.

### Input Data Schema

| Field | Description | Requirement |
|:------|:------------|:------------|
| `case_id` | Parameter / observation metric | Required |
| `patient_synthetic_id` | Parameter / observation metric | Required |
| `metric_primary` | Parameter / observation metric | Required |
| `metric_secondary` | Parameter / observation metric | Required |
| `is_stat` | Parameter / observation metric | Required |
| `status_flag` | Parameter / observation metric | Required |

---

## 🛡️ Security & Enterprise Architecture

* **Zero-PHI Outbound Interceptor:** Active AST and regex inspection blocking SSNs, MRNs, phone numbers, and patient identifiers.
* **Tamper-Evident HMAC-SHA256 Audit Trail:** Chained, cryptographically signed logs for every evaluation and state transition.
* **Air-Gapped LLM Reasoning Adapter:** Agnostic integration for local Ollama instances (`llama3`, `mistral`), Claude 3.5 Sonnet, GPT-4o, and deterministic test mocks.
* **Active Learning Bayesian Calibration:** Dynamic tracker updating worker reliability weights and monitoring Brier calibration drift.
* **FastAPI & Prometheus Telemetry:** Exposes OpenAPI 3.1 REST endpoints and operational Prometheus metrics (`/metrics`).

---

## 🧪 Testing & Verification

Run the automated test suite:

```bash
pytest -v
```

Execute high-throughput batch simulation benchmarks:

```bash
python simulator.py --tasks 1000 --concurrency 8
```

---

## 🐳 Container Deployment

```bash
docker build -t tb-drug-resistance-agent .
docker run -p 8000:8000 tb-drug-resistance-agent
```
