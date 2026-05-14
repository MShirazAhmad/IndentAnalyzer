# IndentAnalyzer: Open-Source Nanoindentation Analysis Software

**A Python-based GUI and analysis framework for indentation data processing, Oliver–Pharr mechanical property extraction, CSM analysis, calibration, visualization, and reproducible scientific reporting.**

---

## Abstract

IndentAnalyzer is an open-source Python software package for analyzing instrumented nanoindentation data. It is designed mainly for Agilent Nano Indenter G200 `.xls` and `.xlsx` files, but its structure can be extended to other instruments if their data are converted into the required format.

The software provides a graphical user interface that helps the user load indentation files, inspect load–displacement curves, analyze individual tests, exclude poor-quality indents, process continuous stiffness measurement (CSM) data, apply calibration-related corrections, generate plots, and export tables for reports, theses, papers, and supplementary data.

The mechanical-property calculations follow the Oliver–Pharr method, which is widely used in instrumented indentation. In this method, the maximum load, unloading stiffness, contact depth, and projected contact area are used to calculate hardness, reduced modulus, and sample elastic modulus. The software also uses terminology and analysis concepts from ISO 14577, the international standard for instrumented indentation testing. However, the software itself should be understood as **ISO 14577-aligned**, not ISO-certified. Formal ISO compliance depends on the actual instrument, calibration procedure, reference materials, test conditions, and laboratory reporting protocol.

This document explains how IndentAnalyzer works, what scientific equations it uses, how the code is organized, and what limitations should be considered when interpreting nanoindentation results.

**Keywords:** nanoindentation; instrumented indentation; Oliver–Pharr method; ISO 14577; Berkovich indenter; hardness; reduced modulus; elastic modulus; CSM; Python; PyQt5; materials characterization.

---

## 1. Purpose of the software

IndentAnalyzer is intended for researchers who already have nanoindentation data and want a transparent method for calculating mechanical properties. It is especially useful for materials scientists working with ceramics, coatings, metals, high-entropy carbides, thin films, porous samples, and other advanced materials.

The main purpose of the software is to answer the following question:

> From the measured nanoindentation load–displacement data, what are the hardness and elastic modulus values obtained using an Oliver–Pharr-style analysis?

The software also helps answer related questions:

- Which indentation curves are reliable?
- Which tests should be excluded because of poor curve quality or abnormal results?
- How do hardness and modulus change with depth in CSM data?
- How do calibration settings and contact area assumptions affect the final values?
- How can the results be exported in a reproducible form?

The software improves transparency and consistency in nanoindentation analysis, but it does not replace scientific judgment. The user must still decide whether the indentation data are physically meaningful for the material being studied.

---

## 2. Scientific basis

Nanoindentation measures the response of a material as a sharp indenter is pressed into the surface and then unloaded. The instrument records load \(P\) and displacement \(h\). From this curve, the software extracts mechanical properties.

The analysis is based mainly on the Oliver–Pharr method [1,3]. This method uses the unloading part of the indentation curve to calculate contact stiffness. Contact stiffness is then used to calculate the reduced modulus. Hardness is calculated from the maximum load divided by the projected contact area.

The main quantities used in the analysis are:

| Symbol | Meaning |
|---|---|
| \(P\) | Applied indentation load |
| \(h\) | Indentation displacement |
| \(P_\mathrm{max}\) | Maximum load |
| \(h_\mathrm{max}\) | Maximum displacement |
| \(S\) | Contact stiffness |
| \(h_c\) | Contact depth |
| \(A_c\) | Projected contact area |
| \(H\) | Hardness |
| \(E_r\) | Reduced modulus |
| \(E_s\) | Sample elastic modulus |

The analysis follows the general framework used in ISO 14577 for instrumented indentation testing [4–7]. ISO 14577-1 describes the general test method. ISO 14577-2 describes machine verification and calibration. ISO 14577-3 describes reference-block calibration. ISO 14577-4 describes indentation testing of coatings.

IndentAnalyzer implements selected equations and data-processing steps from this framework. It does not certify the instrument or the experiment.

---

## 3. What the software does

IndentAnalyzer performs the following main tasks:

