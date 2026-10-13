#!/usr/bin/env python3
"""
TB Drug Resistance Interpreter

Real implementation of:
- First-line drug resistance interpretation (INH, RIF, PZA, EMB, SM)
- Resistance category classification (mono-resistant, MDR, pre-XDR, XDR)
- Key resistance mutation interpretation
- WHO treatment regimen recommendations

Uses only Python stdlib.
"""

import argparse
import csv
import json
import sys
from typing import Dict, List, Optional, Any, Tuple

# ─── First-Line TB Drugs ─────────────────────────────────────────────────────

FIRST_LINE_DRUGS = {
    "isoniazid": {
        "abbreviation": "INH",
        "drug_class": "first_line",
        "critical": True,
        "resistance_mutations": {
            "katG_S315T": {"level": "high", "frequency": 0.50, "description": "Most common INH resistance mutation; high-level resistance"},
            "katG_other": {"level": "high", "frequency": 0.10, "description": "Other katG mutations causing high-level resistance"},
            "inhA_promoter": {"level": "low", "frequency": 0.25, "description": "inhA promoter mutations; low-level resistance, may respond to higher doses"},
            "inhA_structural": {"level": "low_to_moderate", "frequency": 0.05, "description": "inhA structural gene mutations"},
            "ahpC_promoter": {"level": "variable", "frequency": 0.05, "description": "Often compensatory; may indicate katG mutation"},
            "fabG1_promoter": {"level": "low", "frequency": 0.03, "description": "Linked to inhA promoter mutations"},
        },
        "mic_breakpoints": {"susceptible": 0.1, "resistant": 0.4},
    },
    "rifampicin": {
        "abbreviation": "RIF",
        "drug_class": "first_line",
        "critical": True,
        "resistance_mutations": {
            "rpoB_S531L": {"level": "high", "frequency": 0.45, "description": "Most common RIF resistance mutation (codon 531)"},
            "rpoB_H526Y": {"level": "high", "frequency": 0.15, "description": "Second most common (codon 526)"},
            "rpoB_D516V": {"level": "moderate", "frequency": 0.10, "description": "Codon 516 mutation"},
            "rpoB_L511P": {"level": "moderate", "frequency": 0.05, "description": "Codon 511 mutation"},
            "rpoB_other": {"level": "variable", "frequency": 0.10, "description": "Other RRDR mutations"},
        },
        "mic_breakpoints": {"susceptible": 1.0, "resistant": 1.0},
    },
    "pyrazinamide": {
        "abbreviation": "PZA",
        "drug_class": "first_line",
        "critical": False,
        "resistance_mutations": {
            "pncA_missense": {"level": "variable", "frequency": 0.60, "description": "pncA missense mutations"},
            "pncA_frameshift": {"level": "high", "frequency": 0.15, "description": "pncA frameshift/nonsense mutations"},
            "pncA_promoter": {"level": "variable", "frequency": 0.10, "description": "pncA promoter mutations"},
        },
        "mic_breakpoints": {"susceptible": 100.0, "resistant": 100.0},
    },
    "ethambutol": {
        "abbreviation": "EMB",
        "drug_class": "first_line",
        "critical": False,
        "resistance_mutations": {
            "embB_M306I": {"level": "moderate", "frequency": 0.40, "description": "Most common EMB resistance mutation"},
            "embB_M306V": {"level": "moderate", "frequency": 0.15, "description": "Second most common embB mutation"},
            "embB_M306L": {"level": "moderate", "frequency": 0.05, "description": "Less common embB mutation"},
            "embB_other": {"level": "variable", "frequency": 0.10, "description": "Other embB/embC/embA mutations"},
        },
        "mic_breakpoints": {"susceptible": 5.0, "resistant": 10.0},
    },
    "streptomycin": {
        "abbreviation": "SM",
        "drug_class": "first_line",
        "critical": False,
        "resistance_mutations": {
            "rpsL_K43R": {"level": "high", "frequency": 0.35, "description": "Most common SM resistance mutation"},
            "rpsL_K88R": {"level": "high", "frequency": 0.20, "description": "Second most common rpsL mutation"},
            "rrs_514": {"level": "moderate", "frequency": 0.15, "description": "rrs 514 A>C mutation"},
            "rrs_other": {"level": "variable", "frequency": 0.10, "description": "Other rrs mutations"},
            "gidB": {"level": "low", "frequency": 0.10, "description": "gidB mutations (low-level)"},
        },
        "mic_breakpoints": {"susceptible": 2.0, "resistant": 8.0},
    },
}

