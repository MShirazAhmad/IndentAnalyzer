"""
Scientific reference for the IndentAnalyzer calculation pipeline.

This module is intentionally documentation-heavy. It gives researchers and
code reviewers a source-level explanation of the physical model used by
IndentAnalyzer so that the generated ReadTheDocs code reference contains the
same scientific assumptions as the user-facing documentation.

IndentAnalyzer treats instrumented nanoindentation analysis as a traceable
measurement chain:

    vendor workbook
    -> normalized load, displacement, and time columns
    -> preprocessing and loading/unloading separation
    -> unloading-curve fit
    -> contact stiffness S
    -> contact depth h_c
    -> projected contact area A_c
    -> hardness H and reduced modulus E_r
    -> sample elastic modulus E_s
    -> included-test statistics

The main calculation is based on the Oliver-Pharr family of sharp-indenter
methods. The measured unloading curve is fitted using a power law,

    P(h) = A (h - h_f)^m,

where P is load, h is displacement into the surface, A is a fitted scale factor,
h_f is the residual-depth parameter, and m is the unloading exponent. Contact
stiffness is the derivative of this fitted unloading function at maximum depth:

    S = dP/dh |_(h=h_max) = A m (h_max - h_f)^(m - 1).

For Berkovich-style analysis, contact depth is then estimated as

    h_c = h_max - epsilon P_max / S,

with epsilon approximately 0.75. The projected contact area is evaluated from a
calibrated area function,

    A(h_c) = C0 h_c^2 + C1 h_c + C2 h_c^(1/2) + ... + C8 h_c^(1/128).

For an ideal Berkovich tip, C0 = 24.56 and higher-order coefficients are zero.
Real calibrated coefficients account for tip rounding, wear, and nonideal
geometry.

Hardness and modulus are calculated after explicit unit conversion:

    H = P_max / A_c

    E_r = sqrt(pi) S / (2 beta sqrt(A_c))

    1/E_r = (1 - nu_s^2)/E_s + (1 - nu_i^2)/E_i.

Loads are commonly stored in mN, displacements in nm, stiffness in mN/nm, and
area in nm^2. The calculation must convert mN to N, nm^2 to m^2, and mN/nm to
N/m before reporting GPa-scale results.

Scientific assumptions and limitations
--------------------------------------
The method assumes that unloading is predominantly elastic and that the contact
area is represented adequately by the calibrated area function. Results may be
biased by pile-up, sink-in, surface roughness, cracking, porous regions, poor
first contact, thermal drift, time-dependent creep, or indentation on a
nonrepresentative microstructural feature. Numerical fit quality such as R^2 is
therefore necessary but not sufficient for scientific acceptance.

For heterogeneous ceramics, including high-entropy carbides, the final report
should document the calibration source, area-function coefficients, Poisson
ratio, fitting method, number of total and accepted indents, exclusion reasons,
mean, standard deviation, and coefficient of variation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class ScientificEquation:
    """Human-readable description of one equation used in IndentAnalyzer."""

    name: str
    equation: str
    variables: Dict[str, str]
    purpose: str
    trust_note: str


def get_core_equations() -> List[ScientificEquation]:
    """Return the core nanoindentation equations documented by the project.

    The returned objects are not used to perform numerical analysis. They are a
    source-code-level reference for documentation, testing, and reviewer checks.
    Keeping the equations in code makes it easier for `mkdocstrings` and future
    validation scripts to expose the scientific model alongside the implementation.
    """

    return [
        ScientificEquation(
            name="Oliver-Pharr unloading law",
            equation="P(h) = A (h - h_f)^m",
            variables={
                "P": "load during unloading",
                "h": "displacement into the surface",
                "A": "power-law scale factor",
                "h_f": "residual-depth parameter",
                "m": "unloading exponent",
            },
            purpose="Fits the elastic unloading response and provides a differentiable model for stiffness.",
            trust_note="Sensitive to unloading-segment selection, noise, cracking, drift, and plateau artifacts.",
        ),
        ScientificEquation(
            name="Contact stiffness",
            equation="S = A m (h_max - h_f)^(m - 1)",
            variables={
                "S": "contact stiffness",
                "h_max": "maximum displacement",
                "A, h_f, m": "unloading-fit parameters",
            },
            purpose="Converts the fitted unloading curve into stiffness at maximum depth.",
            trust_note="Modulus depends directly on S; unstable fits produce unstable modulus values.",
        ),
        ScientificEquation(
            name="Contact depth",
            equation="h_c = h_max - epsilon P_max / S",
            variables={
                "h_c": "contact depth",
                "epsilon": "geometry correction, approximately 0.75 for Berkovich analysis",
                "P_max": "maximum load",
                "S": "contact stiffness",
            },
            purpose="Estimates the depth of the projected contact area under load.",
            trust_note="Pile-up, sink-in, and poor contact can make this geometric estimate biased.",
        ),
        ScientificEquation(
            name="Tip-area function",
            equation="A_c = C0 h_c^2 + C1 h_c + C2 h_c^(1/2) + ... + C8 h_c^(1/128)",
            variables={
                "A_c": "projected contact area",
                "C0...C8": "area-function coefficients",
                "h_c": "contact depth",
            },
            purpose="Converts contact depth into projected contact area.",
            trust_note="Hardness is directly proportional to 1/A_c, so calibration error strongly affects H.",
        ),
        ScientificEquation(
            name="Hardness",
            equation="H = P_max / A_c",
            variables={"H": "indentation hardness", "P_max": "maximum load", "A_c": "projected contact area"},
            purpose="Reports resistance to indentation under the assumed contact-area model.",
            trust_note="Area uncertainty usually dominates hardness uncertainty.",
        ),
        ScientificEquation(
            name="Reduced modulus",
            equation="E_r = sqrt(pi) S / (2 beta sqrt(A_c))",
            variables={
                "E_r": "reduced modulus",
                "S": "contact stiffness",
                "beta": "indenter shape correction",
                "A_c": "projected contact area",
            },
            purpose="Combines contact stiffness and contact area into the sample-indenter reduced modulus.",
            trust_note="Depends on both unloading-fit quality and area-function accuracy.",
        ),
        ScientificEquation(
            name="Sample modulus",
            equation="E_s = (1 - nu_s^2) / (1/E_r - (1 - nu_i^2)/E_i)",
            variables={
                "E_s": "sample elastic modulus",
                "nu_s": "sample Poisson ratio",
                "E_i": "indenter modulus",
                "nu_i": "indenter Poisson ratio",
                "E_r": "reduced modulus",
            },
            purpose="Back-calculates sample modulus after subtracting indenter compliance.",
            trust_note="Highly sensitive when the compliance denominator approaches zero or nu_s is poorly known.",
        ),
    ]


def get_minimum_reporting_record() -> List[str]:
    """Return the minimum metadata that should accompany published results."""

    return [
        "repository commit or released version",
        "instrument model and vendor export type",
        "source workbook names",
        "calibration workbook and calibration date if available",
        "area-function coefficients or ideal Berkovich assumption",
        "indenter material constants",
        "sample Poisson ratio",
        "fitting method and unloading selection rule",
        "minimum accepted fit quality threshold",
        "number of total, accepted, and excluded indents",
        "reason for each excluded indent",
        "mean, standard deviation, coefficient of variation, and sample count",
    ]


def get_validation_caveats() -> List[str]:
    """Return physical conditions that can invalidate otherwise numerical-looking results."""

    return [
        "pile-up or sink-in changing true contact area",
        "surface roughness or polishing damage",
        "indentation on pores, cracks, or grain boundaries",
        "poor first contact or abnormal zero-point offset",
        "thermal drift or time-dependent creep",
        "pop-in, pop-out, fracture, or discontinuous unloading",
        "wrong column detection or wrong units in the input workbook",
        "calibration performed with too few or unstable reference indents",
    ]
