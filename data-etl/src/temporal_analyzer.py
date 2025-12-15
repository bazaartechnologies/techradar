"""
Temporal analysis of technology adoption patterns.
Analyzes when technologies were adopted and how actively they're being used.
"""

import logging
from typing import Dict, List
from collections import defaultdict

logger = logging.getLogger(__name__)


class TemporalAnalyzer:
    """Analyzes technology adoption patterns over time."""

    def analyze_technology(
        self,
        tech_name: str,
        repo_details: List[Dict],
        domain_filter: str = None
    ) -> Dict:
        """
        Analyze temporal patterns for a specific technology.

        Args:
            tech_name: Name of the technology
            repo_details: List of repository detail dictionaries
            domain_filter: Optional domain to filter by (e.g., 'mobile', 'backend')

        Returns:
            Dict with temporal analysis (includes domain breakdown if available)
        """
        # Find repos using this technology
        repos_with_tech = []
        for repo in repo_details:
            # Check if tech is in any category
            for category_techs in repo['technologies'].values():
                if tech_name in category_techs:
                    repos_with_tech.append(repo)
                    break

        if not repos_with_tech:
            return self._empty_analysis()

        # Apply domain filter if specified
        if domain_filter:
            repos_with_tech = [
                r for r in repos_with_tech
                if r.get('domain', {}).get('domain') == domain_filter
            ]
            if not repos_with_tech:
                return self._empty_analysis()

        total_repos = len(repos_with_tech)

        # Analyze temporal patterns
        recent_repos = sum(1 for r in repos_with_tech if r['temporal_metadata']['is_recent'])
        new_repos = sum(1 for r in repos_with_tech if r['temporal_metadata']['is_new'])
        legacy_repos = sum(1 for r in repos_with_tech if r['temporal_metadata']['is_legacy'])
        active_repos = sum(1 for r in repos_with_tech if r['temporal_metadata']['is_active'])
        stale_repos = total_repos - active_repos

        # Calculate average age
        avg_age = sum(r['temporal_metadata']['age_months'] for r in repos_with_tech) / total_repos

        # Determine trend
        trend = self._determine_trend(
            recent_repos,
            new_repos,
            legacy_repos,
            active_repos,
            total_repos
        )

        # Calculate scores
        recency_score = self._calculate_recency_score(recent_repos, new_repos, total_repos)
        activity_score = active_repos / total_repos if total_repos > 0 else 0

        # Analyze domain breakdown if not filtered
        by_domain = None
        if not domain_filter:
            by_domain = self._analyze_by_domain(tech_name, repos_with_tech)

        result = {
            'total_repos': total_repos,
            'recent_repos': recent_repos,           # < 6 months
            'new_repos': new_repos,                 # < 12 months
            'legacy_repos': legacy_repos,           # > 24 months
            'active_repos': active_repos,           # commits in last 60 days
            'stale_repos': stale_repos,             # no commits in 60+ days
            'avg_age_months': round(avg_age, 1),
            'trend': trend,                         # GROWING, STABLE, DECLINING, ABANDONED
            'recency_score': round(recency_score, 3),
            'activity_score': round(activity_score, 3),
            'repos_list': [r['name'] for r in repos_with_tech[:10]]  # First 10 for reference
        }

        if by_domain:
            result['by_domain'] = by_domain

        return result

    def _analyze_by_domain(
        self,
        tech_name: str,
        repos_with_tech: List[Dict]
    ) -> Dict:
        """
        Analyze technology usage across different domains.

        Args:
            tech_name: Technology name
            repos_with_tech: Repos using this technology

        Returns:
            Dict mapping domains to their specific metrics
        """
        domain_groups = defaultdict(list)

        # Group repos by domain
        for repo in repos_with_tech:
            domain_info = repo.get('domain')
            if domain_info and domain_info.get('domain'):
                domain = domain_info['domain']
                domain_groups[domain].append(repo)

        # Analyze each domain
        domain_analysis = {}
        for domain, repos in domain_groups.items():
            total = len(repos)
            recent = sum(1 for r in repos if r['temporal_metadata']['is_recent'])
            new = sum(1 for r in repos if r['temporal_metadata']['is_new'])
            active = sum(1 for r in repos if r['temporal_metadata']['is_active'])

            domain_analysis[domain] = {
                'total_repos': total,
                'recent_repos': recent,
                'new_repos': new,
                'active_repos': active,
                'recency_score': round(self._calculate_recency_score(recent, new, total), 3),
                'activity_score': round(active / total, 3) if total > 0 else 0,
                'trend': self._determine_trend(recent, new,
                                              sum(1 for r in repos if r['temporal_metadata']['is_legacy']),
                                              active, total)
            }

        return domain_analysis

    def _empty_analysis(self) -> Dict:
        """Return empty analysis structure."""
        return {
            'total_repos': 0,
            'recent_repos': 0,
            'new_repos': 0,
            'legacy_repos': 0,
            'active_repos': 0,
            'stale_repos': 0,
            'avg_age_months': 0,
            'trend': 'NONE',
            'recency_score': 0,
            'activity_score': 0,
            'repos_list': []
        }

    def _determine_trend(
        self,
        recent: int,
        new: int,
        legacy: int,
        active: int,
        total: int
    ) -> str:
        """
        Determine adoption trend.

        Returns:
            GROWING, STABLE, DECLINING, or ABANDONED
        """
        if total == 0:
            return 'NONE'

        recent_ratio = recent / total
        new_ratio = new / total
        legacy_ratio = legacy / total
        activity_ratio = active / total

        # GROWING: New adoption + high activity
        if recent_ratio > 0.5 or (new_ratio > 0.6 and activity_ratio > 0.7):
            return 'GROWING'

        # ABANDONED: Mostly legacy + low activity
        if legacy_ratio > 0.7 and activity_ratio < 0.3:
            return 'ABANDONED'

        # DECLINING: No new adoption + declining activity
        if recent_ratio == 0 and new_ratio < 0.3 and activity_ratio < 0.5:
            return 'DECLINING'

        # STABLE: Consistent usage
        return 'STABLE'

    def _calculate_recency_score(
        self,
        recent: int,
        new: int,
        total: int
    ) -> float:
        """
        Calculate recency score (0-1).

        Higher score = more recent adoption
        """
        if total == 0:
            return 0

        # Weight recent repos more heavily
        return (recent * 1.0 + new * 0.5) / total

    def aggregate_temporal_stats(self, repo_details: List[Dict]) -> Dict:
        """
        Get aggregate temporal statistics across all repos.

        Args:
            repo_details: List of repository details

        Returns:
            Dict with aggregate stats
        """
        if not repo_details:
            return {}

        total = len(repo_details)
        recent = sum(1 for r in repo_details if r['temporal_metadata']['is_recent'])
        new = sum(1 for r in repo_details if r['temporal_metadata']['is_new'])
        legacy = sum(1 for r in repo_details if r['temporal_metadata']['is_legacy'])
        active = sum(1 for r in repo_details if r['temporal_metadata']['is_active'])

        return {
            'total_repositories': total,
            'recent_repositories': recent,
            'new_repositories': new,
            'legacy_repositories': legacy,
            'active_repositories': active,
            'stale_repositories': total - active
        }
