"""Analytics module for registry computations."""

from . import hashtag_frequency, mention_frequency


def module_registry():
    return {
        "hashtags_frequency": hashtag_frequency.run,
        "mentions_frequency": mention_frequency.run,
    }
