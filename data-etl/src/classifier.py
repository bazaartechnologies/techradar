"""
AI-powered technology classification using OpenAI.
"""

import logging
import json
import backoff
from typing import Dict, List, Optional
from openai import OpenAI
from openai import OpenAIError

logger = logging.getLogger(__name__)


class TechnologyClassifier:
    """Classifies technologies using AI."""

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

    def classify_technologies(
        self,
        tech_counts: Dict[str, int],
        total_repos: int,
        repo_details: List[Dict]
    ) -> List[Dict]:
        """
        Classify all technologies.

        Args:
            tech_counts: Dict of tech name -> count of repos
            total_repos: Total number of repositories scanned
            repo_details: List of repository details

        Returns:
            List of classified technology entries
        """
        classified = []
        min_repos = self.config['classification'].get('min_repos', 2)

        for tech_name, count in sorted(tech_counts.items(), key=lambda x: x[1], reverse=True):
            # Skip if below minimum threshold
            if count < min_repos:
                logger.debug(f"Skipping {tech_name} (only {count} repos)")
                continue

            # Skip if matches exclude patterns
            if self._should_exclude(tech_name):
                logger.debug(f"Skipping {tech_name} (matches exclude pattern)")
                continue

            try:
                usage_percentage = (count / total_repos) * 100

                logger.info(f"Classifying {tech_name} ({count}/{total_repos} repos, {usage_percentage:.1f}%)")

                # Classify with AI
                classification = self._classify_single(
                    tech_name,
                    count,
                    total_repos,
                    usage_percentage,
                    repo_details
                )

                if classification:
                    classified.append(classification)

            except Exception as e:
                logger.error(f"Error classifying {tech_name}: {e}")

        return classified

    @backoff.on_exception(
        backoff.expo,
        OpenAIError,
        max_tries=3,
        max_time=60
    )
    def _classify_single(
        self,
        tech_name: str,
        count: int,
        total_repos: int,
        usage_percentage: float,
        repo_details: List[Dict]
    ) -> Optional[Dict]:
        """
        Classify a single technology using AI.

        Args:
            tech_name: Technology name
            count: Number of repos using it
            total_repos: Total repos scanned
            usage_percentage: Percentage of repos using it
            repo_details: Repository details for context

        Returns:
            Classification dict or None
        """
        # Determine ring based on usage
        ring = self._determine_ring(usage_percentage)

        # Build context about repos using this tech
        example_repos = self._get_example_repos(tech_name, repo_details, limit=5)

        # Create prompt for AI
        prompt = self._build_classification_prompt(
            tech_name,
            count,
            total_repos,
            usage_percentage,
            ring,
            example_repos
        )

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a technology expert helping to classify technologies for a tech radar. Provide concise, accurate classifications."
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

            # Validate and build final classification
            return {
                "name": tech_name,
                "quadrant": result.get("quadrant", self._infer_quadrant(tech_name)),
                "ring": ring,
                "description": result.get("description", f"{tech_name} is used in {count} repositories."),
                "metadata": {
                    "repos_count": count,
                    "usage_percentage": round(usage_percentage, 1),
                    "total_repos": total_repos,
                    "confidence": result.get("confidence", "medium"),
                    "ai_model": self.model
                }
            }

        except Exception as e:
            logger.error(f"AI classification failed for {tech_name}: {e}")
            # Fallback to rule-based classification
            return self._fallback_classification(tech_name, count, total_repos, usage_percentage, ring)

    def _build_classification_prompt(
        self,
        tech_name: str,
        count: int,
        total_repos: int,
        usage_percentage: float,
        ring: int,
        example_repos: List[str]
    ) -> str:
        """Build prompt for AI classification."""
        return f"""Classify the technology "{tech_name}" for a tech radar.

**Usage Context:**
- Found in {count} out of {total_repos} repositories ({usage_percentage:.1f}%)
- Suggested ring: {self.RINGS[ring]}
- Example repositories: {', '.join(example_repos) if example_repos else 'N/A'}

**Quadrants:**
0 = Techniques (practices, methodologies like CI/CD, Infrastructure as Code)
1 = Tools (development tools like GitHub Actions, Playwright, testing frameworks)
2 = Platforms (infrastructure, databases, cloud like AWS, Docker, Kubernetes, PostgreSQL)
3 = Languages & Frameworks (like React, Python, Go, TypeScript, Django)

**Rings (based on usage):**
0 = Adopt (70%+): Proven, recommended, high confidence
1 = Trial (40-70%): Worth pursuing, showing promise
2 = Assess (10-40%): Worth exploring, emerging
3 = Hold (<10%): Proceed with caution, limited use

**Your Task:**
Provide a JSON response with:
1. "quadrant": The appropriate quadrant number (0-3)
2. "description": A concise 1-2 sentence description explaining:
   - What the technology is
   - Why it's in the {self.RINGS[ring]} ring based on usage
   - Your recommendation (use, explore, or avoid)
3. "confidence": "high", "medium", or "low" based on how well-known this technology is

**Example Response:**
{{
  "quadrant": 3,
  "description": "JavaScript library for building user interfaces. Found in {usage_percentage:.0f}% of repositories, indicating strong adoption. Recommended for new frontend projects.",
  "confidence": "high"
}}

Respond with valid JSON only."""

    def _determine_ring(self, usage_percentage: float) -> int:
        """
        Determine ring based on usage percentage.

        Args:
            usage_percentage: Percentage of repos using the tech

        Returns:
            Ring number (0-3)
        """
        thresholds = self.config['classification']['thresholds']

        if usage_percentage >= thresholds['adopt'] * 100:
            return 0  # Adopt
        elif usage_percentage >= thresholds['trial'] * 100:
            return 1  # Trial
        elif usage_percentage >= thresholds['assess'] * 100:
            return 2  # Assess
        else:
            return 3  # Hold

    def _infer_quadrant(self, tech_name: str) -> int:
        """
        Infer quadrant from technology name (fallback).

        Args:
            tech_name: Technology name

        Returns:
            Quadrant number (0-3)
        """
        tech_lower = tech_name.lower()

        # Languages & Frameworks
        languages = ['python', 'javascript', 'typescript', 'java', 'go', 'rust', 'php', 'ruby', 'c++', 'c#']
        frameworks = ['react', 'vue', 'angular', 'django', 'flask', 'express', 'next.js', 'rails', 'laravel']

        if any(lang in tech_lower for lang in languages + frameworks):
            return 3

        # Platforms
        platforms = ['docker', 'kubernetes', 'aws', 'azure', 'gcp', 'postgres', 'mysql', 'mongodb', 'redis']
        if any(plat in tech_lower for plat in platforms):
            return 2

        # Tools
        tools = ['webpack', 'vite', 'jest', 'pytest', 'eslint', 'prettier', 'github', 'gitlab', 'jenkins']
        if any(tool in tech_lower for tool in tools):
            return 1

        # Default to Techniques
        return 0

    def _get_example_repos(self, tech_name: str, repo_details: List[Dict], limit: int = 5) -> List[str]:
        """Get example repositories using this technology."""
        example_repos = []

        for repo in repo_details:
            # Check if this repo uses the tech
            for techs in repo['technologies'].values():
                if tech_name in techs:
                    example_repos.append(repo['name'])
                    break

            if len(example_repos) >= limit:
                break

        return example_repos

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
        count: int,
        total_repos: int,
        usage_percentage: float,
        ring: int
    ) -> Dict:
        """Fallback classification when AI fails."""
        return {
            "name": tech_name,
            "quadrant": self._infer_quadrant(tech_name),
            "ring": ring,
            "description": f"{tech_name} is used in {count} repositories ({usage_percentage:.1f}%). Further evaluation recommended.",
            "metadata": {
                "repos_count": count,
                "usage_percentage": round(usage_percentage, 1),
                "total_repos": total_repos,
                "confidence": "low",
                "ai_model": "fallback"
            }
        }
