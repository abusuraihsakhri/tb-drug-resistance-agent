# TB Drug Resistance Interpreter

A deterministic Python research utility for classifying *Mycobacterium tuberculosis* drug-susceptibility results. It distinguishes rifampicin resistance, MDR-TB, pre-XDR-TB and XDR-TB using the WHO 2021 resistance definitions.

**Research and educational use only. This software is not a validated clinical decision-support system.** Do not use its output to diagnose a patient, determine treatment, prescribe medication or calculate doses.

## Browser application

The `web/index.html` interface uses **Pyodide** to execute the same `tb_resistance.py` classifier entirely in the browser. The GitHub Actions workflow `.github/workflows/pages.yml` assembles the page and Python module for GitHub Pages. The live URL should be added only after a successful deployment and end-to-end verification.

The web interface accepts S (susceptible), R (resistant), and U (unknown / not tested), presents the classification and DST completeness, and exports JSON. **Patient identifiers must not be entered.** No result data is sent to an application backend, but Pyodide runtime files are fetched from the pinned jsDelivr CDN. An internet connection is required for initial loading.

## Python interpreter

- `tb_resistance.py`: stdlib-only DST classification, limited mutation annotation, CSV input and JSON output.
- Missing DST is **unknown**, not susceptible. The interpreter distinguishes first-line susceptibility that is incomplete from fully documented susceptible results.
- Pre-XDR and XDR classification covers the WHO **MDR/RR-TB** population, including rifampicin-resistant cases without isoniazid resistance.
- Mutation annotations are illustrative, not a validated catalogue-based interpretation. The hard-coded mutation frequencies and historical MIC fields are not suitable for diagnosis.
- `get_who_regimen()` is retained **only for backward compatibility**. It contains **outdated historical example regimens and doses** that do **not** implement WHO's 2026 Module 4 guideline. Every response carries a safety notice. Do not use it for treatment selection or dosing.

### Install and run

Python 3.10 or newer:

```bash
python -m pip install -e ".[api,test]"
python -m pytest -q

python -m tb_resistance classify --susceptibility '{"isoniazid":"R","rifampicin":"R","moxifloxacin":"R"}'
python -m tb_resistance csv --input your-dst.csv --output classifications.json
```

For CSV, use columns such as `isoniazid,rifampicin,pyrazinamide,ethambutol,streptomycin,moxifloxacin,bedaquiline,linezolid` with values `S`, `R` or `U`. Unrecognized result values are rejected rather than silently treated as susceptible.

## Additional experimental components

The repository also includes two **separate, generic threshold-based demonstration systems**: `agents/` (Pydantic/FastAPI supervisor) and `tb_drug_resistance_agent/` (dataclass coordinator/CLI). Their arbitrary numerical thresholds and status flags **do not determine TB resistance or implement the cited clinical guidelines**. The similarly named `enrichment.py` modules are parameterized threshold demonstrations, not implemented TB treatment, dosing, interaction or surveillance algorithms.

To run the separate numerical demonstration CLI:

```bash
python -m tb_drug_resistance_agent.cli audit --case-id DEMO-001 --primary 26 --secondary 13
python -m tb_drug_resistance_agent.cli verify-audit
python -m tb_drug_resistance_agent.cli serve --host 127.0.0.1 --port 8000
```

The example API exposes `/health`, `/api/audit`, and `/api/chat`. It has no authentication or production hardening: **bind to localhost, not the public Internet**. The container port is intended for development only. The demonstration audit chain is in-memory, not durable across restarts. HMAC signatures detect changes to retained log entries but do not prove an absence of records, compliance certification, or protection against every form of PHI.

## Security and configuration

- Keep test and research input de-identified. Simple regular-expression identifier checks are **not** comprehensive PHI de-identification.
- In Docker Compose, provide a strong `AUDIT_SECRET_KEY` through the environment (see `.env.example`); do not commit the value. Without it, an ephemeral key is generated, and audit verification only applies within that process lifetime.
- The generic LLM provider factory currently returns a deterministic mock, regardless of selected provider. No live hosted or local LLM integration is implemented.
- The browser application executes locally; only static assets and the CDN runtime are fetched. It does not persist user input.
- GitHub Actions runs Python installation, compilation, tests and CLI smoke checks.

## Authoritative clinical references

- WHO (2021): [Updated pre-XDR-TB and XDR-TB definitions](https://www.who.int/news/item/27-01-2021-who-announces-updated-definitions-of-extensively-drug-resistant-tuberculosis).
- WHO (2026): [Consolidated guidelines on TB, Module 4: Treatment and care, second edition](https://www.who.int/publications/i/item/9789240125124).

**License:** MIT (see `LICENSE`). **Browser compatibility:** current browsers supporting WebAssembly and ES2020+; Pyodide CDN access is necessary.
