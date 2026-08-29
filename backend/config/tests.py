from unittest.mock import patch

from django.test import RequestFactory, TestCase
from ninja.conf import settings as ninja_settings

from .network import get_client_ip


class ClientIpTest(TestCase):
    """слева в x-forwarded-for стоит то, что прислал клиент, справа - nginx"""

    def setUp(self):
        self.factory = RequestFactory()

    def _request(self, xff: str | None):
        headers = {"HTTP_X_FORWARDED_FOR": xff} if xff is not None else {}
        return self.factory.get("/", REMOTE_ADDR="10.0.0.1", **headers)

    def test_falls_back_to_remote_addr(self):
        self.assertEqual(get_client_ip(self._request(None)), "10.0.0.1")

    def test_spoofed_left_value_is_ignored(self):
        request = self._request("1.2.3.4, 203.0.113.7")
        self.assertEqual(get_client_ip(request), "203.0.113.7")

    def test_single_proxy_hop(self):
        self.assertEqual(get_client_ip(self._request("203.0.113.7")), "203.0.113.7")

    def test_two_trusted_proxies(self):
        # NINJA_NUM_PROXIES читается ninja один раз при импорте,
        # override_settings до него не доходит.
        request = self._request("1.2.3.4, 203.0.113.7, 10.0.0.9")
        with patch.object(ninja_settings, "NUM_PROXIES", 2):
            self.assertEqual(get_client_ip(request), "203.0.113.7")