# ─── Second-Line TB Drugs ────────────────────────────────────────────────────

SECOND_LINE_DRUGS = {
    "fluoroquinolones": {
        "drugs": ["moxifloxacin", "levofloxacin", "gatifloxacin"],
        "abbreviation": "FQ",
        "drug_class": "second_line",
        "resistance_mutations": {
            "gyrA_D94G": {"level": "high", "frequency": 0.25, "description": "Most common FQ resistance mutation"},
            "gyrA_A90V": {"level": "high", "frequency": 0.20, "description": "Common gyrA mutation"},
            "gyrA_S91P": {"level": "moderate", "frequency": 0.10, "description": "gyrA codon 91 mutation"},
            "gyrA_D94A": {"level": "moderate", "frequency": 0.08, "description": "gyrA codon 94 mutation"},
            "gyrB": {"level": "low_to_moderate", "frequency": 0.05, "description": "gyrB mutations"},
        },
    },
    "injectable_agents": {
        "drugs": ["amikacin", "kanamycin", "capreomycin"],
        "abbreviation": "INJ",
        "drug_class": "second_line",
        "resistance_mutations": {
            "rrs_1401": {"level": "high", "frequency": 0.40, "description": "rrs A1401G mutation (amikacin/kanamycin)"},
            "rrs_1484": {"level": "high", "frequency": 0.10, "description": "rrs G1484T mutation (capreomycin)"},
            "eis_promoter": {"level": "low_to_moderate", "frequency": 0.15, "description": "eis promoter mutation (kanamycin)"},
            "tlyA": {"level": "moderate", "frequency": 0.05, "description": "tlyA mutation (capreomycin)"},
        },
    },
    "bedaquiline": {
        "drugs": ["bedaquiline"],
        "abbreviation": "BDQ",
        "drug_class": "new_drug",
        "resistance_mutations": {
            "atpE_mutations": {"level": "high", "frequency": 0.30, "description": "atpE gene mutations"},
            "Rv0678_mutations": {"level": "moderate", "frequency": 0.20, "description": "Rv0678 (mmpR) mutations"},
            "pepQ_mutations": {"level": "low", "frequency": 0.05, "description": "pepQ mutations"},
        },
    },
    "linezolid": {
        "drugs": ["linezolid"],
        "abbreviation": "LZD",
        "drug_class": "new_drug",
        "resistance_mutations": {
            "rrl_2270": {"level": "high", "frequency": 0.30, "description": "rrl A2270G/C mutation"},
            "rplC_C154R": {"level": "moderate", "frequency": 0.15, "description": "rplC C154R mutation"},
        },
    },
}


# ─── Resistance Category Classification ──────────────────────────────────────

