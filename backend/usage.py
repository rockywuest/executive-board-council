"""
Usage Tracking Module for Executive Board Council.

Tracks API usage per user (authenticated) and per IP (anonymous).
Implements the freemium model with tier-based limits.
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any
from collections import defaultdict
import threading

from fastapi import Request, HTTPException, status

from backend.auth import UserResponse, UserTier, get_client_ip


# ============================================================================
# Configuration
# ============================================================================

# Storage path for usage data
_PROJECT_ROOT = Path(__file__).parent.parent
USAGE_DATA_PATH = _PROJECT_ROOT / "data" / "usage"
USAGE_DATA_PATH.mkdir(parents=True, exist_ok=True)

# Files for persistence
USER_USAGE_FILE = USAGE_DATA_PATH / "user_usage.json"
IP_USAGE_FILE = USAGE_DATA_PATH / "ip_usage.json"
BLOCKED_IPS_FILE = USAGE_DATA_PATH / "blocked_ips.json"


# ============================================================================
# Usage Tracker Class
# ============================================================================

class UsageTracker:
    """
    Thread-safe usage tracker for API requests.

    Tracks usage by user ID (authenticated) and by IP (anonymous).
    Supports daily and monthly limits with automatic reset.
    """

    def __init__(self):
        self._lock = threading.Lock()

        # In-memory storage
        # Structure: {user_id: {"requests": [], "tier": "free"}}
        self._user_usage: Dict[str, Dict[str, Any]] = {}

        # Structure: {ip: {"requests": [], "blocked_until": None}}
        self._ip_usage: Dict[str, Dict[str, Any]] = {}

        # Blocked IPs with reason
        self._blocked_ips: Dict[str, Dict[str, Any]] = {}

        # Load from disk
        self._load_data()

    def _load_data(self):
        """Load usage data from disk."""
        try:
            if USER_USAGE_FILE.exists():
                with open(USER_USAGE_FILE, "r") as f:
                    self._user_usage = json.load(f)
        except Exception as e:
            print(f"Failed to load user usage data: {e}")

        try:
            if IP_USAGE_FILE.exists():
                with open(IP_USAGE_FILE, "r") as f:
                    self._ip_usage = json.load(f)
        except Exception as e:
            print(f"Failed to load IP usage data: {e}")

        try:
            if BLOCKED_IPS_FILE.exists():
                with open(BLOCKED_IPS_FILE, "r") as f:
                    self._blocked_ips = json.load(f)
        except Exception as e:
            print(f"Failed to load blocked IPs: {e}")

    def _save_data(self):
        """Save usage data to disk."""
        try:
            with open(USER_USAGE_FILE, "w") as f:
                json.dump(self._user_usage, f, indent=2)
        except Exception as e:
            print(f"Failed to save user usage data: {e}")

        try:
            with open(IP_USAGE_FILE, "w") as f:
                json.dump(self._ip_usage, f, indent=2)
        except Exception as e:
            print(f"Failed to save IP usage data: {e}")

        try:
            with open(BLOCKED_IPS_FILE, "w") as f:
                json.dump(self._blocked_ips, f, indent=2)
        except Exception as e:
            print(f"Failed to save blocked IPs: {e}")

    def _get_period_start(self, period: str) -> datetime:
        """Get the start of the current period (day or month)."""
        now = datetime.utcnow()
        if period == "daily":
            return now.replace(hour=0, minute=0, second=0, microsecond=0)
        else:  # monthly
            return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    def _count_requests_in_period(self, requests: list, period: str) -> int:
        """Count requests within the current period."""
        period_start = self._get_period_start(period)
        period_start_str = period_start.isoformat()

        count = 0
        for req_time in requests:
            if req_time >= period_start_str:
                count += 1
        return count

    def _cleanup_old_requests(self, requests: list) -> list:
        """Remove requests older than 32 days."""
        cutoff = (datetime.utcnow() - timedelta(days=32)).isoformat()
        return [r for r in requests if r >= cutoff]

    def is_ip_blocked(self, ip: str) -> tuple[bool, Optional[str]]:
        """
        Check if an IP is blocked.

        Returns:
            (is_blocked, reason)
        """
        with self._lock:
            if ip in self._blocked_ips:
                block_info = self._blocked_ips[ip]
                blocked_until = block_info.get("blocked_until")

                if blocked_until:
                    if datetime.utcnow().isoformat() < blocked_until:
                        return True, block_info.get("reason", "Rate limit exceeded")
                    else:
                        # Block expired, remove it
                        del self._blocked_ips[ip]
                        self._save_data()
                        return False, None
                else:
                    # Permanent block
                    return True, block_info.get("reason", "Blocked")

            return False, None

    def block_ip(self, ip: str, reason: str, hours: Optional[int] = 24):
        """
        Block an IP address.

        Args:
            ip: IP address to block
            reason: Reason for blocking
            hours: Hours to block (None for permanent)
        """
        with self._lock:
            blocked_until = None
            if hours:
                blocked_until = (datetime.utcnow() + timedelta(hours=hours)).isoformat()

            self._blocked_ips[ip] = {
                "reason": reason,
                "blocked_until": blocked_until,
                "blocked_at": datetime.utcnow().isoformat()
            }
            self._save_data()

    def unblock_ip(self, ip: str):
        """Unblock an IP address."""
        with self._lock:
            if ip in self._blocked_ips:
                del self._blocked_ips[ip]
                self._save_data()

    def get_user_usage(self, user_id: str, tier: str = UserTier.FREE) -> Dict[str, Any]:
        """
        Get usage info for an authenticated user.

        Returns:
            {
                "used_today": int,
                "used_this_month": int,
                "limit_daily": int,
                "limit_monthly": int,
                "remaining_daily": int,
                "remaining_monthly": int,
            }
        """
        with self._lock:
            if user_id not in self._user_usage:
                self._user_usage[user_id] = {"requests": [], "tier": tier}

            user_data = self._user_usage[user_id]
            requests = user_data.get("requests", [])

            daily_limit = UserTier.get_limit(tier, "daily")
            monthly_limit = UserTier.get_limit(tier, "monthly")

            used_today = self._count_requests_in_period(requests, "daily")
            used_month = self._count_requests_in_period(requests, "monthly")

            return {
                "used_today": used_today,
                "used_this_month": used_month,
                "limit_daily": daily_limit,
                "limit_monthly": monthly_limit,
                "remaining_daily": max(0, daily_limit - used_today) if daily_limit > 0 else -1,
                "remaining_monthly": max(0, monthly_limit - used_month) if monthly_limit > 0 else -1,
            }

    def get_ip_usage(self, ip: str) -> Dict[str, Any]:
        """
        Get usage info for an anonymous IP.

        Returns similar structure to get_user_usage.
        """
        with self._lock:
            if ip not in self._ip_usage:
                self._ip_usage[ip] = {"requests": []}

            ip_data = self._ip_usage[ip]
            requests = ip_data.get("requests", [])

            daily_limit = UserTier.get_limit(UserTier.ANONYMOUS, "daily")
            monthly_limit = UserTier.get_limit(UserTier.ANONYMOUS, "monthly")

            used_today = self._count_requests_in_period(requests, "daily")
            used_month = self._count_requests_in_period(requests, "monthly")

            return {
                "used_today": used_today,
                "used_this_month": used_month,
                "limit_daily": daily_limit,
                "limit_monthly": monthly_limit,
                "remaining_daily": max(0, daily_limit - used_today),
                "remaining_monthly": max(0, monthly_limit - used_month),
            }

    def check_and_record_request(
        self,
        request: Request,
        user: Optional[UserResponse] = None
    ) -> Dict[str, Any]:
        """
        Check if request is allowed and record it.

        Args:
            request: FastAPI request object
            user: Authenticated user (None for anonymous)

        Returns:
            Usage info after recording

        Raises:
            HTTPException if rate limit exceeded
        """
        ip = get_client_ip(request)

        # Check if IP is blocked
        is_blocked, reason = self.is_ip_blocked(ip)
        if is_blocked:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "rate_limit_exceeded",
                    "message": reason or "Your IP has been temporarily blocked",
                    "action": "create_account",
                    "hint": "Create a free account to continue using the service"
                }
            )

        with self._lock:
            now = datetime.utcnow().isoformat()

            if user:
                # Authenticated user
                tier = user.tier

                if user.id not in self._user_usage:
                    self._user_usage[user.id] = {"requests": [], "tier": tier}

                user_data = self._user_usage[user.id]
                user_data["tier"] = tier
                requests = user_data.get("requests", [])

                # Cleanup old requests
                requests = self._cleanup_old_requests(requests)

                # Check limits
                monthly_limit = UserTier.get_limit(tier, "monthly")
                used_month = self._count_requests_in_period(requests, "monthly")

                if monthly_limit > 0 and used_month >= monthly_limit:
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail={
                            "error": "rate_limit_exceeded",
                            "message": f"Monthly limit of {monthly_limit} requests reached",
                            "action": "upgrade",
                            "hint": "Upgrade to Pro for more requests",
                            "used": used_month,
                            "limit": monthly_limit
                        }
                    )

                # Record request
                requests.append(now)
                user_data["requests"] = requests
                self._save_data()

                return self.get_user_usage(user.id, tier)

            else:
                # Anonymous user - track by IP
                if ip not in self._ip_usage:
                    self._ip_usage[ip] = {"requests": []}

                ip_data = self._ip_usage[ip]
                requests = ip_data.get("requests", [])

                # Cleanup old requests
                requests = self._cleanup_old_requests(requests)

                # Check daily limit for anonymous
                daily_limit = UserTier.get_limit(UserTier.ANONYMOUS, "daily")
                used_today = self._count_requests_in_period(requests, "daily")

                if used_today >= daily_limit:
                    # Block IP for 24 hours if they exceed limit
                    if used_today == daily_limit:
                        self.block_ip(ip, "Daily anonymous limit exceeded", hours=24)

                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail={
                            "error": "rate_limit_exceeded",
                            "message": f"Free limit of {daily_limit} requests per day reached",
                            "action": "create_account",
                            "hint": "Create a free account for 5 requests per month, or upgrade to Pro for 50",
                            "used": used_today,
                            "limit": daily_limit
                        }
                    )

                # Record request
                requests.append(now)
                ip_data["requests"] = requests
                self._save_data()

                return self.get_ip_usage(ip)

    def get_all_stats(self) -> Dict[str, Any]:
        """Get overall usage statistics (admin only)."""
        with self._lock:
            total_users = len(self._user_usage)
            total_ips = len(self._ip_usage)
            blocked_ips = len(self._blocked_ips)

            # Count by tier
            tiers = defaultdict(int)
            for user_data in self._user_usage.values():
                tiers[user_data.get("tier", "free")] += 1

            return {
                "total_users": total_users,
                "total_anonymous_ips": total_ips,
                "blocked_ips": blocked_ips,
                "users_by_tier": dict(tiers),
                "timestamp": datetime.utcnow().isoformat()
            }


# ============================================================================
# Singleton Instance
# ============================================================================

_usage_tracker: Optional[UsageTracker] = None


def get_usage_tracker() -> UsageTracker:
    """Get the singleton usage tracker instance."""
    global _usage_tracker
    if _usage_tracker is None:
        _usage_tracker = UsageTracker()
    return _usage_tracker
