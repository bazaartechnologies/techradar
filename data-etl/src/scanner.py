"""
GitHub repository scanner with pagination and rate limiting.
"""

import logging
import fnmatch
from typing import List, Dict, Set, Optional
from github import Github
from github.Repository import Repository
from github.GithubException import GithubException

from rate_limiter import RateLimiter, CircuitBreaker
from detector import TechnologyDetector
from ai_detector import AITechnologyDetector
from domain_detector import DomainDetector
from deep_scanner import DeepScanner

logger = logging.getLogger(__name__)


class GitHubScanner:
    """Scans GitHub repositories for technology usage."""

    def __init__(self, github_token: str, config: dict, progress_tracker=None, openai_api_key: str = None):
        """
        Initialize scanner.

        Args:
            github_token: GitHub personal access token
            config: Configuration dictionary
            progress_tracker: Optional ProgressTracker for resumability
            openai_api_key: Optional OpenAI API key for domain detection
        """
        self.github = Github(github_token, per_page=100)
        self.config = config
        self.progress_tracker = progress_tracker
        self.rate_limiter = RateLimiter(
            self.github,
            max_per_minute=config.get('rate_limit', {}).get('max_per_minute', 25),
            safety_threshold=config.get('rate_limit', {}).get('safety_threshold', 100)
        )
        self.circuit_breaker = CircuitBreaker(failure_threshold=5, timeout=60)

        # Initialize detector based on config mode
        detection_config = config.get('detection', {})
        detection_mode = detection_config.get('mode', 'legacy')

        if detection_mode == 'ai' and openai_api_key:
            self.detector = AITechnologyDetector(openai_api_key, config)
            logger.info("Using AI-driven technology detection")
        elif detection_mode == 'hybrid' and openai_api_key:
            # Use both detectors - AI first, fallback to legacy
            self.detector = AITechnologyDetector(openai_api_key, config)
            self.legacy_detector = TechnologyDetector()
            logger.info("Using hybrid detection (AI + legacy fallback)")
        else:
            self.detector = TechnologyDetector()
            logger.info("Using legacy hardcoded detection")

        # Initialize domain detector if API key provided
        self.domain_detector = None
        if openai_api_key:
            self.domain_detector = DomainDetector(openai_api_key, config)
            logger.info("Domain detection enabled")

        # Initialize deep scanner if API key provided
        self.deep_scanner = None
        if openai_api_key:
            self.deep_scanner = DeepScanner(openai_api_key, config)
            if config.get('deep_scan', {}).get('enabled', False):
                deep_repos = config.get('deep_scan', {}).get('repositories', [])
                logger.info(f"Deep scanning enabled for: {', '.join(deep_repos)}")

        # Get repo limit from config (can be overridden externally)
        config_limit = config.get('github', {}).get('repo_limit', 0)
        self.repo_limit = config_limit if config_limit > 0 else None

        # Get checkpoint save interval from config
        self.checkpoint_save_interval = config.get('checkpoint', {}).get('save_interval', 10)

        # Stats
        self.stats = {
            'repos_scanned': 0,
            'repos_skipped': 0,
            'api_calls': 0,
            'errors': 0
        }

    def scan_organizations(
        self,
        progress_callback: Optional[callable] = None
    ) -> tuple[Dict[str, int], List[Dict]]:
        """
        Scan all configured organizations.

        Args:
            progress_callback: Optional callback(current, total, repo_name)

        Returns:
            Tuple of (tech_counts, repo_details)
        """
        orgs = self.config['github']['organizations']
        all_repo_techs = []
        repo_details = []

        for org_name in orgs:
            logger.info(f"Scanning organization: {org_name}")

            try:
                org_techs, org_repos = self.scan_organization(
                    org_name,
                    progress_callback
                )
                all_repo_techs.extend(org_techs)
                repo_details.extend(org_repos)

            except GithubException as e:
                logger.error(f"Error accessing organization {org_name}: {e}")
                self.stats['errors'] += 1
            except Exception as e:
                logger.error(f"Unexpected error scanning {org_name}: {e}")
                self.stats['errors'] += 1

        # Aggregate technologies
        tech_counts = self.detector.aggregate_technologies(all_repo_techs)

        logger.info(f"Scan complete. Found {len(tech_counts)} unique technologies.")
        return tech_counts, repo_details

    def scan_organization(
        self,
        org_name: str,
        progress_callback: Optional[callable] = None
    ) -> tuple[List[Dict[str, Set[str]]], List[Dict]]:
        """
        Scan all repositories in an organization.

        Args:
            org_name: Organization name
            progress_callback: Optional progress callback

        Returns:
            Tuple of (list of repo technologies, list of repo details)
        """
        self.rate_limiter.check_and_wait()
        self.stats['api_calls'] += 1

        org = self.github.get_organization(org_name)
        repos = list(org.get_repos())

        # Apply limit if specified
        total_repos = len(repos)
        if self.repo_limit and self.repo_limit < total_repos:
            repos = repos[:self.repo_limit]
            logger.info(f"Found {total_repos} repositories in {org_name}, limiting to {self.repo_limit}")
        else:
            logger.info(f"Found {len(repos)} repositories in {org_name}")

        all_repo_techs = []
        repo_details = []

        for idx, repo in enumerate(repos):
            # Check if already scanned (checkpoint resume)
            if self.progress_tracker and self.progress_tracker.is_scanned(repo.full_name):
                logger.info(f"Skipping {repo.name} (already scanned in previous run)")
                self.stats['repos_skipped'] += 1
                continue

            # Check if should skip
            if self._should_skip_repo(repo):
                logger.debug(f"Skipping {repo.name} (filtered)")
                self.stats['repos_skipped'] += 1
                continue

            # Progress callback
            if progress_callback:
                progress_callback(idx + 1, len(repos), repo.name)

            try:
                # Scan repository with circuit breaker protection
                techs = self.circuit_breaker.call(
                    self._scan_repository,
                    repo
                )

                if techs:
                    all_repo_techs.append(techs)

                    # Detect domain if enabled
                    domain_info = None
                    if self.domain_detector:
                        try:
                            domain_info = self.domain_detector.detect_domain(repo, techs)
                        except Exception as e:
                            logger.warning(f"Domain detection failed for {repo.name}: {e}")

                    repo_details.append({
                        'name': repo.name,
                        'full_name': repo.full_name,
                        'url': repo.html_url,
                        'stars': repo.stargazers_count,
                        'technologies': techs,
                        'temporal_metadata': self._get_temporal_metadata(repo),
                        'domain': domain_info
                    })

                self.stats['repos_scanned'] += 1

                # Mark as scanned (checkpoint)
                if self.progress_tracker:
                    self.progress_tracker.mark_scanned(
                        repo.full_name,
                        save_interval=self.checkpoint_save_interval
                    )

            except Exception as e:
                logger.error(f"Error scanning {repo.name}: {e}")
                self.stats['errors'] += 1

        return all_repo_techs, repo_details

    def _scan_repository(self, repo: Repository) -> Dict[str, Set[str]]:
        """
        Scan a single repository for technologies.

        Args:
            repo: Repository object

        Returns:
            Dict of technologies by category
        """
        logger.debug(f"Scanning repository: {repo.name}")

        # Rate limiting
        self.rate_limiter.check_and_wait()
        self.stats['api_calls'] += 1

        # Detect technologies (standard detection)
        technologies = self.detector.detect_technologies(repo)

        # Deep scan if enabled for this repo
        if self.deep_scanner and self.deep_scanner.should_deep_scan(repo.name):
            try:
                logger.info(f"🔍 Deep scanning {repo.name}...")
                deep_techs = self.deep_scanner.deep_scan_repository(repo)

                if deep_techs:
                    # Add deep scan discoveries to tools category
                    if 'tools' not in technologies:
                        technologies['tools'] = set()

                    before_count = len(technologies['tools'])
                    technologies['tools'].update(deep_techs)
                    after_count = len(technologies['tools'])

                    new_techs = after_count - before_count
                    if new_techs > 0:
                        logger.info(f"✅ Deep scan added {new_techs} new technologies to {repo.name}")

            except Exception as e:
                logger.error(f"Deep scan failed for {repo.name}: {e}")

        # Log what we found
        tech_count = sum(len(techs) for techs in technologies.values())
        if tech_count > 0:
            logger.info(f"  {repo.name}: Found {tech_count} technologies")

        return technologies

    def _should_skip_repo(self, repo: Repository) -> bool:
        """
        Check if repository should be skipped based on filters.

        Args:
            repo: Repository object

        Returns:
            True if should skip
        """
        config = self.config['github']

        # Check archived
        if repo.archived and not config.get('include_archived', False):
            return True

        # Check fork
        if repo.fork and not config.get('include_forks', False):
            return True

        # Check private
        if repo.private and not config.get('include_private', True):
            return True

        # Check stars
        min_stars = config.get('min_stars', 0)
        if repo.stargazers_count < min_stars:
            return True

        # Check exclude patterns
        exclude_patterns = config.get('exclude_repos', [])
        for pattern in exclude_patterns:
            if fnmatch.fnmatch(repo.name, pattern):
                return True

        return False

    def _get_temporal_metadata(self, repo: Repository) -> dict:
        """
        Extract temporal metadata from repository.

        Args:
            repo: Repository object

        Returns:
            Dict with temporal information
        """
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc)

        # Get dates
        created_at = repo.created_at
        pushed_at = repo.pushed_at if repo.pushed_at else created_at

        # Calculate age
        age_days = (now - created_at).days
        age_months = age_days / 30.0

        # Calculate days since last push
        days_since_push = (now - pushed_at).days

        # Determine if active (commits in last 90 days)
        # 90 days is more realistic for production systems and stable libraries
        is_active = days_since_push < 90

        # Categorize by age
        is_recent = age_months <= 6
        is_new = age_months <= 12
        is_legacy = age_months > 24

        return {
            'created_at': created_at.isoformat(),
            'pushed_at': pushed_at.isoformat(),
            'age_months': round(age_months, 1),
            'days_since_push': days_since_push,
            'is_active': is_active,
            'is_recent': is_recent,       # < 6 months
            'is_new': is_new,              # < 12 months
            'is_legacy': is_legacy         # > 24 months
        }

    def get_stats(self) -> dict:
        """Get scanning statistics."""
        return {
            **self.stats,
            'rate_limit': self.rate_limiter.get_status()
        }