def classify_tb_resistance(
    susceptibility: Dict[str, str],
    mutations: Optional[Dict[str, List[str]]] = None,
) -> Dict[str, Any]:
    """Classify TB drug resistance pattern.

    Args:
        susceptibility: Dict mapping drug name to 'S' or 'R'
        mutations: Optional dict mapping gene to list of detected mutations

    Returns:
        Dict with resistance category, details, and clinical implications
    """
    # Unknown or untested results must never be interpreted as susceptible.
    if not isinstance(susceptibility, dict):
        raise ValueError("Susceptibility must be a mapping of drugs to S, R or U.")

    aliases = {
        "inh": "isoniazid", "h": "isoniazid",
        "rif": "rifampicin", "r": "rifampicin", "rifampin": "rifampicin",
        "pza": "pyrazinamide", "z": "pyrazinamide",
        "emb": "ethambutol", "e": "ethambutol",
        "sm": "streptomycin",
        "mfx": "moxifloxacin", "lfx": "levofloxacin",
        "fq": "fluoroquinolones", "bdq": "bedaquiline",
        "lzd": "linezolid",
    }
    valid_drugs = set(FIRST_LINE_DRUGS) | {
        "moxifloxacin", "levofloxacin", "gatifloxacin",
        "fluoroquinolones", "amikacin", "kanamycin",
        "capreomycin", "injectable_agents", "bedaquiline", "linezolid",
    }
    susc = {}
    for key, value in susceptibility.items():
        if not isinstance(key, str) or not isinstance(value, str):
            raise ValueError("Drug names and susceptibility results must be strings.")
        drug = aliases.get(key.strip().lower().replace(" ", "_"), key.strip().lower().replace(" ", "_"))
        if drug not in valid_drugs:
            raise ValueError(f"Unknown drug: {key!r}")
        state = value.strip().upper()
        if state in ("", "UNKNOWN", "NOT_TESTED", "NT"):
            state = "U"
        if state not in ("S", "R", "U"):
            raise ValueError(f"Invalid result for {key!r}: expected S, R or U")
        if drug in susc and susc[drug] != state:
            raise ValueError(f"Conflicting susceptibility results for {drug}")
        susc[drug] = state

    inh = susc.get("isoniazid", "U")
    rif = susc.get("rifampicin", "U")
    inh_resistant = inh == "R"
    rif_resistant = rif == "R"
    pza_resistant = susc.get("pyrazinamide") == "R"
    emb_resistant = susc.get("ethambutol") == "R"
    sm_resistant = susc.get("streptomycin") == "R"
    fq_drugs = ("moxifloxacin", "levofloxacin", "gatifloxacin", "fluoroquinolones")
    fq_resistant = any(susc.get(d) == "R" for d in fq_drugs)
    inj_resistant = any(susc.get(d) == "R" for d in
                        ("amikacin", "kanamycin", "capreomycin", "injectable_agents"))
    bdq_resistant = susc.get("bedaquiline") == "R"
    lzd_resistant = susc.get("linezolid") == "R"
    first_line_resistant_count = sum(
        susc.get(d) == "R" for d in FIRST_LINE_DRUGS
    )

    resistance_category = "INDETERMINATE"
    subcategory = "Insufficient first-line DST to establish a resistance category"
    clinical_significance = "UNDETERMINED"

    if rif_resistant:
        if inh_resistant:
            resistance_category = "MDR_TB"
            subcategory = "Rifampicin and isoniazid resistance (MDR-TB)"
        elif inh == "S":
            resistance_category = "RIF_MONO_RESISTANT" if first_line_resistant_count == 1 else "RIF_RESISTANT"
            subcategory = "Rifampicin-resistant TB (isoniazid susceptible)"
        else:
            resistance_category = "RR_TB"
            subcategory = "Rifampicin-resistant TB; isoniazid susceptibility unknown"
        clinical_significance = "HIGH"
        if fq_resistant:
            resistance_category = "PRE_XDR_TB"
            subcategory = "Pre-XDR-TB (rifampicin resistant and fluoroquinolone resistant)"
            clinical_significance = "VERY_HIGH"
            if bdq_resistant or lzd_resistant:
                resistance_category = "XDR_TB"
                drugs = [d for d, resistant in
                         (("bedaquiline", bdq_resistant), ("linezolid", lzd_resistant))
                         if resistant]
                subcategory = "XDR-TB (pre-XDR plus " + "+".join(drugs) + " resistance)"
                clinical_significance = "CRITICAL"
    elif rif == "S" and inh_resistant:
        resistance_category = "INH_MONO_RESISTANT" if first_line_resistant_count == 1 else "INH_POLY_RESISTANT"
        subcategory = "Isoniazid-resistant, rifampicin-susceptible TB"
        clinical_significance = "MODERATE"
    elif rif == "S" and inh == "S":
        other_resistant = [
            d for d in ("pyrazinamide", "ethambutol", "streptomycin")
            if susc.get(d) == "R"
        ]
        if len(other_resistant) == 1:
            resistance_category = "MONO_RESISTANT"
            subcategory = f"Mono-resistant to {FIRST_LINE_DRUGS[other_resistant[0]]['abbreviation']}"
            clinical_significance = "MODERATE"
        elif len(other_resistant) > 1:
            resistance_category = "POLY_RESISTANT"
            subcategory = "Resistance to multiple first-line drugs other than INH/RIF"
            clinical_significance = "MODERATE"
        elif fq_resistant or inj_resistant or bdq_resistant or lzd_resistant:
            resistance_category = "ADDITIONAL_DRUG_RESISTANCE"
            subcategory = "Second-line resistance recorded without first-line resistance; specialist review required"
            clinical_significance = "UNDETERMINED"
        elif any(susc.get(d, "U") == "U" for d in FIRST_LINE_DRUGS):
            subcategory = "No documented first-line resistance; DST incomplete"
        else:
            resistance_category = "SUSCEPTIBLE"
            subcategory = "All five recorded first-line susceptibility results are S"
            clinical_significance = "LOW"

    untested_drugs = [d for d in FIRST_LINE_DRUGS if susc.get(d, "U") == "U"]
    # Build resistance details
    resistance_details = {}
    for drug_name, drug_info in FIRST_LINE_DRUGS.items():
        drug_key = drug_name.lower().replace(" ", "_")
        state = susc.get(drug_key, "U")
        is_r = state == "R"
        resistance_details[drug_name] = {
            "abbreviation": drug_info["abbreviation"],
            "resistant": is_r,
            "interpretation": state,
            "critical": drug_info["critical"],
        }

    # Analyze mutations if provided
    mutation_analysis = {}
    if mutations:
        mutation_analysis = _analyze_mutations(mutations, susc)

    return {
        "resistance_category": resistance_category,
        "subcategory": subcategory,
        "clinical_significance": clinical_significance,
        "first_line_resistance": {
            "isoniazid": inh_resistant,
            "rifampicin": rif_resistant,
            "pyrazinamide": pza_resistant,
            "ethambutol": emb_resistant,
            "streptomycin": sm_resistant,
        },
        "second_line_resistance": {
            "fluoroquinolones": fq_resistant,
            "injectable_agents": inj_resistant,
            "bedaquiline": bdq_resistant,
            "linezolid": lzd_resistant,
        },
        "resistant_drug_count": first_line_resistant_count,
        "untested_first_line_drugs": untested_drugs,
        "incomplete_first_line_dst": bool(untested_drugs),
        "classification_standard": "WHO 2021 MDR/RR-TB, pre-XDR and XDR definitions",
        "resistance_details": resistance_details,
        "mutation_analysis": mutation_analysis,
    }


