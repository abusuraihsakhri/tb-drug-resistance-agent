"""Tests for TB Drug Resistance Interpreter."""
import json
import pytest
from tb_resistance import (
    classify_tb_resistance,
    get_who_regimen,
    analyze_tb_resistance,
    _analyze_mutations,
    FIRST_LINE_DRUGS,
    SECOND_LINE_DRUGS,
    main,
)


# ─── Classification Tests ────────────────────────────────────────────────────

def test_classify_fully_susceptible():
    susc = {"isoniazid": "S", "rifampicin": "S", "pyrazinamide": "S",
            "ethambutol": "S", "streptomycin": "S"}
    result = classify_tb_resistance(susc)
    assert result["resistance_category"] == "SUSCEPTIBLE"
    assert result["clinical_significance"] == "LOW"


def test_classify_inh_mono_resistant():
    susc = {"isoniazid": "R", "rifampicin": "S", "pyrazinamide": "S",
            "ethambutol": "S", "streptomycin": "S"}
    result = classify_tb_resistance(susc)
    assert result["resistance_category"] == "INH_MONO_RESISTANT"
    assert result["clinical_significance"] == "MODERATE"


def test_classify_rif_mono_resistant():
    susc = {"isoniazid": "S", "rifampicin": "R", "pyrazinamide": "S",
            "ethambutol": "S", "streptomycin": "S"}
    result = classify_tb_resistance(susc)
    assert result["resistance_category"] == "RIF_MONO_RESISTANT"
    assert result["clinical_significance"] == "HIGH"


def test_classify_mdr_tb():
    susc = {"isoniazid": "R", "rifampicin": "R", "pyrazinamide": "S",
            "ethambutol": "S", "streptomycin": "S"}
    result = classify_tb_resistance(susc)
    assert result["resistance_category"] == "MDR_TB"
    assert result["clinical_significance"] == "HIGH"


def test_classify_pre_xdr_tb():
    susc = {"isoniazid": "R", "rifampicin": "R", "pyrazinamide": "S",
            "ethambutol": "S", "streptomycin": "S", "moxifloxacin": "R"}
    result = classify_tb_resistance(susc)
    assert result["resistance_category"] == "PRE_XDR_TB"
    assert result["clinical_significance"] == "VERY_HIGH"


def test_classify_xdr_tb():
    susc = {"isoniazid": "R", "rifampicin": "R", "pyrazinamide": "S",
            "ethambutol": "S", "streptomycin": "S", "moxifloxacin": "R",
            "bedaquiline": "R"}
    result = classify_tb_resistance(susc)
    assert result["resistance_category"] == "XDR_TB"
    assert result["clinical_significance"] == "CRITICAL"


def test_classify_xdr_tb_linezolid():
    """XDR via linezolid resistance."""
    susc = {"isoniazid": "R", "rifampicin": "R", "moxifloxacin": "R",
            "linezolid": "R"}
    result = classify_tb_resistance(susc)
    assert result["resistance_category"] == "XDR_TB"


def test_classify_mono_resistant_pza():
    susc = {"isoniazid": "S", "rifampicin": "S", "pyrazinamide": "R",
            "ethambutol": "S", "streptomycin": "S"}
    result = classify_tb_resistance(susc)
    assert result["resistance_category"] == "MONO_RESISTANT"


def test_resistant_drug_count():
    susc = {"isoniazid": "R", "rifampicin": "R", "pyrazinamide": "R",
            "ethambutol": "S", "streptomycin": "S"}
    result = classify_tb_resistance(susc)
    assert result["resistant_drug_count"] == 3


# ─── Mutation Analysis Tests ─────────────────────────────────────────────────

def test_mutation_katg_s315t():
    mutations = {"katG": ["S315T"]}
    result = _analyze_mutations(mutations, {"isoniazid": "R"})
    assert len(result["detected_mutations"]) > 0
    assert any(m["drug"] == "isoniazid" for m in result["detected_mutations"])


def test_mutation_rpoB_s531l():
    mutations = {"rpoB": ["S531L"]}
    result = _analyze_mutations(mutations, {"rifampicin": "R"})
    assert len(result["detected_mutations"]) > 0


