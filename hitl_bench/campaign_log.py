"""One JSON file per campaign, written under results/.

Campaign logs are the raw material of the study: never delete them, and never
overwrite one silently. A log is self-contained, so an analysis script only
ever needs the results directory, not the code that produced it.
"""

import json
import os
from datetime import datetime

RESULTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")


def campaign_filename(log):
    """Stable, sortable name built from the campaign's identity."""
    config = log["config"]
    # Windows will not take a colon in a filename, and "fixed:20" has one.
    arm = config["arm"].replace(":", "-")
    name = "%s__%s__seed%02d" % (config["case"], arm, config["seed"])
    fork = log.get("fork")
    if fork and fork.get("draw_seed") is not None:
        name += "__draw%02d" % fork["draw_seed"]
    return name + ".json"


def save_campaign(log, results_dir=RESULTS_DIR, overwrite=False):
    """Write one campaign log and return the path it went to."""
    os.makedirs(results_dir, exist_ok=True)
    path = os.path.join(results_dir, campaign_filename(log))
    if os.path.exists(path) and not overwrite:
        raise FileExistsError(
            "%s already exists; pass overwrite=True to replace it" % path)
    log = dict(log)
    log["written_at"] = datetime.now().isoformat(timespec="seconds")
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(log, handle, indent=2, sort_keys=False)
    return path


def load_campaign(path):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def load_all(results_dir=RESULTS_DIR):
    """Every campaign log in the directory, oldest name first."""
    if not os.path.isdir(results_dir):
        return []
    return [load_campaign(os.path.join(results_dir, name))
            for name in sorted(os.listdir(results_dir)) if name.endswith(".json")]
