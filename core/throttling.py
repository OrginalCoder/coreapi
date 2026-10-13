"""Rate throttling classes for CoreAPI."""

from rest_framework.throttling import AnonRateThrottle


class ChatRateThrottle(AnonRateThrottle):
    """Rate throttle applied to public chat question endpoint."""

    scope = 'chat'
