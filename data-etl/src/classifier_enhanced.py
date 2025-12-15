"""
Enhanced AI-powered technology classification with temporal analysis and confidence scoring.
"""

import logging
import json
import backoff
from typing import Dict, List, Optional, Tuple
from openai import OpenAI
from openai import OpenAIError

from temporal_analyzer import TemporalAnalyzer

logger = logging.getLogger(__name__)


class EnhancedTechnologyClassifier:
    """Classifies technologies using AI with temporal analysis and confidence scoring."""

    # Quadrant definitions
    QUADRANTS = {
        0: "Techniques",        # Practices, methodologies
        1: "Tools",            # Development tools, testing frameworks
        2: "Platforms",        # Infrastructure, databases, cloud
        3: "Languages & Frameworks"  # Programming languages and frameworks
    }

    # Ring definitions
    RINGS = {
        0: "Adopt",   # Proven, recommended
        1: "Trial",   # Worth pursuing
        2: "Assess",  # Worth exploring
        3: "Hold"     # Proceed with caution
    }

    def __init__(self, api_key: str, config: dict):
        """
        Initialize classifier.

        Args:
            api_key: OpenAI API key
            config: Configuration dictionary
        """
        self.client = OpenAI(api_key=api_key)
        self.config = config
        self.model = config['openai']['model']
        self.max_tokens = config['openai'].get('max_tokens', 1000)
        self.temperature = config['openai'].get('temperature', 0.3)
        self.temporal_analyzer = TemporalAnalyzer()

    def classify_technologies(
        self,
        tech_counts: Dict[str, int],
        total_repos: int,
        repo_details: List[Dict]
    ) -> Tuple[List[Dict], List[Dict]]:
        """
        Classify all technologies with confidence-based splitting.

        Args:
            tech_counts: Dict of tech name -> count of repos
            total_repos: Total number of repositories scanned
            repo_details: List of repository details

        Returns:
            Tuple of (high_confidence_list, needs_review_list)
        """
        high_confidence = []
        needs_review = []
        default_min_repos = self.config['classification'].get('min_repos', 2)
        min_repos_by_domain = self.config['classification'].get('min_repos_by_domain', {})

        for tech_name, count in sorted(tech_counts.items(), key=lambda x: x[1], reverse=True):
            # Domain-aware min_repos check
            should_include = self._meets_domain_threshold(
                tech_name, count, repo_details,
                default_min_repos, min_repos_by_domain
            )

            if not should_include:
                logger.debug(f"Skipping {tech_name} (doesn't meet domain thresholds)")
                continue

            # Skip if matches exclude patterns
            if self._should_exclude(tech_name):
                logger.debug(f"Skipping {tech_name} (matches exclude pattern)")
                continue

            try:
                usage_percentage = (count / total_repos) * 100

                logger.info(f"Classifying {tech_name} ({count}/{total_repos} repos, {usage_percentage:.1f}%)")

                # Get temporal analysis
                temporal_data = self.temporal_analyzer.analyze_technology(
                    tech_name,
                    repo_details
                )

                # Classify with enhanced logic
                classification = self._classify_single_enhanced(
                    tech_name,
                    count,
                    total_repos,
                    usage_percentage,
                    temporal_data,
                    repo_details
                )

                if classification:
                    # Split based on confidence
                    if classification['confidence'] >= 0.75:
                        high_confidence.append(classification)
                    else:
                        needs_review.append(classification)

            except Exception as e:
                logger.error(f"Error classifying {tech_name}: {e}")

        return high_confidence, needs_review

    def _classify_single_enhanced(
        self,
        tech_name: str,
        count: int,
        total_repos: int,
        usage_percentage: float,
        temporal_data: Dict,
        repo_details: List[Dict]
    ) -> Optional[Dict]:
        """
        Classify a single technology with temporal analysis.

        Args:
            tech_name: Technology name
            count: Number of repos using it
            total_repos: Total repos scanned
            usage_percentage: Percentage of repos using it
            temporal_data: Temporal analysis data
            repo_details: Repository details for context

        Returns:
            Classification dict or None
        """
        # Calculate scores
        usage_score = usage_percentage / 100
        recency_score = temporal_data['recency_score']
        activity_score = temporal_data['activity_score']

        # Smart ring decision
        ring, ring_confidence = self._smart_ring_decision(
            usage_score,
            recency_score,
            activity_score,
            temporal_data['trend'],
            temporal_data
        )

        # Get AI classification
        ai_result = self._get_ai_classification(
            tech_name,
            usage_percentage,
            temporal_data,
            ring
        )

        # Convert AI confidence string to float
        ai_confidence_str = ai_result.get('ai_confidence', 'medium')
        ai_confidence_float = self._convert_ai_confidence(ai_confidence_str)

        # Calculate overall confidence
        confidence = self._calculate_confidence(
            usage_score,
            recency_score,
            activity_score,
            temporal_data,
            ring_confidence,
            ai_confidence_float
        )

        # Build decision factors
        decision_factors = self._build_decision_factors(
            tech_name,
            usage_percentage,
            temporal_data,
            ring
        )

        # Determine if needs review
        needs_review, review_reason = self._determine_review_need(
            confidence,
            temporal_data,
            usage_score,
            ring
        )

        # Add domain-specific analysis if available
        domain_breakdown = None
        if 'by_domain' in temporal_data and temporal_data['by_domain']:
            domain_breakdown = self._analyze_domain_breakdown(
                tech_name,
                temporal_data['by_domain']
            )

        metadata = {
            "repos_count": count,
            "usage_percentage": round(usage_percentage, 1),
            "total_repos": total_repos,
            "ai_confidence": ai_result.get('ai_confidence', 'medium'),
            "ai_model": self.model,
            "temporal_data": temporal_data,
            "usage_score": round(usage_score, 3),
            "recency_score": round(recency_score, 3),
            "activity_score": round(activity_score, 3)
        }

        if domain_breakdown:
            metadata["domain_breakdown"] = domain_breakdown

        return {
            "name": tech_name,
            "quadrant": ai_result.get("quadrant", self._infer_quadrant(tech_name)),
            "ring": ring,
            "description": ai_result.get("description", f"{tech_name} is used in {count} repositories."),
            "confidence": round(confidence, 3),
            "metadata": metadata,
            "decision_factors": decision_factors,
            "needs_review": needs_review,
            "review_reason": review_reason if needs_review else None
        }

    def _smart_ring_decision(
        self,
        usage: float,
        recency: float,
        activity: float,
        trend: str,
        temporal_data: Dict
    ) -> Tuple[int, float]:
        """
        Smart ring decision based on multiple factors including domain dominance.

        Returns:
            Tuple of (ring, confidence)
        """
        # Check for domain-specific dominance first
        # A technology can be ADOPT if it's dominant in any major domain
        if 'by_domain' in temporal_data and temporal_data['by_domain']:
            for domain, metrics in temporal_data['by_domain'].items():
                domain_repos = metrics.get('total_repos', 0)
                domain_activity = metrics.get('activity_score', 0)

                # Significant domain presence: 20+ repos
                if domain_repos >= 20:
                    # Calculate domain usage (we need to estimate total repos in this domain)
                    # Use heuristic: if 50+ repos in domain → likely dominant
                    # OR high activity with substantial presence

                    # ADOPT: Dominant in a major domain with reasonable activity
                    if (domain_repos >= 50 and domain_activity >= 0.5) or \
                       (domain_repos >= 70 and domain_activity >= 0.4):
                        confidence = 0.9
                        logger.info(f"Domain dominance detected: {domain_repos} repos in {domain} domain, {domain_activity:.1%} active")
                        return 0, confidence

                    # TRIAL: Strong presence in domain with high activity
                    if domain_repos >= 30 and domain_activity >= 0.65:
                        confidence = 0.8
                        logger.info(f"Strong domain presence: {domain_repos} repos in {domain} domain")
                        return 1, confidence

        # Fallback to global metrics if no domain dominance

        # ADOPT: High global usage + Active (more realistic thresholds)
        if (usage >= 0.4 and activity >= 0.5) or \
           (usage >= 0.35 and activity >= 0.6):
            confidence = 0.9
            return 0, confidence

        # TRIAL: Growing adoption OR moderate usage with high activity
        if (recency >= 0.2 and activity >= 0.6 and trend == 'GROWING') or \
           (usage >= 0.25 and activity >= 0.75):
            confidence = 0.8
            return 1, confidence

        # HOLD: Low usage + Abandoned OR explicitly abandoned trend
        if (usage < 0.1 and activity < 0.3) or trend == 'ABANDONED':
            confidence = 0.85
            return 3, confidence

        # ASSESS: Everything else (medium confidence)
        confidence = 0.6
        return 2, confidence

    def _calculate_confidence(
        self,
        usage_score: float,
        recency_score: float,
        activity_score: float,
        temporal_data: Dict,
        ring_confidence: float,
        ai_confidence: float
    ) -> float:
        """
        Calculate overall confidence score (0-1).

        Higher confidence = clearer signals
        """
        # Strong signals increase confidence
        strong_signals = 0
        total_signals = 0

        # Check usage clarity
        total_signals += 1
        if usage_score > 0.7 or usage_score < 0.1:
            strong_signals += 1  # Very high or very low is clear

        # Check activity clarity
        total_signals += 1
        if activity_score > 0.8 or activity_score < 0.2:
            strong_signals += 1  # Very active or very stale is clear

        # Check trend clarity
        total_signals += 1
        if temporal_data['trend'] in ['GROWING', 'ABANDONED']:
            strong_signals += 1  # Clear trends

        # Check repo count
        total_signals += 1
        if temporal_data['total_repos'] >= 5:
            strong_signals += 1  # More data = higher confidence

        signal_confidence = strong_signals / total_signals

        # Weighted average
        confidence = (
            signal_confidence * 0.4 +
            ring_confidence * 0.4 +
            ai_confidence * 0.2
        )

        return min(confidence, 1.0)

    def _build_decision_factors(
        self,
        tech_name: str,
        usage_percentage: float,
        temporal_data: Dict,
        ring: int
    ) -> List[str]:
        """Build list of decision factors for review."""
        factors = []

        # Usage factor
        if usage_percentage >= 50:
            factors.append(f"✓ High usage ({usage_percentage:.1f}%)")
        elif usage_percentage >= 20:
            factors.append(f"• Medium usage ({usage_percentage:.1f}%)")
        else:
            factors.append(f"✗ Low usage ({usage_percentage:.1f}%)")

        # Recency factor
        if temporal_data['recent_repos'] > 0:
            factors.append(f"✓ {temporal_data['recent_repos']} new repos in last 6 months")
        else:
            factors.append(f"✗ No new adoption in last 6 months")

        # Activity factor
        active_pct = (temporal_data['active_repos'] / temporal_data['total_repos'] * 100) if temporal_data['total_repos'] > 0 else 0
        if active_pct >= 70:
            factors.append(f"✓ {active_pct:.0f}% of repos actively maintained")
        elif active_pct >= 40:
            factors.append(f"• {active_pct:.0f}% of repos actively maintained")
        else:
            factors.append(f"✗ Only {active_pct:.0f}% of repos actively maintained")

        # Trend factor
        trend_emoji = {'GROWING': '📈', 'STABLE': '➡', 'DECLINING': '📉', 'ABANDONED': '💀'}
        factors.append(f"{trend_emoji.get(temporal_data['trend'], '?')} Trend: {temporal_data['trend']}")

        return factors

    def _determine_review_need(
        self,
        confidence: float,
        temporal_data: Dict,
        usage_score: float,
        ring: int
    ) -> Tuple[bool, Optional[str]]:
        """
        Determine if technology needs human review.

        Returns:
            Tuple of (needs_review, reason)
        """
        # Low confidence always needs review
        if confidence < 0.75:
            return True, "Low confidence classification"

        # Conflicting signals
        if temporal_data['trend'] == 'DECLINING' and usage_score > 0.3:
            return True, "High usage but declining trend"

        if temporal_data['trend'] == 'GROWING' and usage_score < 0.1:
            return True, "Low usage but growing trend"

        # Low repo count
        if temporal_data['total_repos'] < 3:
            return True, "Limited data (fewer than 3 repos)"

        # All clear
        return False, None

    @backoff.on_exception(
        backoff.expo,
        OpenAIError,
        max_tries=3,
        max_time=60
    )
    def _get_ai_classification(
        self,
        tech_name: str,
        usage_percentage: float,
        temporal_data: Dict,
        suggested_ring: int
    ) -> Dict:
        """Get AI classification with temporal context."""
        prompt = self._build_enhanced_prompt(
            tech_name,
            usage_percentage,
            temporal_data,
            suggested_ring
        )

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a technology expert helping to classify technologies for a tech radar. Provide strategic, industry-informed classifications."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)
            return result

        except Exception as e:
            logger.error(f"AI classification failed for {tech_name}: {e}")
            return self._fallback_classification(tech_name, usage_percentage, suggested_ring)

    def _build_enhanced_prompt(
        self,
        tech_name: str,
        usage_percentage: float,
        temporal_data: Dict,
        suggested_ring: int
    ) -> str:
        """Build enhanced prompt with temporal context."""
        ring_name = self.RINGS[suggested_ring]

        return f"""Classify the technology "{tech_name}" for a tech radar.

**Our Usage:**
- Found in {temporal_data['total_repos']} repositories ({usage_percentage:.1f}%)
- Recent adoption: {temporal_data['recent_repos']} repos in last 6 months
- Active repos: {temporal_data['active_repos']} out of {temporal_data['total_repos']}
- Trend: {temporal_data['trend']}
- Suggested ring: {ring_name}

**Quadrants:**
0 = Techniques (practices, methodologies like CI/CD, DevOps practices)
1 = Tools (development tools like Maven, GitHub Actions, Jest)
2 = Platforms (infrastructure like Docker, AWS, Kubernetes, databases)
3 = Languages & Frameworks (like Java, React, Python, Kotlin)

**Rings (STRATEGIC, not just usage-based):**
0 = ADOPT: Mature, proven, industry standard. Recommend for production.
1 = TRIAL: Promising, worth pursuing. Try in new projects.
2 = ASSESS: Emerging, experimental. Worth exploring.
3 = HOLD: Legacy, deprecated, or better alternatives exist.

**Your Task:**
Provide JSON with:
1. "quadrant": The appropriate quadrant (0-3)
2. "description": 1-2 sentences explaining what it is and why it's in {ring_name}
3. "ai_confidence": "high", "medium", or "low"

**Consider:**
- Industry standards (not just our usage)
- Technology maturity and ecosystem
- Better alternatives available?
- Is low usage due to being new or obsolete?

Respond with valid JSON only."""

    def _infer_quadrant(self, tech_name: str) -> int:
        """Infer quadrant from technology name (fallback)."""
        tech_lower = tech_name.lower()

        # Languages & Frameworks
        languages = ['python', 'javascript', 'typescript', 'java', 'go', 'rust', 'php', 'ruby', 'kotlin', 'c++', 'c#']
        frameworks = ['react', 'vue', 'angular', 'django', 'flask', 'express', 'next.js', 'rails', 'laravel']

        if any(lang in tech_lower for lang in languages + frameworks):
            return 3

        # Platforms
        platforms = ['docker', 'kubernetes', 'aws', 'azure', 'gcp', 'postgres', 'mysql', 'mongodb', 'redis']
        if any(plat in tech_lower for plat in platforms):
            return 2

        # Tools
        tools = ['webpack', 'vite', 'jest', 'pytest', 'eslint', 'prettier', 'github', 'maven', 'gradle']
        if any(tool in tech_lower for tool in tools):
            return 1

        # Default to Techniques
        return 0

    def _convert_ai_confidence(self, ai_confidence: str) -> float:
        """Convert AI confidence string to float."""
        mapping = {
            'high': 0.9,
            'medium': 0.6,
            'low': 0.3
        }
        return mapping.get(ai_confidence.lower(), 0.5)

    def _meets_domain_threshold(
        self,
        tech_name: str,
        total_count: int,
        repo_details: List[Dict],
        default_min_repos: int,
        min_repos_by_domain: Dict[str, int]
    ) -> bool:
        """
        Check if technology meets domain-aware minimum repo threshold.

        Infrastructure technologies are centralized (1 repo = mature).
        Application technologies are distributed (multiple repos = mature).

        Args:
            tech_name: Technology name
            total_count: Total repos using this tech
            repo_details: List of repo detail dicts
            default_min_repos: Default minimum repos threshold
            min_repos_by_domain: Domain-specific thresholds

        Returns:
            True if meets threshold in any domain or globally
        """
        # If meets global threshold, include regardless of domain
        if total_count >= default_min_repos:
            return True

        # Check domain-specific thresholds
        # Count repos per domain for this technology
        domain_counts = {}

        for repo in repo_details:
            # Check if this repo uses this technology
            repo_techs = repo.get('technologies', {})
            has_tech = False

            for category, techs in repo_techs.items():
                if tech_name in techs:
                    has_tech = True
                    break

            if has_tech:
                # Domain is a dict: {'domain': 'backend', 'confidence': 0.95, ...}
                domain_data = repo.get('domain', {})
                domain = domain_data.get('domain', 'unknown') if domain_data else 'unknown'
                domain_counts[domain] = domain_counts.get(domain, 0) + 1

        # Check if meets threshold in any domain
        for domain, count in domain_counts.items():
            threshold = min_repos_by_domain.get(domain, default_min_repos)

            if count >= threshold:
                logger.info(
                    f"✓ {tech_name} meets {domain} domain threshold "
                    f"({count} repos >= {threshold} required)"
                )
                return True

        # Log why it was filtered
        domain_info = ", ".join([f"{d}:{c}" for d, c in domain_counts.items()])
        logger.debug(
            f"✗ {tech_name} below thresholds (total:{total_count}, by domain: {domain_info})"
        )

        return False

    def _should_exclude(self, tech_name: str) -> bool:
        """Check if technology should be excluded."""
        import fnmatch

        exclude_patterns = self.config['classification'].get('exclude_patterns', [])
        for pattern in exclude_patterns:
            if fnmatch.fnmatch(tech_name.lower(), pattern.lower()):
                return True
        return False

    def _fallback_classification(
        self,
        tech_name: str,
        usage_percentage: float,
        ring: int
    ) -> Dict:
        """Fallback classification when AI fails."""
        return {
            "quadrant": self._infer_quadrant(tech_name),
            "description": f"{tech_name} is used in {usage_percentage:.1f}% of repositories. Further evaluation recommended.",
            "ai_confidence": "low"
        }

    def _analyze_domain_breakdown(
        self,
        tech_name: str,
        by_domain: Dict
    ) -> Dict:
        """
        Analyze technology classification per domain.

        Args:
            tech_name: Technology name
            by_domain: Domain-specific metrics from temporal analyzer

        Returns:
            Dict with domain-specific ring suggestions
        """
        domain_classifications = {}

        for domain, metrics in by_domain.items():
            # Calculate domain-specific ring
            # For domain-specific analysis, we use normalized repo count as usage proxy
            # This provides a relative weight (more repos = higher usage signal)
            # Normalize to 0-1 scale where 10+ repos = 1.0
            usage_score = min(metrics['total_repos'] / 10.0, 1.0)
            recency_score = metrics['recency_score']
            activity_score = metrics['activity_score']
            trend = metrics['trend']

            # Use smart ring decision for this domain
            ring, confidence = self._smart_ring_decision(
                usage_score,
                recency_score,
                activity_score,
                trend,
                metrics
            )

            domain_classifications[domain] = {
                'suggested_ring': ring,
                'ring_name': self.RINGS[ring],
                'confidence': round(confidence, 2),
                'total_repos': metrics['total_repos'],
                'recent_repos': metrics['recent_repos'],
                'activity_score': metrics['activity_score'],
                'trend': trend
            }

        return domain_classifications
