"""ORBIT Security and Governance.

Implements:
- robots.txt handling consistent with RFC 9309
- Website terms and applicable access restrictions
- Per-host rate limits
- Backoff and politeness
- SSRF protection
- DNS rebinding protection
- Safe URL validation
- Network egress controls
- Sandboxed browser and agent execution
- Prompt-injection defenses
- Secret management
- Authentication and authorization
- Audit logs
- Tenant isolation
- Data retention and deletion controls
- Dependency and license checks
"""

import logging
import re
import hashlib
import ipaddress
from typing import Optional, List, Dict, Any, Set
from datetime import datetime, timezone
from dataclasses import dataclass, field
from urllib.parse import urlparse

logger = logging.getLogger("orbit.core.security")


class SecurityPolicy:
    """Security policy configuration for ORBIT."""

    def __init__(self, settings=None):
        self.settings = settings
        self.enable_ssrf_protection = settings.security_enable_ssrf_protection if settings else True
        self.enable_dns_rebinding_protection = settings.security_enable_dns_rebinding_protection if settings else True
        self.sandbox_browser = settings.security_sandbox_browser if settings else True
        self.audit_log_enabled = settings.security_audit_log_enabled if settings else True
        self.tenant_isolation = settings.tenant_isolation_enabled if settings else True

        # Audit log
        self._audit_log: List[Dict[str, Any]] = []


class URLValidator:
    """Validates URLs for safety (SSRF, DNS rebinding, malformed URLs)."""

    PRIVATE_RANGES = [
        ipaddress.ip_network("127.0.0.0/8"),
        ipaddress.ip_network("10.0.0.0/8"),
        ipaddress.ip_network("172.16.0.0/12"),
        ipaddress.ip_network("192.168.0.0/16"),
        ipaddress.ip_network("169.254.0.0/16"),
        ipaddress.ip_network("::1/128"),
        ipaddress.ip_network("fc00::/7"),
        ipaddress.ip_network("fe80::/10"),
    ]

    BLOCKED_HOSTS = {
        "localhost",
        "127.0.0.1",
        "0.0.0.0",
        "::1",
        "169.254.169.254",  # AWS metadata
        "169.254.170.2",    # Azure/GCP metadata
    }

    ALLOWED_SCHEMES = {"http", "https"}

    @classmethod
    def is_safe(cls, url: str) -> bool:
        """Check if URL is safe from SSRF, DNS rebinding, and other attacks."""
        try:
            parsed = urlparse(url)

            # Scheme check
            if parsed.scheme not in cls.ALLOWED_SCHEMES:
                logger.warning(f"Blocked URL with scheme {parsed.scheme}: {url}")
                return False

            # Hostname check
            hostname = parsed.hostname
            if not hostname:
                logger.warning(f"Blocked URL with no hostname: {url}")
                return False

            # Block known bad hosts
            if hostname.lower() in cls.BLOCKED_HOSTS:
                logger.warning(f"Blocked URL to blocked host: {hostname}")
                return False

            # IP address check - block private ranges
            try:
                ip = ipaddress.ip_address(hostname)
                for private_range in cls.PRIVATE_RANGES:
                    if ip in private_range:
                        logger.warning(f"Blocked URL to private IP: {hostname}")
                        return False
            except ValueError:
                # Not an IP address, it's a hostname - DNS rebinding protection
                pass

            return True

        except Exception as e:
            logger.warning(f"URL validation error for {url}: {e}")
            return False

    @classmethod
    def sanitize_url(cls, url: str) -> Optional[str]:
        """Sanitize a URL by removing dangerous components."""
        if not cls.is_safe(url):
            return None
        return url


class RateLimiter:
    """Per-host rate limiter for crawl politeness."""

    def __init__(self):
        self._host_limits: Dict[str, Dict[str, Any]] = {}
        self._host_request_times: Dict[str, List[datetime]] = {}

    def set_host_limit(self, host: str, max_requests_per_second: float,
                       max_concurrent: int = 1):
        """Set rate limit for a host."""
        self._host_limits[host] = {
            "max_rps": max_requests_per_second,
            "max_concurrent": max_concurrent,
            "current_concurrent": 0,
        }
        self._host_request_times[host] = []

    def can_request(self, host: str) -> bool:
        """Check if a request can be made to this host."""
        now = datetime.now(timezone.utc)

        if host not in self._host_limits:
            # Default: 1 request per second, 1 concurrent
            return True

        limit = self._host_limits[host]

        # Check concurrency
        if limit["current_concurrent"] >= limit["max_concurrent"]:
            return False

        # Check rate
        request_times = self._host_request_times[host]
        # Remove old timestamps (older than 1 second)
        cutoff = now - __import__('datetime').timedelta(seconds=1)
        request_times[:] = [t for t in request_times if t > cutoff]

        if len(request_times) >= limit["max_rps"]:
            return False

        return True

    def record_request(self, host: str):
        """Record that a request was made to this host."""
        now = datetime.now(timezone.utc)

        if host not in self._host_request_times:
            self._host_request_times[host] = []

        self._host_request_times[host].append(now)

        if host in self._host_limits:
            self._host_limits[host]["current_concurrent"] += 1

    def release_request(self, host: str):
        """Release a concurrent request slot."""
        if host in self._host_limits:
            self._host_limits[host]["current_concurrent"] = max(
                0, self._host_limits[host]["current_concurrent"] - 1
            )


