"""
AI-powered domain detection for repositories.

Analyzes repository structure, files, and content to intelligently
determine the engineering domain without hardcoded patterns.
"""

import logging
import json
from typing import Dict, Set, Optional, List
from github.Repository import Repository
from github.GithubException import GithubException
from openai import OpenAI

logger = logging.getLogger(__name__)


class DomainDetector:
    """AI-powered repository domain detector."""

    # Standard domain categories (can be extended)
    STANDARD_DOMAINS = [
        'mobile',
        'backend',
        'frontend',
        'infrastructure',
        'data',
        'ml',
        'library',
        'tooling',
    ]

    def __init__(self, openai_api_key: str, config: Optional[dict] = None):
        """
        Initialize domain detector.

        Args:
            openai_api_key: OpenAI API key for AI analysis
            config: Optional configuration dict
        """
        self.client = OpenAI(api_key=openai_api_key)
        self.config = config or {}
        self.detection_cache = {}

        # Get AI model from config
        self.model = self.config.get('ai', {}).get('model', 'gpt-4o-mini')

    def detect_domain(
        self,
        repo: Repository,
        technologies: Dict[str, Set[str]] = None
    ) -> Dict[str, any]:
        """
        Detect the domain of a repository using AI analysis.

        Args:
            repo: GitHub repository object
            technologies: Optional dict of detected technologies

        Returns:
            Dict with domain classification:
            {
                'domain': 'backend',
                'confidence': 0.95,
                'reasoning': 'This is a microservice...',
                'all_domains': {'backend': 0.95, 'infrastructure': 0.3}
            }
        """
        # Cache check
        cache_key = repo.full_name
        if cache_key in self.detection_cache:
            return self.detection_cache[cache_key]

        try:
            # Gather repository signals
            signals = self._gather_repo_signals(repo, technologies)

            # Use AI to classify
            result = self._ai_classify_domain(repo.name, signals)

            # Cache result
            self.detection_cache[cache_key] = result
            return result

        except Exception as e:
            logger.error(f"Error detecting domain for {repo.name}: {e}")
            return {
                'domain': 'unknown',
                'confidence': 0.0,
                'reasoning': f'Error during detection: {str(e)}',
                'all_domains': {}
            }

    def _gather_repo_signals(
        self,
        repo: Repository,
        technologies: Dict[str, Set[str]] = None
    ) -> Dict[str, any]:
        """
        Gather all signals from repository for domain detection.

        Args:
            repo: Repository object
            technologies: Optional detected technologies

        Returns:
            Dict with repository signals
        """
        signals = {
            'name': repo.name,
            'description': repo.description or '',
            'root_files': [],
            'root_directories': [],
            'file_types': {},
            'technologies': technologies or {},
            'readme_snippet': '',
            'topics': []
        }

        try:
            # Get root directory structure
            contents = repo.get_contents("")

            for item in contents[:50]:  # Limit to avoid rate limits
                if item.type == 'dir':
                    signals['root_directories'].append(item.name)
                else:
                    signals['root_files'].append(item.name)

                    # Track file extensions
                    if '.' in item.name:
                        ext = item.name.split('.')[-1]
                        signals['file_types'][ext] = signals['file_types'].get(ext, 0) + 1

        except GithubException as e:
            logger.debug(f"Could not fetch contents for {repo.name}: {e}")

        # Get README snippet
        try:
            readme = repo.get_readme()
            readme_content = readme.decoded_content.decode('utf-8', errors='ignore')
            # Get first 500 chars for context
            signals['readme_snippet'] = readme_content[:500]
        except:
            pass

        # Get topics
        try:
            signals['topics'] = repo.get_topics()
        except:
            pass

        return signals

    def _ai_classify_domain(self, repo_name: str, signals: Dict) -> Dict[str, any]:
        """
        Use AI to classify repository domain based on signals.

        Args:
            repo_name: Repository name
            signals: Gathered repository signals

        Returns:
            Classification result dict
        """
        # Prepare prompt
        prompt = self._build_classification_prompt(repo_name, signals)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert at analyzing software repositories and determining their engineering domain.

Analyze the provided repository information and classify it into one of these domains:
- mobile: Mobile applications (iOS, Android, cross-platform)
- backend: Backend services, APIs, microservices
- frontend: Web frontends, SPAs, user interfaces
- infrastructure: Infrastructure as code, DevOps, deployment
- data: Data pipelines, ETL, analytics, warehousing
- ml: Machine learning, AI models, inference services
- library: Shared libraries, SDKs, frameworks
- tooling: Developer tools, CLI applications, scripts

