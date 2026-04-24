"""Page layout factories."""

from .layout_about import create_about_layout
from .layout_opti_home import create_opti_home_layout
from .layout_opti_param import create_opti_param_layout
from .layout_opti_run import create_opti_run_layout
from .layout_tutorial import create_tutorial_layout

__all__ = [
    "create_about_layout",
    "create_opti_home_layout",
    "create_opti_param_layout",
    "create_opti_run_layout",
    "create_tutorial_layout",
]
