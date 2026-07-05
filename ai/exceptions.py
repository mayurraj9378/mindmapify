class ProviderError(Exception):
    """A provider failed for a reason other than quota (bad response, network, etc.)."""


class QuotaExceededError(ProviderError):
    """A provider hit its rate limit / quota. The fallback chain should move on."""


class NotConfiguredError(ProviderError):
    """A provider was called but has no API key configured."""