def _analyze_mutations(mutations: Dict[str, List[str]],
                        susceptibility: Dict[str, str]) -> Dict[str, Any]:
    """Analyze detected mutations for clinical significance."""
    analysis = {"detected_mutations": [], "drug_implications": {}}

    all_drug_mutations = {}
    for drug_name, drug_info in FIRST_LINE_DRUGS.items():
        all_drug_mutations[drug_name] = drug_info["resistance_mutations"]
    for group_name, group_info in SECOND_LINE_DRUGS.items():
        all_drug_mutations[group_name] = group_info["resistance_mutations"]

    for gene, mutation_list in mutations.items():
        for mutation in mutation_list:
            mutation_key = f"{gene}_{mutation}"
            found = False
            for drug_name, mut_dict in all_drug_mutations.items():
                if mutation_key in mut_dict:
                    mut_info = mut_dict[mutation_key]
                    analysis["detected_mutations"].append({
                        "mutation": mutation_key,
                        "drug": drug_name,
                        "resistance_level": mut_info["level"],
                        "frequency": mut_info["frequency"],
                        "description": mut_info["description"],
                    })
                    found = True
            if not found:
                # Try partial matching
                for drug_name, mut_dict in all_drug_mutations.items():
                    for known_mut, mut_info in mut_dict.items():
                        if gene in known_mut and mutation in known_mut:
                            analysis["detected_mutations"].append({
                                "mutation": mutation_key,
                                "drug": drug_name,
                                "resistance_level": mut_info["level"],
                                "frequency": mut_info["frequency"],
                                "description": mut_info["description"],
                            })
                            found = True
                            break

    return analysis


