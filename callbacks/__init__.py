"""Callback modules (imported for their @callback side-effects)."""

from . import opti_param_callbacks, opti_run_callbacks
from .opti_results_callbacks import generate_report  # noqa: F401

__all__ = ["opti_param_callbacks", "opti_run_callbacks"]
