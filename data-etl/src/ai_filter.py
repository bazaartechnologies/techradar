"""
AI-driven technology filtering for strategic tech radar curation.

Post-detection filter that uses AI to:
1. Evaluate strategic value
2. Detect and merge duplicates
3. Consolidate parent-child hierarchies
4. Flag deprecated technologies
"""

import json
import logging
import backoff
from typing import Dict, List, Set, Tuple
from collections import defaultdict
from openai import OpenAI
from openai import OpenAIError

logger = logging.getLogger(__name__)


class AITechnologyFilter:
    """
    AI-powered filter to clean and curate technology list.

    Transforms raw detection results into strategic tech radar by:
    - Removing low-value utilities
    - Merging duplicate variations
    - Consolidating sub-features
    - Flagging deprecated technologies
    """

    # Quadrant names for context
    QUADRANTS = {
        0: "Techniques",
        1: "Tools",
        2: "Platforms",
        3: "Languages & Frameworks"
    }

    # Ring names for context
    RINGS = {
        0: "Adopt",
        1: "Trial",
        2: "Assess",
        3: "Hold"
    }

    def __init__(self, openai_api_key: str, config: dict):
        """
        Initialize AI filter.

        Args:
            openai_api_key: OpenAI API key
            config: Configuration dictionary
        """
        self.client = OpenAI(api_key=openai_api_key)
        self.config = config

        # Get filter config
        filter_config = config.get('filtering', {})
        self.model = filter_config.get('ai_filter', {}).get('model', 'gpt-4o-mini')
        self.enabled = filter_config.get('enabled', True)

        # Auto-ignore rules
        auto_ignore = filter_config.get('auto_ignore', {})
        self.ignore_single_repo = auto_ignore.get('single_repo_technologies', True)
        self.ignore_os_utilities = auto_ignore.get('os_utilities', True)
        self.ignore_dev_conveniences = auto_ignore.get('developer_conveniences', True)

        # AI filter settings
        ai_config = filter_config.get('ai_filter', {})
        self.strategic_include = ai_config.get('strategic_value', {}).get('include_if', ['high', 'medium'])
        self.duplicate_detection = ai_config.get('duplicate_detection', {}).get('enabled', True)
        self.consolidation = ai_config.get('consolidation', {}).get('enabled', True)
        self.deprecation = ai_config.get('deprecation', {}).get('enabled', True)

        # Overrides
        overrides = filter_config.get('overrides', {})
        self.always_include_min_repos = overrides.get('always_include_if_repos_gte', 5)
        self.always_include_names = set(overrides.get('always_include_names', []))

        # Stats
        self.stats = {
            'evaluated': 0,
            'kept': 0,
            'removed': 0,
            'merged': 0,
            'consolidated': 0,
            'ai_calls': 0
        }

    def filter_technologies(self, technologies: List[Dict]) -> Dict:
        """
        Main filtering pipeline.

        Args:
            technologies: List of technology dicts from detection

        Returns:
            Dict with filtering decisions and statistics
        """
        if not self.enabled:
            logger.info("Filtering disabled in config")
            return {
                'keep': technologies,
                'remove': [],
                'merge_groups': [],
                'consolidations': [],
                'deprecated': [],
                'stats': {'filtering_disabled': True}
            }

        logger.info(f"Starting AI filtering for {len(technologies)} technologies")

        # Phase 1: Strategic value evaluation
        logger.info("Phase 1: Evaluating strategic value...")
        strategic_decisions = self._evaluate_all_strategic_value(technologies)

        # Phase 2: Duplicate detection
        logger.info("Phase 2: Detecting duplicates...")
        merge_groups = []
        if self.duplicate_detection:
            merge_groups = self._detect_all_duplicates(technologies)

        # Phase 3: Hierarchy consolidation
        logger.info("Phase 3: Detecting hierarchies...")
        consolidations = []
        if self.consolidation:
            consolidations = self._detect_all_hierarchies(technologies)

        # Phase 4: Deprecation detection
        logger.info("Phase 4: Checking for deprecated technologies...")
        deprecated = []
        if self.deprecation:
            deprecated = self._detect_deprecated(technologies)

        # Compile results
        result = {
            'strategic_decisions': strategic_decisions,
            'merge_groups': merge_groups,
            'consolidations': consolidations,
            'deprecated': deprecated,
            'stats': self.stats
        }

        logger.info(f"Filtering complete. Stats: {self.stats}")
        return result

    def apply_filter_decisions(self, technologies: List[Dict], decisions: Dict) -> List[Dict]:
        """
        Apply filtering decisions to produce final cleaned list.

        Args:
            technologies: Original technology list
            decisions: Filtering decisions from filter_technologies()

        Returns:
            Cleaned technology list
        """
        logger.info("Applying filter decisions...")

        # Create lookup
        tech_lookup = {t['name']: t for t in technologies}

        # Track what to remove
        to_remove = set()

        # 1. Remove low strategic value
        strategic_decisions = decisions.get('strategic_decisions', {})
        for name, decision in strategic_decisions.items():
            if not decision.get('should_include', True):
                to_remove.add(name)
                logger.debug(f"Removing {name}: {decision.get('reason')}")

        # 2. Merge duplicates
        merge_groups = decisions.get('merge_groups', [])
        for group in merge_groups:
            canonical = group['canonical_name']
            candidates = group['merge_candidates']

            # Merge repo counts
            total_repos = sum(tech_lookup[name]['metadata']['repos_count']
                            for name in [canonical] + candidates
                            if name in tech_lookup)

            # Update canonical
            if canonical in tech_lookup:
                tech_lookup[canonical]['metadata']['repos_count'] = total_repos
                tech_lookup[canonical]['metadata']['usage_percentage'] = round(
                    (total_repos / tech_lookup[canonical]['metadata']['total_repos']) * 100, 1
                )
                tech_lookup[canonical]['filtering_metadata'] = {
                    'merged_from': candidates,
                    'ai_decision': group.get('reason', '')
                }

            # Mark candidates for removal
            to_remove.update(candidates)
            logger.info(f"Merged: {canonical} ← {candidates}")

        # 3. Consolidate hierarchies
        consolidations = decisions.get('consolidations', [])
        for consolidation in consolidations:
            parent = consolidation['parent']
            children = consolidation['children']

            # Add sub-features to parent
            if parent in tech_lookup:
                sub_features = []
                for child in children:
                    if child in tech_lookup:
                        repos = tech_lookup[child]['metadata']['repos_count']
                        sub_features.append(f"{child} ({repos} repos)")

                tech_lookup[parent]['sub_features'] = sub_features
                tech_lookup[parent]['filtering_metadata'] = tech_lookup[parent].get('filtering_metadata', {})
                tech_lookup[parent]['filtering_metadata']['consolidated_from'] = children

            # Mark children for removal
            to_remove.update(children)
            logger.info(f"Consolidated: {parent} ← {children}")

        # 4. Flag deprecated
        deprecated = decisions.get('deprecated', [])
        for dep_info in deprecated:
            name = dep_info['name']
            if name in tech_lookup:
                tech_lookup[name]['deprecated'] = True
                tech_lookup[name]['replacement'] = dep_info.get('replacement')
                tech_lookup[name]['deprecation_note'] = dep_info.get('note')
                logger.info(f"Flagged deprecated: {name} → {dep_info.get('replacement')}")

        # 5. Build final list
        final_technologies = []
        for tech in technologies:
            if tech['name'] not in to_remove:
                final_technologies.append(tech_lookup[tech['name']])

        logger.info(f"Final count: {len(final_technologies)} (removed {len(to_remove)})")
        return final_technologies

    def _evaluate_all_strategic_value(self, technologies: List[Dict]) -> Dict[str, Dict]:
        """
        Evaluate strategic value for all technologies.

        Returns:
            Dict mapping tech name to decision
        """
        decisions = {}

        for tech in technologies:
            name = tech['name']
            self.stats['evaluated'] += 1

            # Check overrides first
            if name in self.always_include_names:
                decisions[name] = {
                    'should_include': True,
                    'strategic_value': 'high',
                    'reason': 'Explicitly configured to always include',
                    'confidence': 'high'
                }
                self.stats['kept'] += 1
                continue

            if tech['metadata']['repos_count'] >= self.always_include_min_repos:
                decisions[name] = {
                    'should_include': True,
                    'strategic_value': 'medium',
                    'reason': f"Used in {tech['metadata']['repos_count']} repos (above threshold)",
                    'confidence': 'high'
                }
                self.stats['kept'] += 1
                continue

            # Auto-ignore rules
            if self._should_auto_ignore(tech):
                decisions[name] = {
                    'should_include': False,
                    'strategic_value': 'low',
                    'reason': 'Auto-ignored (utility/single-repo)',
                    'confidence': 'high'
                }
                self.stats['removed'] += 1
                continue

            # AI evaluation
            try:
                decision = self._evaluate_strategic_value(tech)
                decisions[name] = decision

                if decision.get('should_include', True):
                    self.stats['kept'] += 1
                else:
                    self.stats['removed'] += 1

            except Exception as e:
                logger.error(f"Error evaluating {name}: {e}")
                # Default to keeping if AI fails
                decisions[name] = {
                    'should_include': True,
                    'strategic_value': 'unknown',
                    'reason': 'AI evaluation failed, kept by default',
                    'confidence': 'low'
                }
                self.stats['kept'] += 1

        return decisions

    def _should_auto_ignore(self, tech: Dict) -> bool:
        """Check if technology matches auto-ignore rules."""
        name = tech['name'].lower()
        repos_count = tech['metadata']['repos_count']

        # Single repo technologies (unless overridden)
        if self.ignore_single_repo and repos_count == 1:
            return True

        # OS utilities
        if self.ignore_os_utilities:
            os_utils = ['apt-get', 'brew', 'curl', 'wget', 'tar', 'zip', 'unzip', 'grep', 'sed', 'awk']
            if any(util in name for util in os_utils):
                return True

        # Developer conveniences
        if self.ignore_dev_conveniences:
            dev_utils = ['rimraf', 'nodemon', 'npm-run-all', 'cross-env', 'dotenv', 'envsubst']
            if any(util in name for util in dev_utils):
                return True

        return False

    @backoff.on_exception(
        backoff.expo,
        OpenAIError,
        max_tries=2,
        max_time=30
    )
    def _evaluate_strategic_value(self, tech: Dict) -> Dict:
        """
        AI evaluation of single technology's strategic value.

        Returns:
            Dict with decision
        """
        prompt = self._build_strategic_value_prompt(tech)

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a technology strategist evaluating technologies for an enterprise tech radar. Be concise and decisive."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.1,
            max_tokens=300,
            response_format={"type": "json_object"},
            timeout=15
        )

        self.stats['ai_calls'] += 1

        result = json.loads(response.choices[0].message.content)

        # Validate strategic value is in include list
        strategic_value = result.get('strategic_value', 'medium')
        result['should_include'] = strategic_value in self.strategic_include

        return result

    def _detect_all_duplicates(self, technologies: List[Dict]) -> List[Dict]:
        """
        Detect all duplicate technology groups.

        Returns:
            List of merge groups
        """
        # Group similar names
        potential_groups = self._group_similar_names(technologies)

        merge_groups = []
        for group in potential_groups:
            if len(group) > 1:
                try:
                    result = self._detect_duplicates(group)
                    if result.get('are_duplicates', False):
                        merge_groups.append(result)
                        self.stats['merged'] += len(result['merge_candidates'])
                except Exception as e:
                    logger.error(f"Error detecting duplicates for {group}: {e}")

        return merge_groups

    def _group_similar_names(self, technologies: List[Dict]) -> List[List[str]]:
        """
        Group technology names that might be duplicates.

        Uses simple heuristics: case-insensitive matching, prefix matching.
        """
        groups = []
        processed = set()

        tech_names = [t['name'] for t in technologies]

        for name in tech_names:
            if name in processed:
                continue

            # Find similar names
            similar = [name]
            name_lower = name.lower()

            for other in tech_names:
                if other == name or other in processed:
                    continue

                other_lower = other.lower()

                # Case variation
                if name_lower == other_lower:
                    similar.append(other)
                # Prefix/suffix match with space/hyphen
                elif (name_lower in other_lower or other_lower in name_lower) and \
                     abs(len(name) - len(other)) <= 5:
                    similar.append(other)

            if len(similar) > 1:
                groups.append(similar)
                processed.update(similar)

        return groups

    @backoff.on_exception(
        backoff.expo,
        OpenAIError,
        max_tries=2,
        max_time=30
    )
    def _detect_duplicates(self, tech_group: List[str]) -> Dict:
        """AI detection of duplicates in a group."""
        prompt = self._build_duplicate_detection_prompt(tech_group)

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "You are analyzing technology names for duplicates. Be precise and conservative."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.1,
            max_tokens=200,
            response_format={"type": "json_object"},
            timeout=10
        )

        self.stats['ai_calls'] += 1

        return json.loads(response.choices[0].message.content)

    def _detect_all_hierarchies(self, technologies: List[Dict]) -> List[Dict]:
        """Detect parent-child hierarchies across all technologies."""
        # Group by potential parents (look for common prefixes)
        potential_hierarchies = self._find_potential_hierarchies(technologies)

        consolidations = []
        for parent, children in potential_hierarchies.items():
            if len(children) > 0:
                try:
                    result = self._detect_hierarchy(parent, children)
                    if result.get('should_consolidate', False):
                        consolidations.append(result)
                        self.stats['consolidated'] += len(children)
                except Exception as e:
                    logger.error(f"Error detecting hierarchy for {parent}: {e}")

        return consolidations

    def _find_potential_hierarchies(self, technologies: List[Dict]) -> Dict[str, List[str]]:
        """Find potential parent-child relationships based on naming."""
        hierarchies = defaultdict(list)
        tech_names = [t['name'] for t in technologies]

        for name in tech_names:
            # Look for prefix matches (e.g., "Firebase" and "Firebase Crashlytics")
            for other in tech_names:
                if name != other and other.startswith(name + ' '):
                    hierarchies[name].append(other)

        return dict(hierarchies)

    @backoff.on_exception(
        backoff.expo,
        OpenAIError,
        max_tries=2,
        max_time=30
    )
    def _detect_hierarchy(self, parent: str, children: List[str]) -> Dict:
        """AI detection of parent-child relationship."""
        prompt = self._build_hierarchy_detection_prompt(parent, children)

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "You are analyzing technology relationships. Be conservative - only consolidate true sub-features."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.1,
            max_tokens=200,
            response_format={"type": "json_object"},
            timeout=10
        )

        self.stats['ai_calls'] += 1

        result = json.loads(response.choices[0].message.content)
        result['parent'] = parent
        result['children'] = children

        return result

    def _detect_deprecated(self, technologies: List[Dict]) -> List[Dict]:
        """Detect deprecated technologies (batch check common ones)."""
        # Known deprecated technologies
        known_deprecated = {
            'TSLint': {'replacement': 'ESLint', 'note': 'TSLint is deprecated. Migrate to ESLint.'},
            'tslint': {'replacement': 'ESLint', 'note': 'TSLint is deprecated. Migrate to ESLint.'},
        }

        deprecated = []
        for tech in technologies:
            name = tech['name']
            if name in known_deprecated:
                deprecated.append({
                    'name': name,
                    'repos_count': tech['metadata']['repos_count'],
                    **known_deprecated[name]
                })

        return deprecated

    def _build_strategic_value_prompt(self, tech: Dict) -> str:
        """Build prompt for strategic value evaluation."""
        return f"""Evaluate if this technology has strategic value for an enterprise tech radar.

**Technology**: {tech['name']}
**Usage**: {tech['metadata']['repos_count']} repos ({tech['metadata']['usage_percentage']}%)
**Category**: {self.QUADRANTS.get(tech['quadrant'], 'Unknown')}
**Ring**: {self.RINGS.get(tech['ring'], 'Unknown')}

**Consider**:
1. **Architectural Impact**: Affects system design? (YES = high value)
2. **Team Scope**: Multi-team or single-dev convenience? (Multi = higher value)
3. **Decision Weight**: Leadership cares? (YES = high value)
4. **Industry Recognition**: Well-known or obscure? (Well-known = higher value)

**Examples**:
✅ GraphQL → HIGH (API architecture choice)
✅ Kubernetes → HIGH (infrastructure platform)
✅ Jest → MEDIUM (testing standard)
❌ tqdm → LOW (progress bar utility)
❌ curl → LOW (OS utility)

**Respond in JSON**:
{{
  "strategic_value": "high/medium/low",
  "reason": "One sentence explanation",
  "category": "platform/framework/tool/library/utility",
  "confidence": "high/medium/low"
}}"""

    def _build_duplicate_detection_prompt(self, tech_group: List[str]) -> str:
        """Build prompt for duplicate detection."""
        return f"""Are these the same technology with different names?

**Names**: {', '.join(tech_group)}

**Examples**:
✅ SAME: ["AWS ECR", "Amazon ECR", "ECR"]
✅ SAME: ["ESLint", "eslint"]
❌ DIFFERENT: ["React", "React Native"]
❌ DIFFERENT: ["AWS", "AWS CLI"]

**Respond in JSON**:
{{
  "are_duplicates": true/false,
  "canonical_name": "Official standard name",
  "merge_candidates": ["names to merge into canonical"],
  "reason": "Brief explanation",
  "confidence": "high/medium/low"
}}"""

    def _build_hierarchy_detection_prompt(self, parent: str, children: List[str]) -> str:
        """Build prompt for hierarchy detection."""
        return f"""Is this a parent-child relationship where children are sub-features?

**Parent**: {parent}
**Potential Children**: {', '.join(children)}

**Examples**:
✅ CONSOLIDATE: Firebase → [Firebase Crashlytics, Firebase Performance]
✅ CONSOLIDATE: AWS → [AWS CloudFront, AWS Elastic Beanstalk]
❌ KEEP SEPARATE: Docker → [Docker Compose] (both strategic)
❌ KEEP SEPARATE: React → [React Native] (different platforms)

**Respond in JSON**:
{{
  "should_consolidate": true/false,
  "reason": "Brief explanation",
  "confidence": "high/medium/low"
}}"""

    def get_stats(self) -> Dict:
        """Get filtering statistics."""
        return self.stats
