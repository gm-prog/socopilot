"""Regex patterns for IOC extraction."""

import re

# IPv4
IPV4_RE = re.compile(
    r"\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b"
)

# IPv6 (simplified)
IPV6_RE = re.compile(
    r"\b(?:[0-9a-fA-F]{1,4}:){2,7}[0-9a-fA-F]{1,4}\b"
)

# Domain (exclude common false positives)
DOMAIN_RE = re.compile(
    r"\b(?!(?:\d{1,3}\.){3}\d{1,3})(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}\b"
)

URL_RE = re.compile(
    r"https?://[^\s<>\"']+",
    re.IGNORECASE,
)

MD5_RE = re.compile(r"\b[a-fA-F0-9]{32}\b")
SHA1_RE = re.compile(r"\b[a-fA-F0-9]{40}\b")
SHA256_RE = re.compile(r"\b[a-fA-F0-9]{64}\b")

EMAIL_RE = re.compile(
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
)

# Windows-style username or simple user@domain in entities
USERNAME_RE = re.compile(r"\b(?:[a-zA-Z0-9._-]+\\[a-zA-Z0-9._-]+|[a-zA-Z0-9._-]{2,32})\b")

# Hostname heuristic (short alphanumeric + hyphen, not pure IP)
HOSTNAME_RE = re.compile(
    r"\b(?![\d.]+$)[a-zA-Z][a-zA-Z0-9-]{0,62}\b"
)

PRIVATE_IPV4_PREFIXES = ("10.", "172.16.", "172.17.", "172.18.", "172.19.", "172.2", "192.168.", "127.")
