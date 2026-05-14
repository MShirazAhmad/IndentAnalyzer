# GUI Walkthrough

This walkthrough is the primary guide for material scientists using nanoindentation data in the IndentAnalyzer GUI.

## Before you begin

Prepare:

- a fused-silica reference file (if calibration must be generated),
- an unknown sample file (`.xls`/`.xlsx`),
- target fitting choices (usually Oliver-Pharr first),
- expected physical ranges for your material class.

## Standard workflow overview

The left workflow tabs are:

1. `1. Calibration`
2. `2. Load File`
3. `3. Settings`
4. `4. Results`
5. `5. Export`

Additional tabs: `Expert Mode`, `Log`.

---

## Step 1 — Define calibration strategy (`1. Calibration`)

Decide whether you will load saved area-function coefficients, generate from fused silica, or enter coefficients manually.

![Calibration start: choose coefficient source before sample analysis](screenshots/figure_01_step1_calibration_start.png){ width="900" }

Scientific intent: a valid area function is required before hardness/modulus from unknown samples can be trusted.

## Step 2 — Generate calibration from fused silica (if needed)

If no approved coefficient set exists, generate a calibration profile from reference data.

![Calibration generation dialog: selecting fused-silica reference data](screenshots/figure_02_step1_generate_silica_file_dialog.png){ width="900" }

Reference assumptions commonly used:

\[
E_s = 72\,\text{GPa}, \quad \nu_s = 0.17
\]

## Step 3 — Confirm calibration profile

After generation, review the produced calibration profile before analyzing unknown sample files.

![Calibration profile generated: verify coefficients before proceeding](screenshots/figure_03_step1_calibration_profile_generated.png){ width="900" }

## Step 4 — Check calibration quality metrics

Use `Calibration Metrics` to confirm fit quality and identify warnings.

![Calibration metrics: assess fit quality and warning signals](screenshots/figure_04_step1_calibration_metrics.png){ width="900" }

Do not proceed with poor calibration quality unless you document the limitation.

## Step 5 — Load unknown sample file (`2. Load File`)

Load the experiment file and verify that test sheets are recognized.

![Load file step: validate data ingestion and curve availability](screenshots/figure_05_step2_load_file_curve_viewer.png){ width="900" }

## Step 6 — Configure analysis settings (`3. Settings`)

Set the fitting model and acceptance thresholds (for example minimum \(R^2\), fitting fraction, sample Poisson ratio).

![Settings step: configure Oliver-Pharr and quality thresholds](screenshots/figure_09_step3_oliver_pharr_settings.png){ width="900" }

## Step 7 — Sanity-check curves before run

Inspect representative curves before running full summary statistics.

![Curve review after settings: verify unloading behavior before accepting fits](screenshots/figure_10_step3_curve_viewer_after_settings.png){ width="900" }

## Step 8 — Run analysis and review summary (`4. Results`)

Run analysis, then inspect readiness/summary outputs.

![Results summary: verify accepted-test counts and distribution behavior](screenshots/figure_12_step4_results_ready_summary.png){ width="900" }

Useful equations during interpretation:

\[
h_c = h_{\max} - \epsilon\frac{P_{\max}}{S}, \quad \epsilon \approx 0.75
\]

\[
H = \frac{P_{\max}}{A_c}, \qquad E_r = \frac{\sqrt{\pi}}{2\beta}\frac{S}{\sqrt{A_c}}
\]

## Step 9 — Reliability and exclusion decisions

Use `Reliability` and `Curve Viewer` together. Exclude tests only when there is clear scientific justification (artifacts, unstable contact, poor unloading behavior, outlier behavior not explained by structure).

Document exclusion rationale for traceability.

## Step 10 — Export/reporting (`5. Export`)

Export per-test and summary outputs only after final inclusion/exclusion decisions are locked.

Recommended reporting package:

- calibration source and date,
- fitting method and thresholds,
- accepted vs excluded test counts,
- mean ± spread for hardness and modulus,
- representative curves from included and excluded groups.

---

## CSM workflow (when depth profiles are needed)

Use these when analyzing CSM datasets rather than only single-point endpoints.

![CSM setup selected in Settings](screenshots/figure_13_step3_csm_setup_selected.png){ width="900" }
![CSM reliability run context](screenshots/figure_18_step3_csm_run_reliability.png){ width="900" }
![CSM depth profiles](screenshots/figure_15_step4_csm_depth_profiles.png){ width="900" }
![CSM depth profiles after updates](screenshots/figure_19_step4_csm_depth_profiles_updated.png){ width="900" }
![CSM averaged data](screenshots/figure_16_step4_csm_averaged_data.png){ width="900" }
![CSM table review](screenshots/figure_20_step4_csm_table_review.png){ width="900" }
![CSM table and log context](screenshots/figure_21_step4_csm_table_log_context.png){ width="900" }

## Expert Mode (advanced diagnostics)

Use Expert Mode for custom plotting and deeper diagnostics, not as a replacement for the standard 5-step QA workflow.

![Expert Mode multi-test plotting](screenshots/figure_22_expert_mode_multitest_plot.png){ width="900" }
![Expert Mode h0-offset controls](screenshots/figure_23_expert_mode_h0_offsets.png){ width="900" }
![Expert Mode single-test diagnostics](screenshots/figure_24_expert_mode_single_test_plot.png){ width="900" }
![Expert Mode log and single-test context](screenshots/figure_25_expert_mode_log_and_single_test.png){ width="900" }

## Related pages

- [Mathematical Calculations](calculations.md)
- [Analysis Configuration](analysis-configuration.md)
- [Features](features.md)