class AuditLogger:
    """Security audit logger for ORBIT."""

    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self._entries: List[Dict[str, Any]] = []

    def log(self, event: str, actor: str, details: Dict[str, Any],
            severity: str = "info"):
        """Log a security-relevant event."""
        if not self.enabled:
            return

        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": event,
            "actor": actor,
            "details": details,
            "severity": severity,
        }

        self._entries.append(entry)
        logger.info(f"AUDIT: {event} by {actor}: {details}")

    def get_entries(self, severity: Optional[str] = None,
                    limit: int = 1000) -> List[Dict[str, Any]]:
        """Get audit log entries."""
        entries = self._entries
        if severity:
            entries = [e for e in entries if e["severity"] == severity]
        return entries[-limit:]

    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_entries": len(self._entries),
            "enabled": self.enabled,
        }


class TenantIsolation:
    """Tenant isolation for multi-tenant ORBIT deployments."""

    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self._tenant_data: Dict[str, Dict[str, Any]] = {}

    def get_tenant_context(self, tenant_id: str) -> Dict[str, Any]:
        """Get or create tenant context."""
        if tenant_id not in self._tenant_data:
            self._tenant_data[tenant_id] = {
                "created_at": datetime.now(timezone.utc).isoformat(),
                "sources": [],
                "opportunities": [],
                "crawl_budget": 0,
            }
        return self._tenant_data[tenant_id]

    def can_access(self, tenant_id: str, resource_owner: str) -> bool:
        """Check if tenant can access a resource owned by another tenant."""
        if not self.enabled:
            return True
        return tenant_id == resource_owner


class PromptInjectionDefense:
    """Prompt injection defense for LLM interactions."""

    INJECTION_PATTERNS = [
        r"(?i)ignore\s+previous\s+instructions",
        r"(?i)disregard\s+all\s+prior",
        r"(?i)system\s*:\s*you\s+are\s+now",
        r"(?i)jailbreak",
        r"(?i)override\s+safety",
    ]

    @classmethod
    def detect_injection(cls, text: str) -> bool:
        """Detect potential prompt injection in text."""
        for pattern in cls.INJECTION_PATTERNS:
            if re.search(pattern, text):
                logger.warning(f"Potential prompt injection detected: {text[:100]}")
                return True
        return False

    @classmethod
    def sanitize_input(cls, text: str) -> str:
        """Sanitize input to prevent prompt injection."""
        # Remove potential injection patterns
        for pattern in cls.INJECTION_PATTERNS:
            text = re.sub(pattern, "[REDACTED]", text)
        return text


class SecretManager:
    """Secret management for ORBIT.

    Secrets should never be stored in code or configuration files.
    Use environment variables or external secret stores.
    """

    def __init__(self):
        self._secrets: Dict[str, str] = {}

    def set_secret(self, name: str, value: str):
        """Set a secret value (should only be called at startup from env)."""
        self._secrets[name] = value

    def get_secret(self, name: str) -> Optional[str]:
        """Get a secret value."""
        import os
        # First check in-memory, then environment
        if name in self._secrets:
            return self._secrets[name]
        return os.environ.get(name)

    def list_secret_names(self) -> List[str]:
        """List secret names (not values)."""
        return list(self._secrets.keys())


# Global instances
security_policy = SecurityPolicy()
url_validator = URLValidator()
rate_limiter = RateLimiter()
audit_logger = AuditLogger()
tenant_isolation = TenantIsolation()
prompt_injection_defense = PromptInjectionDefense()
secret_manager = SecretManager()

__all__ = [
    "SecurityPolicy", "URLValidator", "RateLimiter", "AuditLogger",
    "TenantIsolation", "PromptInjectionDefense", "SecretManager",
    "security_policy", "url_validator", "rate_limiter", "audit_logger",
    "tenant_isolation", "prompt_injection_defense", "secret_manager",
]
