# TB Drug Resistance Interpreter

Clinical tool for interpreting Mycobacterium tuberculosis drug resistance patterns and recommending WHO treatment regimens based on molecular and phenotypic susceptibility data.

## Features

- **First-line Drug Resistance**: INH, RIF, PZA, EMB, Streptomycin
- **Resistance Category Classification**:
  - INH mono-resistant
  - RIF mono-resistant (treat as MDR-TB pending full DST)
  - MDR-TB: Resistant to INH + RIF
  - Pre-XDR-TB: MDR + fluoroquinolone resistant
  - XDR-TB: Pre-XDR + bedaquiline or linezolid resistant (2021 WHO definition)
- **Key Resistance Mutation Interpretation**:
  - INH: katG S315T (high-level), inhA promoter (low-level)
  - RIF: rpoB S531L, H526Y, D516V
  - PZA: pncA mutations
  - EMB: embB M306 mutations
  - FQ: gyrA D94G, A90V
- **WHO Treatment Regimen Recommendations** per 2022 guidelines
- **Monitoring Recommendations** for each regimen

## Quick Start

```bash
# Classify resistance pattern
python cli.py classify --susceptibility '{"isoniazid":"R","rifampicin":"R","moxifloxacin":"R"}'

# Get WHO regimen recommendation
python cli.py regimen --category MDR_TB

# Analyze with mutations
python cli.py classify --susceptibility '{"isoniazid":"R","rifampicin":"R"}' \
  --mutations '{"katG":["S315T"],"rpoB":["S531L"]}'
```

## Python API

```python
from tb_resistance import analyze_tb_resistance

result = analyze_tb_resistance(
    susceptibility={"isoniazid": "R", "rifampicin": "R", "moxifloxacin": "R"},
    mutations={"katG": ["S315T"], "rpoB": ["S531L"], "gyrA": ["D94G"]},
)
print(result["classification"]["resistance_category"])  # "PRE_XDR_TB"
```

## Testing

```bash
python -m pytest test_tb_resistance.py -v
```

## Standards

- WHO Consolidated Guidelines on Tuberculosis (2022)
- WHO Operational Handbook on Tuberculosis: Module 4 (Drug-Resistant TB Treatment)
- Nahid et al. (2016) Clin Infect Dis 63(7):e147-e195

## License

MIT
