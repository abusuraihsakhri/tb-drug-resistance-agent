"""Safety regression checks for the deterministic TB resistance interpreter."""
import csv
from pathlib import Path

import pytest

from tb_resistance import classify_tb_resistance, get_who_regimen, load_from_csv
from agents.base import AuditTrail
from tb_drug_resistance_agent.cli import _parse_csv_boolean


def test_empty_dst_never_means_susceptible():
    result = classify_tb_resistance({})
    assert result["resistance_category"] == "INDETERMINATE"
    assert result["incomplete_first_line_dst"]
    assert result["resistance_details"]["rifampicin"]["interpretation"] == "U"


def test_rr_tb_when_inh_untested():
    result = classify_tb_resistance({"rifampin": "R"})
    assert result["resistance_category"] == "RR_TB"


@pytest.mark.parametrize("inh", ["S", "U", "R"])
def test_pre_xdr_is_defined_for_all_rifampicin_resistant_tb(inh):
    result = classify_tb_resistance(
        {"rifampicin": "R", "isoniazid": inh, "levofloxacin": "R"}
    )
    assert result["resistance_category"] == "PRE_XDR_TB"


def test_xdr_does_not_require_inh_resistance():
    result = classify_tb_resistance({
        "rifampicin": "R", "isoniazid": "S",
        "moxifloxacin": "R", "linezolid": "R"
    })
    assert result["resistance_category"] == "XDR_TB"


def test_poly_resistant_does_not_become_susceptible():
    result = classify_tb_resistance({
        "inh": "S", "rif": "S", "pyrazinamide": "R", "ethambutol": "R"
    })
    assert result["resistance_category"] == "POLY_RESISTANT"


def test_untested_first_line_is_not_fully_susceptible():
    result = classify_tb_resistance({"isoniazid": "S", "rifampicin": "S"})
    assert result["resistance_category"] == "INDETERMINATE"


@pytest.mark.parametrize("value", ["X", "RESISTANT", "n/a"])
def test_invalid_dst_is_rejected(value):
    with pytest.raises(ValueError):
        classify_tb_resistance({"rifampicin": value})


def test_unknown_drug_is_rejected():
    with pytest.raises(ValueError):
        classify_tb_resistance({"not_a_drug": "S"})


def test_conflicting_alias_is_rejected():
    with pytest.raises(ValueError):
        classify_tb_resistance({"rif": "R", "rifampicin": "S"})


def test_no_automatic_susceptible_regimen_for_unknown_category():
    value = get_who_regimen("INDETERMINATE")
    assert value["drugs"] == []
    assert value["total_duration"] == "Not determined"
    assert "NOT a treatment recommendation" in value["safety_notice"]


def test_legacy_regimens_have_prominent_safety_notice():
    assert "2026" in get_who_regimen("MDR_TB")["safety_notice"]


@pytest.mark.parametrize("value,expected", [
    ("false", False), ("0", False), ("no", False),
    ("TRUE", True), ("1", True), ("yes", True),
])
def test_explicit_csv_booleans(value, expected):
    assert _parse_csv_boolean(value) is expected


def test_csv_missing_dst_fields_is_not_misclassified(tmp_path):
    file = tmp_path / "sample.csv"
    file.write_text("patient_id,isoniazid,rifampicin\nCASE1,S,S\n", encoding="utf-8")
    result = load_from_csv(str(file))
    assert len(result) == 1
    assert result[0]["classification"]["resistance_category"] == "INDETERMINATE"


def test_hmac_must_validate_signature_not_only_chain():
    ledger = AuditTrail(secret_key="test-only-key")
    ledger.log("test", "system", "EVENT", {"count": 1})
    assert ledger.verify_integrity()
    ledger.logs[0]["event_type"] = "FORGED"
    assert not ledger.verify_integrity()


def test_external_log_getter_cannot_change_internal_chain():
    ledger = AuditTrail(secret_key="test-only-key")
    ledger.log("test", "system", "EVENT", {"count": 1})
    copy = ledger.get_trail()
    copy[0]["current_hash"] = "forged"
    assert ledger.verify_integrity()


def test_second_line_resistance_not_labeled_fully_susceptible():
    result = classify_tb_resistance({
        "isoniazid": "S", "rifampicin": "S", "pyrazinamide": "S",
        "ethambutol": "S", "streptomycin": "S", "bedaquiline": "R",
    })
    assert result["resistance_category"] == "ADDITIONAL_DRUG_RESISTANCE"


def test_mock_provider_does_not_impersonate_real_llm():
    from agents.llm_factory import LLMFactory
    with pytest.raises(ValueError, match="not implemented"):
        LLMFactory.create("openai")
