"""Runtime settings that change how much memory a campaign needs, not what it does.

BoFire hands the whole candidate set to BoTorch's `optimize_acqf_discrete`,
which scores it in batches of 2048 by default. On this benchmark that is 5670
candidates against a qLogNEHVI built on 512 Monte Carlo samples, and the
transient tensors peak around 1.5 GB. Small batches cost nothing: the function
simply concatenates the scores of each batch, so the result is the same numbers
in the same order.

Measured on case ii, one acquisition step over 30 experiments:

    max_batch_size   peak memory   time     candidate
    2048 (default)      1484 MB    11.2 s   L4, 300 s, 110 C, 1.75 mol%
     512                 700 MB    11.2 s   identical
     128                 520 MB    11.1 s   identical

This is worth doing because the memory, not the number of cores, is what limits
how many campaigns can run at once, and because a campaign that gets killed
halfway is worse than one that runs slightly differently. Note that this is a
batching detail, unlike lowering the acquisition function's `n_mc_samples`,
which would change the algorithm and no longer match a real REACTO campaign.
"""

import functools

# Candidates scored per batch. 128 keeps a campaign comfortably under a gigabyte
# with no measurable time cost. It is part of the reproducibility contract, not
# only a memory setting: a single acquisition step gives the same candidate at
# 2048, 512 and 128, but over thirty chained steps a difference in the last
# digits is enough to send a campaign down another path. Change it and the saved
# campaigns no longer reproduce.
ACQF_MAX_BATCH_SIZE = 128

# Threads used by the linear algebra libraries.
#
# Pinned so that a result never depends on an environment variable someone
# happens to have set. The pinning has to happen before numpy or torch are
# imported, which is why the scripts call pin_numerics() as their first
# statement. Four threads runs twice as fast as one on this machine, and speed
# matters beyond comfort: a campaign that takes twice as long spends twice as
# long exposed to being killed for memory.
#
# CORRECTION, 10 September. This block previously claimed that campaigns
# reproduce and that the thread count was measured not to matter. The first half
# was simply false and the measurement behind the second half did not test what
# it claimed. Campaigns were **not** reproducible at all, for a reason that has
# nothing to do with threads: REACTO built its BoFire strategy without a seed,
# and BoFire then draws one itself with `np.random.SeedSequence()`, whose
# entropy comes from the operating system. Neither torch.manual_seed nor
# np.random.seed reaches it, so a fresh seed was drawn at every one of the
# thirty acquisition steps of every campaign, the quasi-Monte-Carlo samples
# differed between two identical runs, and wherever two candidates scored
# closely the argmax flipped and the campaigns parted ways.
#
# Fixed by passing an explicit seed: bayesian_optimization now takes `seed=`,
# and campaign.py derives it from the campaign seed and the iteration index.
# Verified on the arylation: two identical runs agree on all 40 experiments and
# to twelve decimals on the area under the curve, and a fork with no
# intervention reproduces its parent exactly - which is the condition the paired
# design rests on. Campaigns logged before that fix cannot be replayed; they
# remain valid as independent samples for failure rates and firing times, but
# they cannot serve as the control arm of a pair.
NUM_THREADS = 4
_THREAD_VARIABLES = (
    "OMP_NUM_THREADS", "MKL_NUM_THREADS",
    "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS",
)

_applied = False


def pin_numerics(num_threads=NUM_THREADS):
    """Fix the thread count so campaigns reproduce across launches.

    Call this before importing numpy, torch or anything that pulls them in.
    Returns the value it set, which callers record in their logs so that a
    result can always be traced back to the numerical setting that produced it.
    """
    import os

    for variable in _THREAD_VARIABLES:
        os.environ[variable] = str(num_threads)
    return num_threads


def pin_torch_threads(num_threads=NUM_THREADS):
    """The torch-side half of pin_numerics, once torch can be imported."""
    import torch

    torch.set_num_threads(num_threads)
    return num_threads


def limit_acquisition_memory(max_batch_size=ACQF_MAX_BATCH_SIZE):
    """Cap how many candidates the acquisition function scores at once.

    Idempotent, and safe to call from anywhere before a campaign starts.
    Returns True the first time it does something, False afterwards.
    """
    global _applied
    if _applied:
        return False

    import botorch.optim.optimize as botorch_optimize
    import bofire.strategies.predictives.acqf_optimization as bofire_acqf

    bofire_acqf.optimize_acqf_discrete = functools.partial(
        botorch_optimize.optimize_acqf_discrete, max_batch_size=max_batch_size,
    )
    _applied = True
    return True
