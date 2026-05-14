# Mathematical Calculations

This page documents the calculations implemented in `src/analysis`, `src/calibration`, and `src/core`. Variable names match the code where possible so the equation can be traced directly into the generated code reference.

## Units Used Internally

The loader normalizes raw Agilent G200 sheets to:

- load \(P\) in millinewtons, stored as `Load (mN)`,
- displacement/depth \(h\) in nanometres, stored as `Displacement (nm)`,
- time \(t\) in seconds when available, stored as `Time (sec)`.

Mechanical calculations convert to SI units before reporting:

\[
P_N = P_{\text{mN}}\times 10^{-3}
\]

\[
A_{\text{m}^2} = A_{\text{nm}^2}\times 10^{-18}
\]

\[
S_{\text{N/m}} = S_{\text{mN/nm}}\times 10^6
\]

Hardness and modulus are calculated in pascals and then reported in gigapascals.

## Loading and Unloading Split

For each test, the maximum load index is:

\[
i_{\max} = \operatorname*{arg\,max}_i P_i
\]

The loading segment includes all rows from the beginning through \(i_{\max}\). The unloading segment starts at \(i_{\max}\) and continues to the end of the curve. The maximum values used later are:

\[
P_{\max} = \max(P_i)
\]

\[
h_{\max} = h_{i_{\max}}
\]

`DataProcessor` filters very low loads before the split. The threshold is the larger of a fixed minimum and a fraction of the file maximum:

\[
P_{\text{threshold}} = \max(0.1P_{\max}, 40\ \text{mN})
\]

## Horizontal Segment Detection

`HorizontalSegmentDetector` identifies plateau-like regions by comparing adjacent load changes to an adaptive threshold:

\[
\Delta P_i = |P_{i+1}-P_i|
\]

\[
T = \max(0.02(P_{\max}-P_{\min}),\ 2\sigma_{\Delta P})
\]

Consecutive intervals with \(\Delta P_i < T\) are grouped as horizontal segments when they meet the configured minimum segment length. These segments can be filtered before unloading fits.

## Unloading Curve Models

The main nonlinear fit is the Oliver-Pharr power law:

\[
P(h)=A(h-h_f)^m
\]

where \(A\) is the fitted scale factor, \(h_f\) is the final/residual depth parameter, and \(m\) is the unloading exponent.

The alternative normalized power-law model is:

\[
P(h)=P_{\max}\left(\frac{h-h_f}{h_{\max}-h_f}\right)^m
\]

The implementation bounds \(m\) to a physically reasonable range:

\[
1.1 \le m \le 3.0
\]

## Contact Stiffness

For the Oliver-Pharr model, contact stiffness is the derivative at maximum displacement:

\[
S=\left.\frac{dP}{dh}\right|_{h=h_{\max}}=Am(h_{\max}-h_f)^{m-1}
\]

For the normalized power-law model:

\[
S=\frac{P_{\max}m}{h_{\max}-h_f}
\]

The linear fallback fits the highest-load fraction of the unloading data with:

\[
P = Sh + b
\]

where the slope \(S\) is the fitted stiffness.

## Contact Depth

Contact depth is calculated as:

\[
h_c = h_{\max} - \epsilon\frac{P_{\max}}{S}
\]

The Berkovich/Vickers implementation uses:

\[
\epsilon = 0.75
\]

The standards module also stores geometry-specific exponents and \(\epsilon\) values for flat punch, paraboloid/spherical, conical, Berkovich, and Vickers assumptions.

## Contact Area Function

`AreaFunction.calculate_contact_area` evaluates the calibrated area function:

\[
A(h_c)=C_0h_c^2+C_1h_c+C_2h_c^{1/2}+C_3h_c^{1/4}+C_4h_c^{1/8}
+C_5h_c^{1/16}+C_6h_c^{1/32}+C_7h_c^{1/64}+C_8h_c^{1/128}
\]

For an ideal Berkovich tip:

\[
C_0 = 24.56
\]

and all higher coefficients are zero. Calibrated coefficients account for tip wear, tip rounding, and nonideal geometry.

## Hardness

Hardness is maximum load divided by projected contact area:

\[
H = \frac{P_{\max}}{A_c}
\]

In code, \(P_{\max}\) is converted from mN to N and \(A_c\) from nm\(^2\) to m\(^2\):

\[
H_{\text{Pa}}=\frac{P_{\text{mN}}\times 10^{-3}}{A_{\text{nm}^2}\times 10^{-18}}
\]

\[
H_{\text{GPa}}=H_{\text{Pa}}\times 10^{-9}
\]

