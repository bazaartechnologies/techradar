"""
Rate limiter for GitHub API to prevent hitting rate limits.
"""

import time
import logging
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class RateLimiter:
    """Manages GitHub API rate limiting."""

    def __init__(self, github_client, max_per_minute: int = 25, safety_threshold: int = 100):
        """
        Initialize rate limiter.

        Args:
            github_client: PyGithub Github instance
            max_per_minute: Maximum requests per minute
            safety_threshold: Pause if remaining requests below this
        """
        self.github = github_client
        self.max_per_minute = max_per_minute
        self.safety_threshold = safety_threshold
        self.request_times = []

        # Cache for rate limit (avoid checking every time)
        self.rate_limit_cache = None
        self.rate_limit_cache_time = 0
        self.cache_ttl = 10  # Cache for 10 seconds

    def check_and_wait(self) -> None:
        """Check rate limit and wait if necessary."""
        # Check GitHub's rate limit (with caching to avoid excessive API calls)
        now = time.time()

        # Only check actual rate limit every 10 seconds
        if self.rate_limit_cache is None or (now - self.rate_limit_cache_time) > self.cache_ttl:
            rate_limit = self.github.get_rate_limit()
            self.rate_limit_cache = rate_limit
            self.rate_limit_cache_time = now
        else:
            rate_limit = self.rate_limit_cache

        core_limit = rate_limit.core

        remaining = core_limit.remaining
        reset_time = core_limit.reset

        logger.debug(f"GitHub rate limit: {remaining}/{core_limit.limit} remaining")

        # If we're below safety threshold, wait until reset
        if remaining < self.safety_threshold:
            wait_seconds = (reset_time - datetime.now()).total_seconds()
            if wait_seconds > 0:
                logger.warning(
                    f"Rate limit low ({remaining} remaining). "
                    f"Waiting {wait_seconds:.0f}s until reset..."
                )
                time.sleep(wait_seconds + 1)  # Add 1s buffer
                # Invalidate cache after waiting
                self.rate_limit_cache = None

        # Enforce per-minute limit
        self._enforce_per_minute_limit()

    def _enforce_per_minute_limit(self) -> None:
        """Ensure we don't exceed max requests per minute."""
        now = time.time()

        # Remove requests older than 1 minute
        self.request_times = [t for t in self.request_times if now - t < 60]

        # If we've hit the limit, wait
        if len(self.request_times) >= self.max_per_minute:
            oldest = self.request_times[0]
            wait_seconds = 60 - (now - oldest)
            if wait_seconds > 0:
                logger.debug(f"Per-minute limit reached. Waiting {wait_seconds:.1f}s...")
                time.sleep(wait_seconds)

        # Record this request
        self.request_times.append(now)

    def get_status(self) -> dict:
        """Get current rate limit status."""
        rate_limit = self.github.get_rate_limit()
        core_limit = rate_limit.core

        return {
            'remaining': core_limit.remaining,
            'limit': core_limit.limit,
            'reset': core_limit.reset.isoformat() if core_limit.reset else None,
            'used': core_limit.limit - core_limit.remaining
        }


class CircuitBreaker:
    """Circuit breaker pattern for API calls."""

    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        """
        Initialize circuit breaker.

        Args:
            failure_threshold: Number of failures before opening circuit
            timeout: Seconds to wait before trying again
        """
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN

    def call(self, func, *args, **kwargs):
        """
        Call function with circuit breaker protection.

        Args:
            func: Function to call
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Function result

        Raises:
            Exception: If circuit is open or function fails
        """
        if self.state == 'OPEN':
            # Check if timeout has passed
            if time.time() - self.last_failure_time >= self.timeout:
                logger.info("Circuit breaker entering HALF_OPEN state")
                self.state = 'HALF_OPEN'
            else:
                remaining = self.timeout - (time.time() - self.last_failure_time)
                raise Exception(
                    f"Circuit breaker is OPEN. Retry in {remaining:.0f}s"
                )

        try:
            result = func(*args, **kwargs)

            # Success - reset counter
            if self.state == 'HALF_OPEN':
                logger.info("Circuit breaker closing (recovery successful)")
                self.state = 'CLOSED'
            self.failure_count = 0

            return result

        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()

            if self.failure_count >= self.failure_threshold:
                logger.error(
                    f"Circuit breaker opening after {self.failure_count} failures"
                )
                self.state = 'OPEN'

            raise

    def reset(self) -> None:
        """Manually reset circuit breaker."""
        self.failure_count = 0
        self.state = 'CLOSED'
        self.last_failure_time = None
        logger.info("Circuit breaker manually reset")