# ─── WHO Treatment Regimen Recommendations ───────────────────────────────────

def get_who_regimen(resistance_category: str,
                     additional_resistance: Optional[Dict[str, bool]] = None) -> Dict[str, Any]:
    """Get WHO treatment regimen recommendation based on resistance pattern.

    Based on WHO consolidated guidelines on TB (2022 update).

    Args:
        resistance_category: One of SUSCEPTIBLE, MONO_RESISTANT, INH_MONO_RESISTANT,
                            RIF_MONO_RESISTANT, MDR_TB, PRE_XDR_TB, XDR_TB
        additional_resistance: Dict of additional drug resistance flags

    Returns:
        Dict with regimen recommendation, duration, and monitoring
    """
    ar = additional_resistance or {}

    regimens = {
        "SUSCEPTIBLE": {
            "regimen_name": "Standard first-line regimen (2HRZE/4HR)",
            "drugs": [
                {"drug": "Isoniazid (H)", "dose": "5 mg/kg (max 300mg)", "duration": "6 months"},
                {"drug": "Rifampicin (R)", "dose": "10 mg/kg (max 600mg)", "duration": "6 months"},
                {"drug": "Pyrazinamide (Z)", "dose": "25 mg/kg (max 2g)", "duration": "2 months"},
                {"drug": "Ethambutol (E)", "dose": "15-20 mg/kg (max 1.6g)", "duration": "2 months"},
            ],
            "phases": [
                {"phase": "Intensive", "duration": "2 months", "drugs": "HRZE"},
                {"phase": "Continuation", "duration": "4 months", "drugs": "HR"},
            ],
            "total_duration": "6 months",
            "monitoring": [
                "Monthly sputum cultures until conversion",
                "LFTs at baseline, 2 weeks, then monthly",
                "Visual acuity testing for ethambutol",
                "CBC at baseline and as needed",
            ],
        },
        "INH_MONO_RESISTANT": {
            "regimen_name": "INH mono-resistant regimen (6RZES or 6RZE)",
            "drugs": [
                {"drug": "Rifampicin (R)", "dose": "10 mg/kg (max 600mg)", "duration": "6 months"},
                {"drug": "Pyrazinamide (Z)", "dose": "25 mg/kg (max 2g)", "duration": "6 months"},
                {"drug": "Ethambutol (E)", "dose": "15-20 mg/kg (max 1.6g)", "duration": "6 months"},
                {"drug": "Streptomycin (S) or Fluoroquinolone", "dose": "Per weight band", "duration": "2 months"},
            ],
            "phases": [
                {"phase": "Intensive", "duration": "2 months", "drugs": "RZES or RZEFQ"},
                {"phase": "Continuation", "duration": "4 months", "drugs": "RZE"},
            ],
            "total_duration": "6 months",
            "monitoring": [
                "Monthly sputum cultures until conversion",
                "LFTs monthly",
                "Audiometry if streptomycin used",
            ],
        },
        "RIF_MONO_RESISTANT": {
            "regimen_name": "RIF mono-resistant regimen (treat as MDR-TB)",
            "drugs": [
                {"drug": "Fluoroquinolone (Lfx/Mfx)", "dose": "750-1000mg/400mg", "duration": "9-12 months"},
                {"drug": "Ethionamide/Prothionamide", "dose": "15-20 mg/kg", "duration": "9-12 months"},
                {"drug": "Pyrazinamide (Z)", "dose": "25 mg/kg", "duration": "9-12 months"},
                {"drug": "Ethambutol (E)", "dose": "15-20 mg/kg", "duration": "9-12 months"},
                {"drug": "Injectable agent", "dose": "Per weight band", "duration": "4-6 months"},
            ],
            "phases": [
                {"phase": "Intensive", "duration": "4-6 months", "drugs": "Lfx-Eto-Z-E-Inj"},
                {"phase": "Continuation", "duration": "5-6 months", "drugs": "Lfx-Eto-Z-E"},
            ],
            "total_duration": "9-12 months",
            "monitoring": [
                "Monthly sputum cultures",
                "Audiometry for injectable agents",
                "Thyroid function if ethionamide used",
                "ECG monitoring",
            ],
        },
        "MDR_TB": {
            "regimen_name": "WHO MDR/RR-TB regimen (BPaL or longer regimen)",
            "drugs": [
                {"drug": "Bedaquiline (B)", "dose": "200mg daily x8w then 100mg 3x/w", "duration": "6 months"},
                {"drug": "Pretomanid (Pa)", "dose": "200mg daily", "duration": "6 months"},
                {"drug": "Linezolid (L)", "dose": "600mg daily", "duration": "6 months"},
            ],
            "phases": [
                {"phase": "All-oral BPaL regimen", "duration": "6 months (up to 9 months)", "drugs": "BPaL"},
            ],
            "total_duration": "6-9 months",
            "alternative_regimen": {
                "name": "Longer individualized regimen (9-20 months)",
                "drugs": [
                    "Fluoroquinolone (Lfx or Mfx)",
                    "Bedaquiline",
                    "Linezolid",
                    "Clofazimine",
                    "Cycloserine/Terizidone",
                ],
            },
            "monitoring": [
                "Monthly sputum cultures",
                "ECG at baseline, 2 weeks, monthly (QTc monitoring for bedaquiline)",
                "CBC weekly x2, then monthly (linezolid toxicity)",
                "LFTs monthly",
                "Visual acuity and color vision",
                "Peripheral neuropathy assessment",
            ],
        },
        "PRE_XDR_TB": {
            "regimen_name": "Pre-XDR-TB regimen (BPaL-based)",
            "drugs": [
                {"drug": "Bedaquiline (B)", "dose": "200mg daily x8w then 100mg 3x/w", "duration": "6-9 months"},
                {"drug": "Pretomanid (Pa)", "dose": "200mg daily", "duration": "6-9 months"},
                {"drug": "Linezolid (L)", "dose": "600mg daily", "duration": "6-9 months"},
            ],
            "phases": [
                {"phase": "BPaL regimen", "duration": "6-9 months", "drugs": "BPaL"},
            ],
            "total_duration": "6-9 months",
            "notes": "FQ resistance confirmed; BPaL regimen per TB-PRACTECAL/Nix-TB trial data",
            "monitoring": [
                "Monthly sputum cultures",
                "ECG monitoring (QTc) for bedaquiline",
                "CBC monitoring for linezolid (myelosuppression)",
                "Peripheral neuropathy assessment",
                "Hepatotoxicity monitoring",
            ],
        },
        "XDR_TB": {
            "regimen_name": "XDR-TB regimen (individualized, BPaL-based backbone)",
            "drugs": [
                {"drug": "Bedaquiline (B)", "dose": "200mg daily x8w then 100mg 3x/w", "duration": "9-18 months"},
                {"drug": "Pretomanid (Pa)", "dose": "200mg daily", "duration": "9-18 months"},
                {"drug": "Linezolid (L)", "dose": "600mg daily (may reduce to 300mg)", "duration": "9-18 months"},
            ],
            "phases": [
                {"phase": "Individualized regimen", "duration": "9-18 months", "drugs": "BPaL backbone + additional agents"},
            ],
            "total_duration": "9-18+ months",
            "notes": "XDR-TB requires individualized regimen with expert consultation. "
                     "Add remaining active agents based on full DST. Consider delamanid, "
                     "clofazimine, cycloserine, or other agents with demonstrated susceptibility.",
            "monitoring": [
                "Monthly sputum cultures throughout treatment",
                "ECG monitoring (QTc) for bedaquiline",
                "Weekly CBC for linezolid toxicity",
                "Peripheral neuropathy assessment",
                "Hepatotoxicity monitoring",
                "Expert MDR-TB panel consultation recommended",
            ],
        },
        "MONO_RESISTANT": {
            "regimen_name": "Modified first-line regimen",
            "drugs": [
                {"drug": "Isoniazid (H)", "dose": "5 mg/kg (max 300mg)", "duration": "6 months"},
                {"drug": "Rifampicin (R)", "dose": "10 mg/kg (max 600mg)", "duration": "6 months"},
                {"drug": "Pyrazinamide (Z)", "dose": "25 mg/kg (max 2g)", "duration": "2 months"},
                {"drug": "Fluoroquinolone", "dose": "Per weight band", "duration": "2 months"},
            ],
            "phases": [
                {"phase": "Intensive", "duration": "2 months", "drugs": "HRZ + FQ"},
                {"phase": "Continuation", "duration": "4 months", "drugs": "HR"},
            ],
            "total_duration": "6 months",
            "monitoring": [
                "Monthly sputum cultures until conversion",
                "LFTs monthly",
            ],
        },
    }

    # Retained for backward compatibility. Regimen tables are historical examples,
    # not validated prescribing advice; never silently substitute susceptible treatment.
    if resistance_category in regimens:
        regimen = dict(regimens[resistance_category])
    else:
        regimen = {
            "regimen_name": "No automated regimen available",
            "drugs": [],
            "phases": [],
            "total_duration": "Not determined",
            "monitoring": [],
        }
    regimen["resistance_category"] = resistance_category
    regimen["safety_notice"] = (
        "Historical, unvalidated examples only; NOT a treatment recommendation. "
        "This table has not been updated for WHO module 4 (2026). "
        "Do not use to prescribe, dose or select a regimen. Consult current WHO "
        "guidance, complete DST and a qualified TB specialist."
    )
    return regimen


