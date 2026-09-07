"""hitl-bench: human-in-the-loop benchmarking for multi-objective reaction optimisation.

The optimiser is REACTO's own, imported from utils.bofire_optimization, so the
in-silico study and a real campaign go through the same code path. Run scripts
from the dash-chem directory so that `utils` is importable.
"""

__all__ = ["benchmark", "campaign", "campaign_log", "metrics"]
