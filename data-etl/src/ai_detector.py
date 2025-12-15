"""
AI-driven technology detection using OpenAI.

Replaces hardcoded detection with intelligent, agnostic discovery.
"""

import json
import logging
import backoff
from typing import Dict, List, Set, Optional
from github.Repository import Repository
from github.GithubException import GithubException
from openai import OpenAI
from openai import OpenAIError

logger = logging.getLogger(__name__)


class AITechnologyDetector:
    """
    AI-driven technology detector that discovers technologies dynamically.

    Architecture:
    - Phase 1: AI triages file tree to identify relevant files
    - Phase 2: AI analyzes file contents to extract technologies
    - Phase 3: Returns structured technology data
    """

    def __init__(self, openai_api_key: str, config: dict):
        """
        Initialize AI detector.

        Args:
            openai_api_key: OpenAI API key
            config: Configuration dictionary
        """
        self.client = OpenAI(api_key=openai_api_key)
        self.config = config

        # Get AI detection config
        ai_config = config.get('detection', {}).get('ai_detection', {})
        self.phase1_model = ai_config.get('phase1_model', 'gpt-4o-mini')
        self.phase2_model = ai_config.get('phase2_model', 'gpt-4o-mini')
        self.max_files_per_repo = ai_config.get('max_files_per_repo', 10)
        self.max_file_size = ai_config.get('max_file_size_kb', 100) * 1024  # Convert to bytes
        self.file_tree_max_depth = ai_config.get('file_tree_max_depth', 3)

        # Caching
        self.cache_enabled = ai_config.get('cache_results', True)
        self.cache = {}

        # Stats
        self.stats = {
            'phase1_calls': 0,
            'phase2_calls': 0,
            'cache_hits': 0,
            'errors': 0
        }

    def detect_technologies(self, repo: Repository) -> Dict[str, Set[str]]:
        """
        Main entry point - detects technologies in repository using AI.

        Args:
            repo: GitHub repository object

        Returns:
            Dict mapping tech categories to sets of technology names
        """
        try:
            # Check cache
            if self.cache_enabled and repo.full_name in self.cache:
                logger.debug(f"Cache hit for {repo.name}")
                self.stats['cache_hits'] += 1
                return self.cache[repo.full_name]

            # Phase 1: AI triage - which files should we read?
            logger.debug(f"Phase 1: Triaging {repo.name}")
            relevant_files = self._phase1_triage(repo)

            if not relevant_files:
                logger.debug(f"No relevant files found in {repo.name}")
                return self._empty_result()

            # Phase 2: AI deep analysis - extract technologies from files
            logger.debug(f"Phase 2: Analyzing {len(relevant_files)} files in {repo.name}")
            result = self._phase2_deep_analysis(repo, relevant_files)

            # Convert to expected format
            technologies = self._format_result(result)

            # Cache result
            if self.cache_enabled:
                self.cache[repo.full_name] = technologies

            return technologies

        except Exception as e:
            logger.error(f"AI detection failed for {repo.name}: {e}")
            self.stats['errors'] += 1
            return self._empty_result()

    @backoff.on_exception(
        backoff.expo,
        OpenAIError,
        max_tries=2,
        max_time=30
    )
    def _phase1_triage(self, repo: Repository) -> List[str]:
        """
        Phase 1: AI analyzes file tree and selects relevant files.

        Args:
            repo: Repository object

        Returns:
            List of file paths to analyze
        """
        try:
            # Get file tree
            file_tree = self._get_file_tree(repo)

            if not file_tree:
                return []

            # Build triage prompt
            prompt = self._build_triage_prompt(repo.name, file_tree)

            # Call AI
            response = self.client.chat.completions.create(
                model=self.phase1_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a technology detection expert. Analyze repository structures and identify files that contain technology information."
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

            self.stats['phase1_calls'] += 1

            # Parse response
            result = json.loads(response.choices[0].message.content)
            relevant_files = result.get('relevant_files', [])

            # Limit files
            if len(relevant_files) > self.max_files_per_repo:
                logger.debug(f"Limiting {len(relevant_files)} files to {self.max_files_per_repo}")
                relevant_files = relevant_files[:self.max_files_per_repo]

            logger.debug(f"Phase 1 selected {len(relevant_files)} files: {result.get('rationale', 'N/A')}")
            return relevant_files

        except Exception as e:
            logger.error(f"Phase 1 triage failed for {repo.name}: {e}")
            raise

    @backoff.on_exception(
        backoff.expo,
        OpenAIError,
        max_tries=2,
        max_time=30
    )
    def _phase2_deep_analysis(self, repo: Repository, files: List[str]) -> Dict:
        """
        Phase 2: AI analyzes file contents and extracts technologies.

        Args:
            repo: Repository object
            files: List of file paths to analyze

        Returns:
            Dict with technologies, evidence, and confidence
        """
        try:
            # Fetch file contents
            file_contents = self._fetch_file_contents(repo, files)

            if not file_contents:
                return {}

            # Build analysis prompt
            prompt = self._build_analysis_prompt(repo.name, file_contents)

            # Call AI
            response = self.client.chat.completions.create(
                model=self.phase2_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a technology detection expert. Analyze code files and extract ALL technologies used."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,
                max_tokens=800,
                response_format={"type": "json_object"},
                timeout=20
            )

            self.stats['phase2_calls'] += 1

            # Parse response
            result = json.loads(response.choices[0].message.content)

            logger.debug(f"Phase 2 found {len(result.get('technologies', {}))} technology categories")
            if result.get('evidence'):
                logger.debug(f"Evidence: {list(result['evidence'].keys())}")

            return result

        except Exception as e:
            logger.error(f"Phase 2 analysis failed for {repo.name}: {e}")
            raise

    def _get_file_tree(self, repo: Repository) -> List[str]:
        """
        Get repository file tree (paths only) up to max_depth.

        Args:
            repo: Repository object

        Returns:
            List of file paths
        """
        try:
            # Get repository contents (root level)
            contents = repo.get_contents("")
            file_tree = []

            # BFS to build tree up to max_depth
            queue = [(item, 1) for item in contents]

            while queue and len(file_tree) < 200:  # Limit to 200 files max (optimized for speed)
                item, depth = queue.pop(0)

                # Add to tree
                file_tree.append(item.path)

                # Recurse into directories if within depth limit
                if item.type == "dir" and depth < self.file_tree_max_depth:
                    try:
                        sub_contents = repo.get_contents(item.path)
                        for sub_item in sub_contents:
                            queue.append((sub_item, depth + 1))
                    except GithubException:
                        pass  # Skip inaccessible directories

            return file_tree

        except Exception as e:
            logger.error(f"Error getting file tree for {repo.name}: {e}")
            return []

    def _fetch_file_contents(self, repo: Repository, paths: List[str]) -> Dict[str, str]:
        """
        Fetch content of specific files.

        Args:
            repo: Repository object
            paths: List of file paths to fetch

        Returns:
            Dict mapping file path to content
        """
        file_contents = {}

        for path in paths:
            try:
                content_file = repo.get_contents(path)

                # Skip if file too large
                if content_file.size > self.max_file_size:
                    logger.debug(f"Skipping {path} (too large: {content_file.size} bytes)")
                    continue

                # Decode content
                content = content_file.decoded_content.decode('utf-8', errors='ignore')
                file_contents[path] = content

            except GithubException as e:
                logger.debug(f"Could not fetch {path}: {e}")
            except Exception as e:
                logger.debug(f"Error reading {path}: {e}")

        return file_contents

    def _build_triage_prompt(self, repo_name: str, file_tree: List[str]) -> str:
        """Build Phase 1 triage prompt."""
        # Format file tree nicely
        tree_display = "\n".join(f"  {path}" for path in file_tree[:50])  # Limit display for speed
        if len(file_tree) > 50:
            tree_display += f"\n  ... and {len(file_tree) - 50} more files"

        return f"""You are analyzing the repository structure to identify technology indicators.

**Repository**: {repo_name}

**File Tree** (up to {self.file_tree_max_depth} levels deep):
{tree_display}

**Your Task**: Identify which files contain technology information.

**Look for**:
1. **Dependency Manifests**: package.json, pom.xml, build.gradle, go.mod, Cargo.toml, requirements.txt, Pipfile, pyproject.toml, composer.json, Gemfile, etc.
2. **Configuration Files**: Dockerfile, docker-compose.yml, .github/workflows/*.yml, *.tf (terraform), k8s/*.yaml, kubernetes/*.yaml
3. **Schema Files**: *.graphql, *.gql, *.proto, schema.sql, migrations/*
4. **Framework Config**: next.config.js, nuxt.config.js, angular.json, tsconfig.json, jest.config.js
5. **Build Tools**: Makefile, webpack.config.js, vite.config.ts, rollup.config.js

**Respond in JSON**:
{{
  "relevant_files": ["path/to/file1", "path/to/file2"],
  "rationale": "Brief explanation of what technologies you expect to find"
}}

**Important**:
- Select ONLY files that definitively indicate technologies
- Prioritize root-level dependency manifests (package.json, pom.xml, etc.)
- Include schema/config files if they indicate specific technologies (*.graphql, *.proto)
- Limit to {self.max_files_per_repo} most important files
- Paths must exactly match the file tree provided"""

    def _build_analysis_prompt(self, repo_name: str, file_contents: Dict[str, str]) -> str:
        """Build Phase 2 analysis prompt."""
        # Format file contents
        files_display = ""
        for path, content in file_contents.items():
            # Truncate large files (reduced for speed)
            truncated_content = content[:2000] + "..." if len(content) > 2000 else content
            files_display += f"\n\n--- File: {path} ---\n{truncated_content}"

        return f"""You are analyzing repository files to extract ALL technologies.

**Repository**: {repo_name}

**Files Analyzed**:{files_display}

**Your Task**: Extract ALL technologies from these files.

**Respond in JSON**:
{{
  "technologies": {{
    "languages": ["TypeScript", "Python"],
    "frameworks": ["React", "Apollo GraphQL", "FastAPI"],
    "tools": ["Jest", "gRPC", "ESLint", "Docker", "Webpack"],
    "platforms": ["Node.js", "PostgreSQL", "Redis", "Kubernetes"]
  }},
  "evidence": {{
    "React": "react in package.json dependencies",
    "GraphQL": "schema.graphql defines types Query and Mutation",
    "gRPC": "services.proto defines gRPC service definitions",
    "PostgreSQL": "pg package in dependencies"
  }},
  "confidence": "high"
}}

**Categories**:
- **languages**: Programming languages (Python, JavaScript, TypeScript, Go, Java, Kotlin, Rust, etc.)
- **frameworks**: Application frameworks (React, Vue, Angular, Django, Flask, FastAPI, Express, Spring Boot, etc.)
- **tools**: Development tools (Jest, Pytest, ESLint, Webpack, Vite, gRPC, Protocol Buffers, Maven, Gradle, etc.)
- **platforms**: Infrastructure & services (Docker, Kubernetes, PostgreSQL, MySQL, Redis, MongoDB, RabbitMQ, Kafka, AWS, etc.)

**Important**:
- Be comprehensive - include ALL technologies found
- Use canonical names (e.g., "PostgreSQL" not "postgres", "GraphQL" not "graphql", "TypeScript" not "typescript")
- Infer technologies from file types (*.proto → Protocol Buffers, *.graphql → GraphQL)
- Include package managers and build tools (npm, Maven, Gradle, Make)
- Provide specific evidence for each technology
- Confidence: "high" if explicit, "medium" if inferred, "low" if uncertain"""

    def _format_result(self, ai_result: Dict) -> Dict[str, Set[str]]:
        """
        Convert AI result to expected format.

        Args:
            ai_result: AI response dict

        Returns:
            Dict with categories as keys and sets of technology names
        """
        if not ai_result or 'technologies' not in ai_result:
            return self._empty_result()

        technologies = ai_result['technologies']

        # Convert lists to sets
        return {
            'languages': set(technologies.get('languages', [])),
            'frameworks': set(technologies.get('frameworks', [])),
            'tools': set(technologies.get('tools', [])),
            'platforms': set(technologies.get('platforms', []))
        }

    def _empty_result(self) -> Dict[str, Set[str]]:
        """Return empty result structure."""
        return {
            'languages': set(),
            'frameworks': set(),
            'tools': set(),
            'platforms': set()
        }

    def aggregate_technologies(self, all_repo_techs: List[Dict[str, Set[str]]]) -> Dict[str, int]:
        """
        Aggregate technologies across all repositories.

        Args:
            all_repo_techs: List of technology dicts from each repo

        Returns:
            Dict mapping technology name to count of repos using it
        """
        tech_counts = {}

        for repo_techs in all_repo_techs:
            # Flatten all categories
            all_techs = set()
            for category_techs in repo_techs.values():
                all_techs.update(category_techs)

            # Count occurrences
            for tech in all_techs:
                tech_counts[tech] = tech_counts.get(tech, 0) + 1

        return tech_counts

    def get_stats(self) -> Dict:
        """Get detection statistics."""
        return {
            **self.stats,
            'cache_size': len(self.cache)
        }
