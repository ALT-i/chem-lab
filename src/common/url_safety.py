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


def _is_blocked_address(host: str, block_unresolvable: bool) -> bool:
    """True if the host resolves to anything that is not a public address."""
    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror:
        # Policy differs by call site. When saving, a transient DNS failure
        # must not stop an administrator storing a correct address, and a name
        # that does not resolve cannot carry the token anywhere anyway. When
        # about to send the token we fail closed instead: if we cannot see
        # where it points, we do not send it, and the request would have
        # failed regardless.
        return block_unresolvable

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


def validate_outbound_url(
    url: str, allow_http: bool = False, block_unresolvable: bool = False
) -> str:
    """Return the normalised URL, or raise UnsafeUrl.

    block_unresolvable=True is used immediately before a request carrying the
    token; it is left False when merely validating a value being saved.
    """
    if not url:
        raise UnsafeUrl('No site address was supplied.')

    parsed = urlparse(url)
    if parsed.scheme not in ('https',) and not (allow_http and parsed.scheme == 'http'):
        raise UnsafeUrl('The site address must start with https://.')
    if not parsed.hostname:
        raise UnsafeUrl('The site address does not include a host name.')
    if parsed.username or parsed.password:
        raise UnsafeUrl('The site address must not embed credentials.')

    if _is_blocked_address(parsed.hostname, block_unresolvable):
        raise UnsafeUrl(
            'That address could not be verified as a public host. Check the site '
            'address: internal and private addresses are not allowed.'
        )

    return url.rstrip('/')
