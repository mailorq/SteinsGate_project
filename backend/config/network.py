from ninja.conf import settings as ninja_settings


def get_client_ip(request) -> str | None:

    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    remote_addr = request.META.get('REMOTE_ADDR')
    num_proxies = ninja_settings.NUM_PROXIES

    if num_proxies is None:
        return "".join(xff.split()) if xff else remote_addr
    if num_proxies == 0 or xff is None:
        return remote_addr

    addrs = xff.split(',')
    return addrs[-min(num_proxies, len(addrs))].strip()