1. Loads Agilent G200 nanoindentation spreadsheet files.
2. Detects individual test sheets inside the workbook.
3. Extracts time, load, and displacement data.
4. Cleans the raw data.
5. Splits each curve into loading and unloading segments.
6. Fits the unloading curve using an Oliver–Pharr-style model.
7. Calculates contact stiffness.
8. Calculates contact depth.
9. Calculates projected contact area.
10. Calculates hardness.
11. Calculates reduced modulus.
12. Calculates sample elastic modulus using the selected Poisson ratio.
13. Processes CSM depth-profile data.
14. Allows the user to exclude poor-quality tests.
15. Generates plots and summary statistics.
16. Exports results for reporting.

The software is therefore both a calculation tool and a review tool. It does not simply produce one number; it helps the user inspect the data before deciding which values should be reported.

---

## 4. General workflow

The analysis workflow can be understood as a sequence of scientific steps:

```text
Raw nanoindentation file
        ↓
Read test sheets
        ↓
Extract load and displacement data
        ↓
Clean and organize the data
        ↓
Find maximum load and maximum depth
        ↓
Separate loading and unloading parts
        ↓
Fit the unloading curve
        ↓
Calculate contact stiffness
        ↓
Calculate contact depth
        ↓
Calculate contact area
        ↓
Calculate hardness and modulus
        ↓
Review curves and exclude bad tests
        ↓
Export final results
```

This workflow is designed to make the analysis reproducible. A researcher can inspect how each result was obtained instead of relying only on final values exported by the instrument software.

---

## 5. Input data

Each indentation test must contain load and displacement information. The preferred internal format uses the following column names:

| Column | Unit | Meaning |
|---|---|---|
| Time (sec) | s | Time during the indentation test |
| Load (mN) | mN | Applied load |
| Displacement (nm) | nm | Indenter displacement into the sample |

For Agilent G200 files, the software tries to detect these columns automatically. If no time column is found, the loader may create a simple synthetic time sequence so the test can still be processed.

The most important columns for Oliver–Pharr analysis are load and displacement.

---

## 6. Unit conversions

Nanoindentation files commonly store load in millinewtons and displacement in nanometers. The software converts these values into SI units where needed.

Load conversion:

$$
P_\mathrm{N}=P_\mathrm{mN}\times10^{-3}
$$

Area conversion:

$$
A_\mathrm{m^2}=A_\mathrm{nm^2}\times10^{-18}
$$

Stiffness conversion:

$$
S_\mathrm{N/m}=S_\mathrm{mN/nm}\times10^{6}
$$

Final hardness and modulus values are reported in gigapascals:

$$
X_\mathrm{GPa}=X_\mathrm{Pa}\times10^{-9}
$$

For CSM data, the harmonic contact stiffness column is usually already reported in N/m. In that case, the software does not apply the mN/nm to N/m conversion.

---

## 7. Main equations used by the software

### 7.1 Maximum load and maximum depth

The software first finds the point where the load is maximum:

$$
P_\mathrm{max}=\max(P_i)
$$

The displacement at this point is:

$$
h_\mathrm{max}=h(P_\mathrm{max})
$$

This point is important because the unloading portion of the curve begins near maximum load. The unloading curve is used to estimate contact stiffness.

Code location: `src/core/data_processor.py`

---

### 7.2 Oliver–Pharr unloading curve

The unloading curve is fitted using the power-law relation:

$$
P(h)=A(h-h_f)^m
$$

where \(A\), \(h_f\), and \(m\) are fitting parameters.

Here, \(h_f\) is related to the final depth after unloading, and \(m\) describes the shape of the unloading curve. This equation is part of the Oliver–Pharr method [1,3].

Code location: `src/analysis/curve_fitting.py`

---

### 7.3 Contact stiffness

Contact stiffness is the slope of the unloading curve at maximum depth:

$$
S=\left.\frac{dP}{dh}\right|_{h=h_\mathrm{max}}
$$

For the fitted unloading equation, this becomes:

$$
S=Am(h_\mathrm{max}-h_f)^{m-1}
$$

Contact stiffness is one of the most important quantities in nanoindentation because it connects the unloading curve to the elastic modulus [2].

Code location: `src/analysis/curve_fitting.py`

---

### 7.4 Contact depth

The contact depth is calculated as:

$$
h_c=h_\mathrm{max}-\epsilon\frac{P_\mathrm{max}}{S}
$$

For Berkovich-type indentation, the software uses:

$$
\epsilon=0.75
$$

