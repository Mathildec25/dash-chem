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

# Threads used by the linear algebra libraries. This is not a performance
# setting, it is a reproducibility one: the number of threads decides the order
# in which sums are accumulated, which changes the last digits of the floating
# point results. On a grid where the acquisition is compared across 5670
# candidates, two of them are sometimes within those last digits of each other,
# the ranking flips, and the campaign takes a different path from there on.
#
# Measured, and it corrects an earlier reading: the thread count does NOT change
# the result. One thread and four give identical hypervolume curves and identical
# ligand sequences, and two runs at four threads agree exactly. A campaign that
# came out at 56.0% of the global front and then at 57.6% had in fact crossed the
# change of ACQF_MAX_BATCH_SIZE below, not a change of threads.
#
# It stays pinned anyway, because reproducibility should not rest on an
# environment variable someone might set, and because the pinning has to happen
# before numpy or torch are imported, which is why the scripts call
# pin_numerics() as their first statement. Four threads is twice as fast as one
# on this machine, which matters: a slower campaign spends longer exposed to
# being killed for memory.
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
