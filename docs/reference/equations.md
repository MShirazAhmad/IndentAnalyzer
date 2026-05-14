# Equations and analysis reference

## Tip-area function

$$
A_c=A(h_c)=C_0h_c^2+C_1h_c+C_2h_c^{1/2}+C_3h_c^{1/4}+\cdots
$$

## Oliver–Pharr unloading fit

$$
P=\alpha(h-h_f)^m
$$

## Contact stiffness

$$
S=\left.\frac{dP}{dh}\right|_{h=h_{max}}
$$

## Contact depth

$$
h_c=h_{max}-\varepsilon\frac{P_{max}}{S}
$$

## Hardness

$$
H=\frac{P_{max}}{A_c}
$$

## Reduced modulus

$$
E_r=\frac{\sqrt{\pi}}{2}\frac{S}{\sqrt{A_c}}
$$

## Sample modulus

$$
E_s=\frac{1-\nu_s^2}{\frac{1}{E_r}-\frac{1-\nu_i^2}{E_i}}
$$

## Fit quality

$$
R^2=1-\frac{\sum_i(P_i-\hat{P}_i)^2}{\sum_i(P_i-\bar{P})^2}
$$

## Reliability statistics

Mean:

$$
\bar{x}=\frac{1}{n}\sum_{i=1}^{n}x_i
$$

Sample standard deviation:

$$
s=\sqrt{\frac{1}{n-1}\sum_{i=1}^{n}(x_i-\bar{x})^2}
$$

Coefficient of variation:

$$
CV(\%)=\frac{s}{\bar{x}}\times100
$$

## Reference constants used in the active codebase

The active standards and defaults are defined in `/home/runner/work/IndentAnalyzer/IndentAnalyzer/src/core/standards.py`, including:

- fused silica modulus = `72e9` Pa,
- fused silica Poisson ratio = `0.17`,
- diamond indenter modulus = `1140e9` Pa,
- diamond indenter Poisson ratio = `0.07`,
- perfect Berkovich `C0 = 24.56`.
