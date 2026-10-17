"""Guard against pointing outbound requests at internal infrastructure.

The Moodle site address is operator-supplied, and the client sends a secret
token to whatever host it names, so an unchecked address is both an SSRF
vector and a way to exfiltrate the token to an attacker-controlled server.
"""
import ipaddress
import socket
from urllib.parse import urlparse


class UnsafeUrl(ValueError):
    """The supplied URL may not be used for outbound requests."""


def _is_blocked_address(host: str) -> bool:
    """True if the host resolves to anything that is not a public address."""
    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror:
        # If we cannot see where it points, we cannot vouch for it.
        return True

    for info in infos:
        address = info[4][0]
        try:
            ip = ipaddress.ip_address(address)
        except ValueError:
            continue
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local       # includes 169.254.169.254 metadata
            or ip.is_reserved
            or ip.is_multicast
            or ip.is_unspecified
        ):
            return True
    return False


def validate_outbound_url(url: str, allow_http: bool = False) -> str:
    """Return the normalised URL, or raise UnsafeUrl."""
    if not url:
        raise UnsafeUrl('No site address was supplied.')

    parsed = urlparse(url)
    if parsed.scheme not in ('https',) and not (allow_http and parsed.scheme == 'http'):
        raise UnsafeUrl('The site address must start with https://.')
    if not parsed.hostname:
        raise UnsafeUrl('The site address does not include a host name.')
    if parsed.username or parsed.password:
        raise UnsafeUrl('The site address must not embed credentials.')

    if _is_blocked_address(parsed.hostname):
        raise UnsafeUrl(
            'That address points at a private or internal host, which is not allowed.'
        )

    return url.rstrip('/')
