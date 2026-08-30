import logging

from ninja.throttling import AnonRateThrottle, AuthRateThrottle, UserRateThrottle

logger = logging.getLogger(__name__)


class FailOpenMixin:
    """недоступное хранилище счетчиков не должно ронять api"""

    def allow_request(self, request):
        try:
            return super().allow_request(request)
        except Exception:
            logger.exception("Throttle storage unavailable, request allowed")
            return True


class FailClosedMixin:
    def allow_request(self, request):
        try:
            return super().allow_request(request)
        except Exception:
            logger.exception("Security throttle storage unavailable, request denied")
            request._security_throttle_unavailable = True
            return False

    def wait(self):
        try:
            return super().wait()
        except AttributeError:
            return None


# у каждого окна свой scope инстансы с общим scope делят счетчик в кеше,
# и второй уровень лимита считал бы те же запросы


class AnonBurstThrottle(FailOpenMixin, AnonRateThrottle):
    scope = "anon_burst"


class AnonSustainedThrottle(FailOpenMixin, AnonRateThrottle):
    scope = "anon_sustained"


class AuthBurstThrottle(FailOpenMixin, AuthRateThrottle):
    scope = "auth_burst"


class AuthSustainedThrottle(FailOpenMixin, AuthRateThrottle):
    scope = "auth_sustained"


class SecurityAnonBurstThrottle(FailClosedMixin, AnonRateThrottle):
    scope = "security_anon_burst"


class SecurityAnonSustainedThrottle(FailClosedMixin, AnonRateThrottle):
    scope = "security_anon_sustained"


class SecurityAnonResendThrottle(FailClosedMixin, AnonRateThrottle):
    scope = "anon_resend"


class ViewEventBurstThrottle(FailOpenMixin, UserRateThrottle):
    scope = "view_event_burst"


class ViewEventSustainedThrottle(FailOpenMixin, UserRateThrottle):
    scope = "view_event_sustained"


def anon_throttles(burst_rate: str, sustained_rate: str) -> list:
    return [AnonBurstThrottle(burst_rate), AnonSustainedThrottle(sustained_rate)]


def security_anon_throttles(burst_rate: str, sustained_rate: str) -> list:
    return [
        SecurityAnonBurstThrottle(burst_rate),
        SecurityAnonSustainedThrottle(sustained_rate),
    ]


def resend_throttles(rate: str) -> list:
    return [SecurityAnonResendThrottle(rate)]


def view_event_throttles(burst_rate: str, sustained_rate: str) -> list:
    return [ViewEventBurstThrottle(burst_rate), ViewEventSustainedThrottle(sustained_rate)]


def auth_throttles(burst_rate: str, sustained_rate: str) -> list:
    return [AuthBurstThrottle(burst_rate), AuthSustainedThrottle(sustained_rate)]
