"""
Sampling configuration callbacks
NOTE: The actual domain creation with sampling is now handled by consolidated_callbacks.py
This file can be used for additional sampling-related UI updates if needed
"""

import dash
from dash import callback, Input, Output, State
from dash.exceptions import PreventUpdate

# Domain creation is now handled in consolidated_callbacks.py
# This avoids callback conflicts and ensures proper data flow

# You can add additional callbacks here for sampling UI updates if needed
# For example, validating sampling parameters or showing previews