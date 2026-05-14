# Mathematical Calculations

This page summarizes the core equations used by IndentAnalyzer and how to interpret outputs for reporting.

## Internal units and SI conversion

Loader-normalized columns:

- \(P\): `Load (mN)`
- \(h\): `Displacement (nm)`
- \(t\): `Time (sec)`

Conversions used in mechanical calculations:

\[
P_N = P_{\mathrm{mN}}\times 10^{-3}
\]

\[
A_{\mathrm{m}^2} = A_{\mathrm{nm}^2}\times 10^{-18}
\]

\[
S_{\mathrm{N/m}} = S_{\mathrm{mN/nm}}\times 10^6
\]

## Curve segmentation

Maximum load index:

\[
i_{\max} = \operatorname*{arg\,max}_i P_i
\]

Then:

- loading segment: start to \(i_{\max}\)
- unloading segment: \(i_{\max}\) to end

Low-load filtering uses:

\[
P_{\text{threshold}} = \max(0.1P_{\max}, 40\ \text{mN})
\]

## Unloading models

Oliver-Pharr:

\[
P(h)=A(h-h_f)^m
\]

Normalized power law:

\[
P(h)=P_{\max}\left(\frac{h-h_f}{h_{\max}-h_f}\right)^m
\]

with bounded exponent:

\[
1.1 \le m \le 3.0
\]

## Contact stiffness and contact depth

Oliver-Pharr stiffness at \(h_{\max}\):

\[
S=Am(h_{\max}-h_f)^{m-1}
\]

Contact depth:

\[
h_c = h_{\max} - \epsilon\frac{P_{\max}}{S}, \quad \epsilon=0.75\ \text{(Berkovich/Vickers path)}
\]

## Contact area function

\[
A(h_c)=C_0h_c^2+C_1h_c+C_2h_c^{1/2}+C_3h_c^{1/4}+C_4h_c^{1/8}+C_5h_c^{1/16}+C_6h_c^{1/32}+C_7h_c^{1/64}+C_8h_c^{1/128}
\]

Ideal Berkovich reference:

\[
C_0 = 24.56
\]

Higher-order coefficients represent non-ideal tip geometry and wear effects.

## Hardness and modulus

Hardness:

\[
H = \frac{P_{\max}}{A_c}
\]

Reduced modulus:

\[
E_r = \frac{\sqrt{\pi}}{2\beta}\frac{S}{\sqrt{A_c}}, \quad \beta = 1.034
\]

Sample modulus from compliance relation:

\[
\frac{1}{E_r}=\frac{1-\nu_s^2}{E_s}+\frac{1-\nu_i^2}{E_i}
\]

\[
E_s=\frac{1-\nu_s^2}{\frac{1}{E_r}-\frac{1-\nu_i^2}{E_i}}
\]

Default indenter constants (diamond):

\[
E_i=1140\ \text{GPa}, \quad \nu_i=0.07
\]

## Calibration formulas

Tip-area reference conversion:

\[
A = \frac{\pi}{4}\left(\frac{S}{\beta E_r}\right)^2
\]

Load-frame compliance regression form:

\[
C_{\text{total}} = C_{\text{lf}} + k\frac{1}{\sqrt{A}}, \qquad C_{\text{total}}=\frac{1}{S}
\]

## Interpretation guidance for material scientists

- Do not accept/reject based on \(R^2\) alone; pair metrics with curve-shape review.
- Large changes after exclusion usually indicate heterogeneous response or poor test quality; report inclusion criteria.
- If calibrated coefficients change substantially between sessions, verify reference-file quality and instrument stability before comparing sample trends.

## Related pages

- [GUI Walkthrough](gui-walkthrough.md)
- [Analysis Configuration](analysis-configuration.md)
- [Features](features.md)