# ─── Full TB Resistance Analysis ─────────────────────────────────────────────

def analyze_tb_resistance(
    susceptibility: Dict[str, str],
    mutations: Optional[Dict[str, List[str]]] = None,
) -> Dict[str, Any]:
    """Complete TB drug resistance analysis.

    Args:
        susceptibility: Dict mapping drug name to 'S' or 'R'
        mutations: Optional dict mapping gene to list of detected mutations

    Returns:
        Comprehensive analysis with classification, regimen, and monitoring
    """
    classification = classify_tb_resistance(susceptibility, mutations)
    regimen = get_who_regimen(
        classification["resistance_category"],
        classification.get("second_line_resistance"),
    )

    # Generate alerts
    alerts = []
    cat = classification["resistance_category"]

    if cat in ("MDR_TB", "RR_TB", "RIF_RESISTANT", "PRE_XDR_TB", "XDR_TB"):
        alerts.append({
            "severity": "CRITICAL",
            "type": "MULTI_DRUG_RESISTANCE",
            "message": f"{classification['subcategory']} detected",
            "recommendation": "Refer to a drug-resistant TB specialist; confirm full DST before treatment selection.",
        })

    if cat == "RIF_MONO_RESISTANT":
        alerts.append({
            "severity": "HIGH",
            "type": "RIF_MONO_RESISTANCE",
            "message": "Rifampicin mono-resistance detected - treat as MDR-TB pending full DST",
            "recommendation": "Obtain full second-line DST and expert consultation.",
        })

    if cat == "XDR_TB":
        alerts.append({
            "severity": "CRITICAL",
            "type": "XDR_TB",
            "message": "Extensively drug-resistant TB detected",
            "recommendation": "Urgent referral to specialized MDR/XDR-TB center. "
                            "Individualized regimen required with expert consultation.",
        })

    return {
        "classification": classification,
        "regimen_recommendation": regimen,
        "alerts": alerts,
    }


