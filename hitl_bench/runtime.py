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

# Candidates scored per batch. 128 keeps a campaign comfortably under a
# gigabyte with no measurable time cost.
ACQF_MAX_BATCH_SIZE = 128

_applied = False


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