## Reduced Modulus

The reduced modulus calculation includes the Berkovich shape correction \(\beta=1.034\):

\[
E_r = \frac{\sqrt{\pi}}{2\beta}\frac{S}{\sqrt{A_c}}
\]

with \(S\) in N/m and \(A_c\) in m\(^2\).

## Sample Elastic Modulus

Reduced modulus combines the sample and indenter elastic compliances:

\[
\frac{1}{E_r}=\frac{1-\nu_s^2}{E_s}+\frac{1-\nu_i^2}{E_i}
\]

Solving for sample modulus:

\[
E_s=\frac{1-\nu_s^2}{\frac{1}{E_r}-\frac{1-\nu_i^2}{E_i}}
\]

The default indenter is diamond:

\[
E_i=1140\ \text{GPa}, \qquad \nu_i=0.07
\]

The sample Poisson ratio is user-configurable and defaults to \(0.3\).

## Tip-Area Calibration

The NIST calibration helper converts reference-material stiffness and known reduced modulus into area:

\[
A = \frac{\pi}{4}\left(\frac{S}{\beta E_r}\right)^2
\]

`calibrate_tip_area_function` then fits a constrained area function with theoretical Berkovich \(C_0\):

\[
A(h_c)=24.56h_c^2+C_1h_c+C_2h_c^{1/2}
\]

The reported coefficient units are converted for display:

\[
C_{0,\text{nm}} = 24.56
\]

\[
C_{1,\text{nm}} = C_{1,\text{SI}}\times 10^9
\]

\[
C_{2,\text{nm}} = \frac{C_{2,\text{SI}}\times 10^9}{\sqrt{10^{-9}}}
\]

The calibration fit is considered preferred quality when \(R^2 > 0.90\), and the documentation/build output reports warnings for lower-quality fits or large fitted correction terms.

## Load-Frame Compliance Calibration

Total compliance is modeled as machine compliance plus sample/contact compliance:

\[
C_{\text{total}} = C_{\text{lf}} + C_{\text{sp}}
\]

\[
C_{\text{total}}=\frac{1}{S}
\]

\[
C_{\text{sp}}=\frac{\sqrt{\pi}}{2E_r}\frac{1}{\sqrt{A}}
\]

Linear regression of \(C_{\text{total}}\) versus \(1/\sqrt{A}\) gives:

\[
C_{\text{total}} = C_{\text{lf}} + k\frac{1}{\sqrt{A}}
\]

The intercept is the load-frame compliance \(C_{\text{lf}}\).

## Continuous Stiffness Measurement

`CSMAnalyzer` can use exported depth-profile hardness/modulus columns directly or recalculate from load, harmonic contact stiffness, and the area function:

\[
H_{\text{CSM}}=\frac{P}{A(h)}
\]

\[
E_{r,\text{CSM}}=\frac{\sqrt{\pi}}{2\beta}\frac{S_{\text{harmonic}}}{\sqrt{A(h)}}
\]

It can average profiles by row index or interpolate each test onto a shared depth grid:

\[
h_j = h_{\text{start}} + j\Delta h
\]

Mean, standard deviation, and count are then reported per depth point.

## Fit Quality

The coefficient of determination is:

\[
R^2 = 1 - \frac{\sum_i(P_i-\hat{P}_i)^2}{\sum_i(P_i-\bar{P})^2}
\]

The nonlinear fit uses the fit-segment \(R^2\) for pass/fail and also reports full-curve \(R^2\) for interpretation.

The default strict fit threshold is:

\[
R^2_{\min}=0.98
\]

## Statistical Summary and Uncertainty

For repeated measurements:

\[
\bar{x}=\frac{1}{n}\sum_{i=1}^{n}x_i
\]

\[
s=\sqrt{\frac{1}{n-1}\sum_{i=1}^{n}(x_i-\bar{x})^2}
\]

\[
\text{CV}=\frac{s}{\bar{x}}\times 100\%
\]

Type A uncertainty is estimated as:

\[
u_A=\frac{s}{\sqrt{n}}
\]

The NIST helper grades precision from the coefficient of variation for modulus and hardness.

## Derived Properties

The mechanical calculator also reports derived quantities when the primary calculations are valid:

\[
\frac{H}{E}=\frac{H}{E_s}
\]

A Tabor-style yield strength estimate is:

\[
\sigma_y \approx \frac{H}{3}
\]

For a Berkovich estimate of contact depth from area:

\[
h_c \approx \sqrt{\frac{A_c}{24.56}}
\]

The approximate indent volume is:

\[
V \approx \frac{A_ch_c}{3}
\]