Contact depth is not the same as maximum displacement. It estimates the depth of actual contact between the indenter and the sample.

Code location: `src/analysis/curve_fitting.py`

---

### 7.5 Projected contact area

The projected contact area is calculated from the contact depth. The general area function is:

$$
A_c(h_c)=C_0h_c^2+C_1h_c+C_2h_c^{1/2}+C_3h_c^{1/4}+C_4h_c^{1/8}+\cdots
$$

For an ideal Berkovich indenter:

$$
A_c=24.56h_c^2
$$

The contact area function is very important. At shallow indentation depths, the real indenter tip is not perfectly sharp, so the ideal Berkovich area function may not be accurate. This is why calibration using a reference material such as fused silica is important [1,3,4].

Code location: `src/analysis/curve_fitting.py`

---

### 7.6 Hardness

Hardness is calculated as:

$$
H=\frac{P_\mathrm{max}}{A_c}
$$

In practical code units:

$$
H_\mathrm{Pa}=\frac{P_\mathrm{mN}\times10^{-3}}{A_{c,\mathrm{nm^2}}\times10^{-18}}
$$

$$
H_\mathrm{GPa}=H_\mathrm{Pa}\times10^{-9}
$$

This means that hardness is the maximum applied load divided by the projected contact area.

Code location: `src/analysis/mechanical_calculator.py`

---

### 7.7 Reduced modulus

Reduced modulus is calculated using:

$$
E_r=\frac{\sqrt{\pi}}{2\beta}\frac{S}{\sqrt{A_c}}
$$

The software uses the Berkovich correction factor:

$$
\beta=1.034
$$

The reduced modulus includes the elastic response of both the sample and the diamond indenter [2,3,8,9].

Code location: `src/analysis/mechanical_calculator.py`

---

### 7.8 Sample elastic modulus

The sample modulus is calculated from the reduced modulus using:

$$
\frac{1}{E_r}=\frac{1-\nu_s^2}{E_s}+\frac{1-\nu_i^2}{E_i}
$$

Solving for the sample modulus:

$$
E_s=\frac{1-\nu_s^2}{\frac{1}{E_r}-\frac{1-\nu_i^2}{E_i}}
$$

For the diamond indenter, the software uses:

$$
E_i=1140\ \mathrm{GPa}
$$

$$
\nu_i=0.07
$$

The sample Poisson ratio (\(\nu_s\)) is selected by the user. The default value is:

$$
\nu_s=0.30
$$

The selected Poisson ratio must be reported because it affects the final sample modulus.

Code location: `src/analysis/mechanical_calculator.py`

---

### 7.9 CSM hardness and modulus

For continuous stiffness measurement data, the software can calculate hardness and modulus as a function of indentation depth:

$$
H(h)=\frac{P(h)}{A_c(h)}
$$

$$
E_r(h)=\frac{\sqrt{\pi}}{2\beta}\frac{S(h)}{\sqrt{A_c(h)}}
$$

This allows the user to generate depth-dependent hardness and modulus profiles.

CSM results at very shallow depths should be interpreted carefully because they are sensitive to surface detection, oscillation amplitude, tip shape, and noise [10,11].

Code location: `src/analysis/csm_analyzer.py`

---

### 7.10 Load-frame compliance calibration

The calibration helper uses the relationship:

$$
C_\mathrm{total}=C_\mathrm{lf}+C_\mathrm{sp}
$$

where:

$$
C_\mathrm{total}=\frac{1}{S}
$$

and:

$$
C_\mathrm{sp}=\frac{\sqrt{\pi}}{2E_r}\frac{1}{\sqrt{A_c}}
$$

The intercept of a compliance plot is used to estimate load-frame compliance.

This calculation helps with calibration analysis, but it does not replace formal instrument verification under ISO 14577-2 or reference-block calibration under ISO 14577-3 [5,6].

Code location: `src/calibration/nist_methods.py`

---

### 7.11 Tip area calibration

The contact area can also be estimated from stiffness and known reference modulus:

$$
A_c=\frac{\pi}{4}\left(\frac{S}{\beta E_r}\right)^2
$$

The current calibration helper fits a simplified area function:

$$
A_c(h_c)=24.56h_c^2+C_1h_c+C_2h_c^{1/2}
$$

This helps estimate tip-shape corrections from reference-material data.