def test_mutation_gyrA():
    mutations = {"gyrA": ["D94G"]}
    result = _analyze_mutations(mutations, {"moxifloxacin": "R"})
    assert len(result["detected_mutations"]) > 0


def test_mutation_embB_m306i():
    mutations = {"embB": ["M306I"]}
    result = _analyze_mutations(mutations, {"ethambutol": "R"})
    assert len(result["detected_mutations"]) > 0


def test_mutation_with_classification():
    susc = {"isoniazid": "R", "rifampicin": "R"}
    mutations = {"katG": ["S315T"], "rpoB": ["S531L"]}
    result = classify_tb_resistance(susc, mutations)
    assert result["resistance_category"] == "MDR_TB"
    assert len(result["mutation_analysis"]["detected_mutations"]) > 0


# ─── WHO Regimen Tests ───────────────────────────────────────────────────────

def test_regimen_susceptible():
    regimen = get_who_regimen("SUSCEPTIBLE")
    assert "2HRZE" in regimen["regimen_name"]
    assert regimen["total_duration"] == "6 months"


def test_regimen_mdr_tb():
    regimen = get_who_regimen("MDR_TB")
    assert "BPaL" in regimen["regimen_name"]
    assert regimen["total_duration"] == "6-9 months"


def test_regimen_xdr_tb():
    regimen = get_who_regimen("XDR_TB")
    assert "individualized" in regimen["regimen_name"].lower()
    assert regimen["clinical_significance"] if "clinical_significance" in regimen else True


def test_regimen_pre_xdr():
    regimen = get_who_regimen("PRE_XDR_TB")
    assert "BPaL" in regimen["regimen_name"]


def test_regimen_inh_mono():
    regimen = get_who_regimen("INH_MONO_RESISTANT")
    assert regimen["total_duration"] == "6 months"


def test_regimen_has_monitoring():
    for cat in ["SUSCEPTIBLE", "MDR_TB", "XDR_TB"]:
        regimen = get_who_regimen(cat)
        assert "monitoring" in regimen
        assert len(regimen["monitoring"]) > 0


# ─── Full Analysis Tests ─────────────────────────────────────────────────────

def test_full_analysis_mdr():
    susc = {"isoniazid": "R", "rifampicin": "R"}
    result = analyze_tb_resistance(susc)
    assert result["classification"]["resistance_category"] == "MDR_TB"
    assert len(result["alerts"]) > 0


def test_full_analysis_susceptible():
    susc = {"isoniazid": "S", "rifampicin": "S", "pyrazinamide": "S",
            "ethambutol": "S", "streptomycin": "S"}
    result = analyze_tb_resistance(susc)
    assert result["classification"]["resistance_category"] == "SUSCEPTIBLE"


# ─── Drug Database Tests ─────────────────────────────────────────────────────

def test_first_line_drugs_exist():
    assert "isoniazid" in FIRST_LINE_DRUGS
    assert "rifampicin" in FIRST_LINE_DRUGS
    assert "pyrazinamide" in FIRST_LINE_DRUGS
    assert "ethambutol" in FIRST_LINE_DRUGS
    assert "streptomycin" in FIRST_LINE_DRUGS


def test_second_line_drugs_exist():
    assert "fluoroquinolones" in SECOND_LINE_DRUGS
    assert "injectable_agents" in SECOND_LINE_DRUGS
    assert "bedaquiline" in SECOND_LINE_DRUGS
    assert "linezolid" in SECOND_LINE_DRUGS


# ─── CLI Tests ───────────────────────────────────────────────────────────────

def test_cli_classify():
    susc = json.dumps({"isoniazid": "R", "rifampicin": "R"})
    assert main(["classify", "--susceptibility", susc]) == 0


def test_cli_regimen():
    assert main(["regimen", "--category", "MDR_TB"]) == 0


def test_cli_help():
    with pytest.raises(SystemExit) as exc:
        main(["classify", "--help"])
    assert exc.value.code == 0