# ─── CSV Processing ──────────────────────────────────────────────────────────

def load_from_csv(filepath: str) -> List[Dict[str, Any]]:
    """Load TB susceptibility data from CSV and analyze each record."""
    results = []
    with open(filepath, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            susceptibility = {}
            for col, val in row.items():
                if col is None:
                    continue
                col_l = col.strip().lower()
                val_u = (val or "").strip().upper()
                if col_l in FIRST_LINE_DRUGS or col_l in (
                    "inh", "rif", "rifampin", "pza", "emb", "sm",
                    "moxifloxacin", "levofloxacin", "gatifloxacin",
                    "fluoroquinolones", "amikacin", "kanamycin", "capreomycin",
                    "injectable_agents", "bedaquiline", "linezolid",
                ):
                    if val_u in ("S", "R", "U", "UNKNOWN", ""):
                        susceptibility[col.strip()] = val_u or "U"
                    else:
                        raise ValueError(f"Invalid DST result {val!r} in column {col!r}")
            if susceptibility:
                result = analyze_tb_resistance(susceptibility)
                result["raw_data"] = dict(row)
                results.append(result)
    return results


# ─── CLI ──────────────────────────────────────────────────────────────────────

def build_parser():
    """Build the argument parser."""
    p = argparse.ArgumentParser(
        prog="tb-resistance",
        description="TB Drug Resistance Interpreter"
    )
    sub = p.add_subparsers(dest="cmd")

    # Classify command
    s_classify = sub.add_parser("classify", help="Classify TB resistance pattern")
    s_classify.add_argument("--susceptibility", required=True,
                            help="JSON string of drug:S/R pairs")
    s_classify.add_argument("--mutations", help="JSON string of gene:[mutations] pairs")

    # Regimen command
    s_regimen = sub.add_parser("regimen", help="Get WHO regimen recommendation")
    s_regimen.add_argument("--category", required=True,
                           choices=["SUSCEPTIBLE", "MONO_RESISTANT", "INH_MONO_RESISTANT",
                                    "RIF_MONO_RESISTANT", "MDR_TB", "PRE_XDR_TB", "XDR_TB"])

    # CSV command
    s_csv = sub.add_parser("csv", help="Analyze TB resistance from CSV")
    s_csv.add_argument("--input", required=True, help="Input CSV file")
    s_csv.add_argument("--output", help="Output JSON file")

    return p


def main(argv=None):
    """CLI entry point."""
    p = build_parser()
    args = p.parse_args(argv)

    if args.cmd == "classify":
        susc = json.loads(args.susceptibility)
        muts = json.loads(args.mutations) if args.mutations else None
        result = analyze_tb_resistance(susc, muts)
        print(json.dumps(result, indent=2))
        return 0

    elif args.cmd == "regimen":
        regimen = get_who_regimen(args.category)
        print(json.dumps(regimen, indent=2))
        return 0

    elif args.cmd == "csv":
        results = load_from_csv(args.input)
        print(json.dumps(results, indent=2))
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2)
        return 0

    else:
        p.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
