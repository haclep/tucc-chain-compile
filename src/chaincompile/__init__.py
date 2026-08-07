"""chaincompile -- compile-from-target chain selector for factorized UCC.

Standalone validation prototype for the tucc chain-selection design
(SD-routed Givens elimination + numeric CC-translation diagnostics).
"""
from .dets import Substitution, substitution_between, bits
from .sector import SectorBasis
from .hubbard import hamiltonian, fermi_sea_mask, eps
from .factors import apply_ucc_factor, apply_cc_triple
from .compile import compile_chain, prepare_state, CompileResult, LedgerRow
from .translate import (
    cluster_analysis,
    build_T,
    sd_truncation_report,
    export_amps_json,
    exp_apply,
)

__version__ = "0.1.0"

__all__ = [
    "Substitution",
    "substitution_between",
    "bits",
    "SectorBasis",
    "hamiltonian",
    "fermi_sea_mask",
    "eps",
    "apply_ucc_factor",
    "apply_cc_triple",
    "compile_chain",
    "prepare_state",
    "CompileResult",
    "LedgerRow",
    "cluster_analysis",
    "build_T",
    "sd_truncation_report",
    "export_amps_json",
    "exp_apply",
    "__version__",
]
