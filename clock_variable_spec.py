from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class VariableSpec:
    name: str
    domain: str
    preferred_measure: str
    allowed_proxies: tuple[str, ...]
    expected_direction: str
    rationale: str


@dataclass(frozen=True)
class DatasetPath:
    name: str
    status: str
    description: str


@dataclass(frozen=True)
class VariableMapping:
    clock_variable: str
    source_dataset: str
    source_columns: tuple[str, ...]
    transform: str
    proxy_tier: str
    notes: str


LOCKED_V1_PANEL: tuple[VariableSpec, ...] = (
    VariableSpec(
        name="fitness",
        domain="physiologic_reserve",
        preferred_measure="VO2max",
        allowed_proxies=("estimated_cardiorespiratory_fitness",),
        expected_direction="higher_is_healthier",
        rationale="Cardiorespiratory fitness is one of the strongest all-cause mortality signals.",
    ),
    VariableSpec(
        name="central_adiposity",
        domain="metabolic_burden",
        preferred_measure="visceral_fat",
        allowed_proxies=("waist_to_height_ratio", "waist_circumference"),
        expected_direction="lower_is_healthier",
        rationale="Central fat distribution captures metabolic risk more directly than body weight alone.",
    ),
    VariableSpec(
        name="glycemia",
        domain="metabolic_burden",
        preferred_measure="HbA1c",
        allowed_proxies=(),
        expected_direction="lower_is_healthier",
        rationale="HbA1c captures chronic glycemic dysregulation with strong mortality relevance.",
    ),
    VariableSpec(
        name="atherogenic_burden",
        domain="cardiovascular_burden",
        preferred_measure="ApoB",
        allowed_proxies=("non_HDL_cholesterol",),
        expected_direction="lower_is_healthier",
        rationale="ApoB best tracks atherogenic particle burden; non-HDL is the fallback proxy.",
    ),
    VariableSpec(
        name="hemodynamic_stress",
        domain="cardiovascular_burden",
        preferred_measure="systolic_blood_pressure",
        allowed_proxies=(),
        expected_direction="lower_is_healthier",
        rationale="Systolic pressure adds vascular load information beyond lipids and glucose.",
    ),
    VariableSpec(
        name="kidney_function",
        domain="organ_resilience",
        preferred_measure="Cystatin_C",
        allowed_proxies=(),
        expected_direction="lower_is_healthier",
        rationale="Cystatin C is a stronger aging-risk kidney marker than creatinine for this clock.",
    ),
    VariableSpec(
        name="inflammation",
        domain="systemic_stress",
        preferred_measure="CRP",
        allowed_proxies=("hs_CRP",),
        expected_direction="lower_is_healthier",
        rationale="CRP captures systemic inflammatory burden relevant to mortality and aging.",
    ),
    VariableSpec(
        name="lung_function",
        domain="physiologic_reserve",
        preferred_measure="FEV1",
        allowed_proxies=("FVC",),
        expected_direction="higher_is_healthier",
        rationale="FEV1 adds non-cardiac reserve information and is strongly mortality-linked.",
    ),
)


PRIMARY_DATASET_PATH = DatasetPath(
    name="NHANES_1999_2002_linked_mortality",
    status="chosen_primary",
    description=(
        "First executable open-access path. Chosen because it is public and supports direct fitness, "
        "Cystatin C, CRP, waist, blood pressure, HbA1c, and a lipid proxy for ApoB."
    ),
)


BACKUP_DATASET_PATH = DatasetPath(
    name="UK_Biobank_full_panel",
    status="backup_higher_coverage",
    description=(
        "Richer marker coverage with less proxy pressure, but higher access friction and less immediate reproducibility."
    ),
)


NHANES_1999_2002_VARIABLE_MAP: tuple[VariableMapping, ...] = (
    VariableMapping(
        clock_variable="chronological_age",
        source_dataset="DEMO",
        source_columns=("RIDAGEYR",),
        transform="use RIDAGEYR directly",
        proxy_tier="direct",
        notes="Required later for age calibration and age acceleration.",
    ),
    VariableMapping(
        clock_variable="fitness",
        source_dataset="CVX",
        source_columns=("CVDVOMAX",),
        transform="use predicted VO2max directly",
        proxy_tier="direct",
        notes="Preferred over estimated CRF because this slice includes direct treadmill-derived fitness.",
    ),
    VariableMapping(
        clock_variable="central_adiposity",
        source_dataset="BMX",
        source_columns=("BMXWAIST", "BMXHT"),
        transform="prefer BMXWAIST / BMXHT for waist-to-height ratio; fall back to BMXWAIST if height is missing",
        proxy_tier="proxy_1",
        notes="Visceral fat is unavailable in this slice, so use the strongest body-size proxy allowed by the spec.",
    ),
    VariableMapping(
        clock_variable="glycemia",
        source_dataset="LAB10_or_L10_B",
        source_columns=("LBXGH",),
        transform="use HbA1c percentage directly",
        proxy_tier="direct",
        notes="1999-2000 and 2001-2002 files use the same glycohemoglobin field name.",
    ),
    VariableMapping(
        clock_variable="atherogenic_burden",
        source_dataset="LAB13_or_equivalent",
        source_columns=("LBXTC", "LBXHDD"),
        transform="compute non_HDL = LBXTC - LBXHDD",
        proxy_tier="proxy_1",
        notes="ApoB is not reliably available in the chosen open slice, so non-HDL is the locked fallback.",
    ),
    VariableMapping(
        clock_variable="hemodynamic_stress",
        source_dataset="BPX",
        source_columns=("BPXSY1", "BPXSY2", "BPXSY3", "BPXSY4"),
        transform="take the mean of available systolic readings",
        proxy_tier="direct",
        notes="Use the participant-level average to reduce measurement noise.",
    ),
    VariableMapping(
        clock_variable="kidney_function",
        source_dataset="SSCYST_B_or_equivalent",
        source_columns=("SSCYPC",),
        transform="use Cystatin C mg/L directly",
        proxy_tier="direct",
        notes="This is the main reason the older NHANES slice was chosen over later cycles.",
    ),
    VariableMapping(
        clock_variable="inflammation",
        source_dataset="LAB11_or_equivalent",
        source_columns=("LBXCRP",),
        transform="use CRP directly; log-transform later during model fitting if distribution is highly skewed",
        proxy_tier="direct",
        notes="Older NHANES exposes CRP rather than later hs-CRP naming, but this still satisfies the selected domain.",
    ),
    VariableMapping(
        clock_variable="lung_function",
        source_dataset="SPX_or_equivalent",
        source_columns=("SPXFEV1",),
        transform="use FEV1 liters directly after cycle-specific harmonization",
        proxy_tier="direct",
        notes="Cycle documentation should be checked during ingestion because spirometry file names can vary by release.",
    ),
)


UKB_HIGH_COVERAGE_NOTES: dict[str, str] = {
    "ApoB": "Field 30640 is available and removes the need for a lipid proxy.",
    "CRP": "Field 30710 is available as high-sensitivity CRP.",
    "systolic_blood_pressure": "Field 4080 is available for automated systolic blood pressure.",
    "waist_circumference": "Field 48 is available for central adiposity.",
    "remaining_fields": "HbA1c, Cystatin C, FEV1, and fitness are available in UK Biobank, but access friction is higher.",
}