Code location: `src/calibration/nist_methods.py`

---

### 7.12 Statistical summaries

For a group of accepted tests, the software calculates the mean:

$$
\bar{x}=\frac{1}{n}\sum_{i=1}^{n}x_i
$$

the standard deviation:

$$
s=\sqrt{\frac{1}{n-1}\sum_{i=1}^{n}(x_i-\bar{x})^2}
$$

and the coefficient of variation:

$$
\mathrm{CV}=\frac{s}{\bar{x}}\times100\%
$$

The software can also flag statistical outliers using the interquartile range:

$$
\mathrm{IQR}=Q_3-Q_1
$$

$$
x < Q_1 - 1.5\,\mathrm{IQR} \quad \text{or} \quad x > Q_3 + 1.5\,\mathrm{IQR}
$$

These summaries help the user report central tendency, data spread, and possible outliers in a transparent way. Outlier flags should be reviewed alongside curve shape and experimental notes before final exclusion.

Code location: `src/analysis/statistics.py`

---

## 8. Limitations and good scientific practice

IndentAnalyzer is designed to make nanoindentation analysis transparent and reproducible, but several limitations remain:

- Results are only as reliable as the input data quality.
- Surface roughness, drift, tip wear, and poor contact detection can strongly affect shallow-depth results.
- CSM profiles at low depth are sensitive to harmonic settings and noise.
- The chosen sample Poisson ratio directly changes calculated sample modulus.
- Curve fitting quality metrics (such as \(R^2\)) should not be used alone to accept a test.

For publication-quality reporting, users should describe calibration status, exclusion criteria, fitting method, area-function assumptions, and uncertainty metrics.

---

## 9. Reproducibility and reporting recommendations

To support reproducible materials research, final reports should include:

1. Instrument model and indenter type.
2. Reference material(s) used for calibration.
3. Loading protocol and maximum load or depth.
4. Fitting model used for unloading analysis.
5. Area-function form and coefficients.
6. Sample Poisson ratio used for modulus conversion.
7. Number of accepted and excluded tests, with criteria.
8. Mean, standard deviation, and coefficient of variation for reported properties.

These reporting items help readers evaluate whether measured hardness and modulus trends are physically meaningful and comparable across studies.

---

## References

[1] W. C. Oliver and G. M. Pharr, “An improved technique for determining hardness and elastic modulus using load and displacement sensing indentation experiments,” *Journal of Materials Research*, 7(6), 1564–1583 (1992).  
[2] I. N. Sneddon, “The relation between load and penetration in the axisymmetric Boussinesq problem for a punch of arbitrary profile,” *International Journal of Engineering Science*, 3(1), 47–57 (1965).  
[3] W. C. Oliver and G. M. Pharr, “Measurement of hardness and elastic modulus by instrumented indentation: Advances in understanding and refinements to methodology,” *Journal of Materials Research*, 19(1), 3–20 (2004).  
[4] ISO 14577-1, *Metallic materials — Instrumented indentation test for hardness and materials parameters — Part 1: Test method* (International Organization for Standardization, Geneva).  
[5] ISO 14577-2, *Metallic materials — Instrumented indentation test for hardness and materials parameters — Part 2: Verification and calibration of testing machines* (International Organization for Standardization, Geneva).  
[6] ISO 14577-3, *Metallic materials — Instrumented indentation test for hardness and materials parameters — Part 3: Calibration of reference blocks* (International Organization for Standardization, Geneva).  
[7] ISO 14577-4, *Metallic materials — Instrumented indentation test for hardness and materials parameters — Part 4: Test method for metallic and non-metallic coatings* (International Organization for Standardization, Geneva).  
[8] A. C. Fischer-Cripps, *Nanoindentation*, 3rd ed., Springer, New York (2011).  
[9] R. B. King, “Elastic analysis of some punch problems for a layered medium,” *International Journal of Solids and Structures*, 23(12), 1657–1664 (1987).  
[10] J. Hay and B. Crawford, “Measuring substrate-independent modulus of thin films,” *Journal of Materials Research*, 26(6), 727–738 (2011).  
[11] W. D. Nix and H. Gao, “Indentation size effects in crystalline materials: A law for strain gradient plasticity,” *Journal of the Mechanics and Physics of Solids*, 46(3), 411–425 (1998).