Return ONLY a valid JSON object with this exact structure:
{
  "domain": "backend",
  "confidence": 0.95,
  "reasoning": "Brief explanation of why this classification was chosen",
  "all_domains": {
    "backend": 0.95,
    "infrastructure": 0.3
  }
}

Rules:
- confidence is 0.0 to 1.0
- reasoning should be 1-2 sentences
- all_domains should include any domain with confidence > 0.2
- Use "unknown" if truly unclear (confidence < 0.4)"""
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=300
            )

            # Parse response
            content = response.choices[0].message.content.strip()

            # Extract JSON from potential markdown code blocks
            if '```json' in content:
                content = content.split('```json')[1].split('```')[0].strip()
            elif '```' in content:
                content = content.split('```')[1].split('```')[0].strip()

            result = json.loads(content)

            # Validate result
            if not all(k in result for k in ['domain', 'confidence', 'reasoning']):
                raise ValueError("Invalid response format from AI")

            return result

        except Exception as e:
            logger.error(f"Error in AI classification for {repo_name}: {e}")
            return {
                'domain': 'unknown',
                'confidence': 0.0,
                'reasoning': f'AI classification failed: {str(e)}',
                'all_domains': {}
            }

    def _build_classification_prompt(self, repo_name: str, signals: Dict) -> str:
        """
        Build prompt for AI classification.

        Args:
            repo_name: Repository name
            signals: Repository signals

        Returns:
            Formatted prompt string
        """
        # Convert sets to lists for JSON serialization
        tech_summary = {}
        for category, techs in signals.get('technologies', {}).items():
            if techs:
                tech_summary[category] = list(techs)

        prompt_parts = [
            f"Repository: {repo_name}",
            ""
        ]

        if signals.get('description'):
            prompt_parts.append(f"Description: {signals['description']}")
            prompt_parts.append("")

        if signals.get('root_directories'):
            dirs = ', '.join(signals['root_directories'][:10])
            prompt_parts.append(f"Root Directories: {dirs}")

        if signals.get('root_files'):
            files = ', '.join(signals['root_files'][:15])
            prompt_parts.append(f"Root Files: {files}")

        if signals.get('file_types'):
            # Show top file types
            sorted_types = sorted(
                signals['file_types'].items(),
                key=lambda x: x[1],
                reverse=True
            )[:8]
            types_str = ', '.join(f"{ext}({count})" for ext, count in sorted_types)
            prompt_parts.append(f"File Types: {types_str}")

        if tech_summary:
            prompt_parts.append(f"\nTechnologies:")
            for category, techs in tech_summary.items():
                if techs:
                    prompt_parts.append(f"  {category}: {', '.join(techs[:5])}")

        if signals.get('topics'):
            prompt_parts.append(f"\nTopics: {', '.join(signals['topics'])}")

        if signals.get('readme_snippet'):
            prompt_parts.append(f"\nREADME Snippet:")
            prompt_parts.append(signals['readme_snippet'])

        return '\n'.join(prompt_parts)

    def batch_detect_domains(
        self,
        repo_data: List[Dict]
    ) -> Dict[str, Dict]:
        """
        Detect domains for multiple repositories efficiently.

        Args:
            repo_data: List of dicts with 'repo' and 'technologies'

        Returns:
            Dict mapping repo names to domain results
        """
        results = {}

        for item in repo_data:
            repo = item['repo']
            technologies = item.get('technologies')

            domain_result = self.detect_domain(repo, technologies)
            results[repo.full_name] = domain_result

            logger.info(
                f"  {repo.name}: {domain_result['domain']} "
                f"(confidence: {domain_result['confidence']:.2f})"
            )

        return results

    def get_domain_statistics(self, domain_results: Dict[str, Dict]) -> Dict:
        """
        Calculate statistics across detected domains.

        Args:
            domain_results: Dict mapping repo names to domain classifications

        Returns:
            Statistics dict
        """
        from collections import Counter

        domains = [result['domain'] for result in domain_results.values()]
        domain_counts = Counter(domains)
        total = len(domains)

        stats = {
            'total_repos': total,
            'by_domain': {},
            'avg_confidence': sum(r['confidence'] for r in domain_results.values()) / total if total > 0 else 0,
        }

        for domain, count in domain_counts.items():
            stats['by_domain'][domain] = {
                'count': count,
                'percentage': round(count / total * 100, 1),
                'avg_confidence': round(
                    sum(
                        r['confidence']
                        for r in domain_results.values()
                        if r['domain'] == domain
                    ) / count,
                    2
                )
            }

        return stats
