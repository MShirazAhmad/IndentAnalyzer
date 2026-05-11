# Core Calculations

This page summarizes the primary formulas implemented in the analysis modules so users can connect reported values to the underlying calculations.

## Hardness

\[
H = \frac{P_{\max}}{A_c}
\]

- \(P_{\max}\): maximum load
- \(A_c\): projected contact area at contact depth

## Reduced Modulus

\[
E_r = \frac{\sqrt{\pi}}{2\beta}\frac{S}{\sqrt{A_c}}
\]

- \(S\): contact stiffness from unloading fit
- \(\beta\): indenter shape factor (Berkovich uses \(\beta = 1.034\))

## Sample Elastic Modulus

\[
\frac{1}{E_r} = \frac{1-\nu_s^2}{E_s} + \frac{1-\nu_i^2}{E_i}
\]

Rearranged for sample modulus:

\[
E_s = \frac{1-\nu_s^2}{\left(\frac{1}{E_r} - \frac{1-\nu_i^2}{E_i}\right)}
\]

## Contact Area Function

General calibrated area function:

\[
A(h_c)=C_0h_c^2+C_1h_c+C_2h_c^{1/2}+C_3h_c^{1/4}+\cdots
\]

Ideal Berkovich reference:

\[
C_0 = 24.56
\]

## Load-Frame Compliance Calibration

Following NIST guidance:

\[
C_{\text{total}} = C_{\text{lf}} + C_{\text{sp}}, \qquad
C_{\text{sp}} = \frac{\sqrt{\pi}}{2E_r}\frac{1}{\sqrt{A}}
\]

Linear regression of \(C_{\text{total}}\) versus \(1/\sqrt{A}\) yields \(C_{\text{lf}}\) as the intercept.

## Fit Quality

\[
R^2 = 1 - \frac{\sum_i (P_i - \hat{P}_i)^2}{\sum_i (P_i - \bar{P})^2}
\]

This metric is used throughout calibration and unloading-fit validation.
