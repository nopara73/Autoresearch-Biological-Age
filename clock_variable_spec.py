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
    name="UK_Biobank_full_panel",
    status="chosen_primary",
    description=(
        "Richer marker coverage with direct ApoB and spirometry, better overlap with the locked panel, "
        "and stronger ACM-oriented scaling potential."
    ),
)


PUBLIC_FALLBACK_DATASET_PATH = DatasetPath(
    name="NHANES_2001_2002_public_path",
    status="public_fallback",
    description=(
        "Open-access fallback that preserves direct fitness and cystatin C, but requires a lipid proxy and "
        "cannot restore lung function cleanly in the same public slice."
    ),
)


UK_BIOBANK_VARIABLE_MAP: tuple[VariableMapping, ...] = (
    VariableMapping(
        clock_variable="chronological_age",
        source_dataset="UKB_main_export",
        source_columns=("f.21022.0.0", "age_at_recruitment"),
        transform="use age at recruitment directly",
        proxy_tier="direct",
        notes="Field 21022 is the clean primary age anchor for bio_age calibration.",
    ),
    VariableMapping(
        clock_variable="fitness",
        source_dataset="UKB_main_export",
        source_columns=("cardiorespiratory_fitness", "estimated_crf", "vo2max", "vo2_max"),
        transform="prefer direct or derived cardiorespiratory fitness from the UKB exercise test export",
        proxy_tier="direct_or_proxy_1",
        notes="Exact export columns vary by application and preprocessing pipeline.",
    ),
    VariableMapping(
        clock_variable="central_adiposity",
        source_dataset="UKB_main_export_or_imaging",
        source_columns=("f.22407.2.0", "visceral_adipose_tissue", "f.48.0.0", "waist_circumference"),
        transform="prefer VAT if available; otherwise use waist-to-height ratio or waist circumference equivalent",
        proxy_tier="direct_or_proxy_1",
        notes="VAT is imaging-subset only, so waist-based fallbacks remain necessary for larger analytic samples.",
    ),
    VariableMapping(
        clock_variable="glycemia",
        source_dataset="UKB_main_export",
        source_columns=("f.30750.0.0", "hba1c", "glycated_haemoglobin"),
        transform="use HbA1c directly",
        proxy_tier="direct",
        notes="HbA1c is expected as a direct biochemistry measurement in UKB exports.",
    ),
    VariableMapping(
        clock_variable="atherogenic_burden",
        source_dataset="UKB_main_export",
        source_columns=("f.30640.0.0", "apolipoprotein_b", "apob", "total_cholesterol", "hdl_cholesterol"),
        transform="prefer direct ApoB; otherwise compute non-HDL cholesterol",
        proxy_tier="direct_or_proxy_1",
        notes="Field 30640 is the preferred direct ApoB path.",
    ),
    VariableMapping(
        clock_variable="hemodynamic_stress",
        source_dataset="UKB_main_export",
        source_columns=("f.4080.0.0", "f.4080.1.0", "systolic_blood_pressure"),
        transform="average available automated systolic blood pressure readings",
        proxy_tier="direct",
        notes="Field 4080 is the confirmed automated systolic pressure field family.",
    ),
    VariableMapping(
        clock_variable="kidney_function",
        source_dataset="UKB_main_export",
        source_columns=("f.30720.0.0", "cystatin_c"),
        transform="use Cystatin C directly",
        proxy_tier="direct",
        notes="Field 30720 is the preferred direct kidney marker in UKB.",
    ),
    VariableMapping(
        clock_variable="inflammation",
        source_dataset="UKB_main_export",
        source_columns=("f.30710.0.0", "c_reactive_protein", "crp"),
        transform="use CRP directly; log-transform later if needed",
        proxy_tier="direct",
        notes="Field 30710 provides the preferred CRP path.",
    ),
    VariableMapping(
        clock_variable="lung_function",
        source_dataset="UKB_main_export",
        source_columns=("forced_expiratory_volume_in_1_second", "fev1", "forced_vital_capacity", "fvc"),
        transform="prefer FEV1; fall back to FVC-equivalent if needed",
        proxy_tier="direct_or_proxy_1",
        notes="UKB spirometry substantially improves this domain versus the NHANES fallback path.",
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
    "age_at_recruitment": "Field 21022 provides the calibration anchor age in years.",
    "cystatin_c": "Field 30720 is available as a direct kidney-function marker.",
    "visceral_adipose_tissue": "Field 22407 is available in the imaging subset as VAT volume.",
    "systolic_blood_pressure": "Field 4080 is available for automated systolic blood pressure.",
    "waist_circumference": "Field 48 is available for central adiposity.",
    "remaining_fields": "HbA1c, Cystatin C, FEV1, and fitness are available in UK Biobank, but access friction is higher.",
}
