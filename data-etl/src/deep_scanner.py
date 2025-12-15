"""
Tree-based deep scanning for infrastructure repositories.

Uses shallow clone + tree command to analyze repository structure
and identify technologies without hardcoded patterns.
"""

import os
import json
import logging
import tempfile
import shutil
import subprocess
from typing import Dict, List, Set
from openai import OpenAI

logger = logging.getLogger(__name__)


class DeepScanner:
    """
    Deep scanner using repository tree analysis.

    Completely organization-agnostic - works with any repo structure.
    """

    def __init__(self, openai_api_key: str, config: Dict):
        """
        Initialize deep scanner.

        Args:
            openai_api_key: OpenAI API key for AI analysis
            config: Configuration dictionary
        """
        self.client = OpenAI(api_key=openai_api_key)
        self.config = config
        self.model = config.get('openai', {}).get('model', 'gpt-4o-mini')

        # Get deep scan config
        self.deep_scan_config = config.get('deep_scan', {})
        self.tree_max_depth = self.deep_scan_config.get('tree', {}).get('max_depth', 6)
        self.tree_ignore = self.deep_scan_config.get('tree', {}).get('ignore_patterns', [
            '.git', 'node_modules', '.terraform', '__pycache__', '*.pyc'
        ])

    def should_deep_scan(self, repo_name: str) -> bool:
        """
        Check if repository should be deep scanned.

        Args:
            repo_name: Repository name

        Returns:
            True if repo is in deep_scan list
        """
        if not self.deep_scan_config.get('enabled', False):
            return False

        deep_scan_repos = self.deep_scan_config.get('repositories', [])
        return repo_name in deep_scan_repos

    def deep_scan_repository(self, repo) -> Set[str]:
        """
        Deep scan a repository using tree-based analysis.

        Args:
            repo: GitHub repository object

        Returns:
            Set of discovered technologies
        """
        logger.info(f"🔍 Deep scanning {repo.name}...")

        temp_dir = None
        try:
            # 1. Shallow clone
            temp_dir = self._shallow_clone(repo)

            # 2. Generate tree
            tree_content = self._generate_tree(temp_dir, repo.name)

            # 3. AI analyzes tree
            technologies = self._ai_analyze_tree(repo.name, tree_content)

            logger.info(f"✅ Deep scan found {len(technologies)} technologies in {repo.name}")
            return technologies

        except Exception as e:
            logger.error(f"Error deep scanning {repo.name}: {e}")
            return set()

        finally:
            # Always cleanup
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)

    def _shallow_clone(self, repo) -> str:
        """
        Shallow clone repository to temp directory.

        Args:
            repo: GitHub repository object

        Returns:
            Path to cloned repository
        """
        temp_dir = tempfile.mkdtemp(prefix=f'scan_{repo.name}_')

        logger.info(f"Cloning {repo.name} to {temp_dir}...")

        try:
            result = subprocess.run([
                'git', 'clone',
                '--depth', '1',              # Shallow clone (only latest commit)
                '--single-branch',           # Only default branch
                '--no-tags',                 # Skip tags
                '--quiet',
                repo.clone_url,
                temp_dir
            ], capture_output=True, text=True, timeout=120)  # 2 minutes should be plenty

            if result.returncode != 0:
                raise Exception(f"Git clone failed: {result.stderr}")

            logger.info(f"✓ Cloned {repo.name}")
            return temp_dir

        except subprocess.TimeoutExpired:
            raise Exception(f"Git clone timeout for {repo.name}")
        except Exception as e:
            # Cleanup on failure
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
            raise e

    def _generate_tree(self, repo_path: str, repo_name: str) -> str:
        """
        Generate repository tree structure.

        Simple approach: Generate full tree at configured depth.
        If too large for AI (>100K chars ~= 130K tokens), reduce depth and retry.
        Let AI discover everything - no hardcoded patterns.

        Args:
            repo_path: Path to cloned repository
            repo_name: Repository name

        Returns:
            Tree structure as string
        """
        logger.info(f"Generating tree for {repo_name}...")

        # Build ignore pattern for tree command
        ignore_pattern = '|'.join(self.tree_ignore)

        # Start with configured depth, reduce if needed
        depth = self.tree_max_depth
        max_attempts = 4

        for attempt in range(max_attempts):
            try:
                result = subprocess.run([
                    'tree',
                    '-a',                    # Show all files
                    '-I', ignore_pattern,    # Ignore patterns
                    '--dirsfirst',           # Directories first
                    '-L', str(depth),        # Current depth
                    '--noreport',            # No summary
                    repo_path
                ], capture_output=True, text=True, timeout=30)

                if result.returncode != 0:
                    logger.warning(f"tree command failed, using fallback")
                    return self._fallback_tree(repo_path)

                tree_content = result.stdout

                # Check if within token limits
                # 128K token limit, ~1.3 tokens/char, so ~98K chars max
                # Use 80K to be safe with prompt
                max_chars = 80000

                if len(tree_content) <= max_chars:
                    logger.info(f"✓ Generated tree at depth {depth} ({len(tree_content)} chars)")
                    return tree_content

                # Too large, reduce depth and retry
                if attempt < max_attempts - 1:
                    depth = max(3, depth - 1)
                    logger.info(f"Tree too large ({len(tree_content)} chars), retrying with depth={depth}")
                else:
                    # Last attempt - truncate but warn
                    logger.warning(f"Tree still large at depth {depth}, truncating to {max_chars} chars")
                    return tree_content[:max_chars] + "\n\n... (tree truncated - large repository) ..."

            except subprocess.TimeoutExpired:
                logger.warning(f"tree command timeout, using fallback")
                return self._fallback_tree(repo_path)
            except FileNotFoundError:
                logger.warning(f"tree command not found, using fallback")
                return self._fallback_tree(repo_path)
            except Exception as e:
                logger.warning(f"Tree generation failed: {e}, using fallback")
                return self._fallback_tree(repo_path)

        # Shouldn't reach here, but fallback just in case
        return self._fallback_tree(repo_path)

    def _fallback_tree(self, repo_path: str) -> str:
        """
        Fallback tree generation using os.walk.

        Args:
            repo_path: Path to repository

        Returns:
            Tree-like structure as string
        """
        tree_lines = []

        for root, dirs, files in os.walk(repo_path):
            # Skip ignored directories
            dirs[:] = [d for d in dirs if not any(
                d.startswith(ignore.rstrip('*'))
                for ignore in self.tree_ignore
            )]

            # Calculate depth
            depth = root.replace(repo_path, '').count(os.sep)
            if depth >= self.tree_max_depth:
                dirs.clear()  # Stop going deeper
                continue

            # Format directory
            indent = '│   ' * depth
            folder = os.path.basename(root)
            if folder:
                tree_lines.append(f"{indent}├── {folder}/")

            # Format files
            subindent = '│   ' * (depth + 1)
            for file in sorted(files)[:50]:  # Limit files per directory
                tree_lines.append(f"{subindent}├── {file}")

        return '\n'.join(tree_lines)

    def _ai_analyze_tree(self, repo_name: str, tree_content: str) -> Set[str]:
        """
        Use AI to analyze repository tree and identify technologies.

        Args:
            repo_name: Repository name
            tree_content: Tree structure as string

        Returns:
            Set of discovered technology names
        """
        prompt = f"""You are an expert at analyzing repository structures to identify technologies and tools.

Analyze this repository tree and identify ALL technologies, tools, frameworks, and patterns being used.

Repository: {repo_name}

Tree structure:
```
{tree_content}
```

Instructions:
1. Analyze directory names to infer tools and services (e.g., "prometheus/" suggests Prometheus)
2. Analyze file extensions to identify technologies (e.g., "*.tf" suggests Terraform)
3. Analyze file names to detect tools and frameworks (e.g., "Chart.yaml" suggests Helm)
4. Identify infrastructure patterns from structure
5. Identify deployment patterns from naming conventions
6. Look for security, monitoring, and CI/CD tools from any indicators
7. Infer cloud providers and services from context (but don't assume)

Guidelines:
- Be comprehensive - identify everything you can infer from the structure
- Use directory names as primary signals
- Use file patterns as secondary signals
- Infer services from common naming patterns (but mark confidence appropriately)
- Note architectural patterns from directory structure
- Include both explicit (clearly named) and implicit (reasonably inferred) technologies
- Do NOT assume specific platforms unless clearly indicated in the tree

Return a JSON object:
{{
  "technologies": [
    {{
      "name": "Technology Name",
      "category": "infrastructure|kubernetes|security|monitoring|cicd|database|cloud|container|language|other",
      "confidence": "high|medium|low",
      "evidence": "What in the tree indicates this technology"
    }}
  ],
  "patterns": [
    {{
      "type": "deployment|architecture|organization",
      "description": "Pattern description",
      "evidence": "What indicates this pattern"
    }}
  ]
}}

Examples of what to look for (but don't limit to these):
- Infrastructure as Code: Terraform (.tf), CloudFormation (.yaml with Resources:), Pulumi
- Kubernetes: Helm (Chart.yaml), Kustomize (kustomization.yaml), manifests (.yaml in k8s dirs)
- Security: Trivy (.trivyignore), pre-commit hooks, policy directories
- Monitoring: Prometheus, Grafana, Loki (from directory names)
- CI/CD: GitHub Actions (.github/workflows), GitLab CI, Jenkins
- Containers: Dockerfile, docker-compose.yaml
- Languages: Identify from file extensions (.py, .js, .go, .java, etc.)

Be thorough and unbiased - this is the ONLY information you'll receive about this repository.
Only include technologies you can reasonably infer from the tree structure.
"""

        # Retry logic for API calls
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are an expert at analyzing repository structures and identifying technologies from directory trees. You have deep knowledge of DevOps, cloud infrastructure, Kubernetes, security tools, and software engineering practices across all platforms and ecosystems. Always return valid JSON."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.3,
                    max_tokens=3000  # Increased for large repos
                )

                content = response.choices[0].message.content

                # Log raw response for debugging (first 500 chars)
                logger.debug(f"AI response preview: {content[:500]}...")

                # Try to parse JSON
                try:
                    result = json.loads(content)
                except json.JSONDecodeError as je:
                    # Log the error location
                    logger.warning(f"JSON parse error at position {je.pos}: {je.msg}")
                    logger.debug(f"Content around error: {content[max(0, je.pos-100):je.pos+100]}")

                    # Try to extract JSON from response if it's wrapped in markdown
                    if '```json' in content or '```' in content:
                        import re
                        json_match = re.search(r'```(?:json)?\s*(.*?)\s*```', content, re.DOTALL)
                        if json_match:
                            try:
                                result = json.loads(json_match.group(1))
                                logger.info("✓ Extracted JSON from markdown wrapper")
                            except:
                                raise je
                        else:
                            raise je
                    else:
                        # Try to fix common JSON issues
                        # Remove trailing commas
                        fixed_content = re.sub(r',\s*}', '}', content)
                        fixed_content = re.sub(r',\s*]', ']', fixed_content)
                        try:
                            result = json.loads(fixed_content)
                            logger.info("✓ Fixed JSON formatting issues")
                        except:
                            raise je

                # Extract technology names
                technologies = set()
                for tech in result.get('technologies', []):
                    tech_name = tech.get('name')
                    confidence = tech.get('confidence', 'low')

                    # Log discovery with evidence
                    logger.info(f"  Found: {tech_name} ({confidence} confidence) - {tech.get('evidence', 'N/A')[:100]}")

                    # Only include medium+ confidence
                    if confidence in ['high', 'medium']:
                        technologies.add(tech_name)

                # Log patterns discovered
                for pattern in result.get('patterns', [])[:3]:  # Limit to top 3 patterns
                    logger.info(f"  Pattern: {pattern.get('description', 'N/A')[:80]}")

                return technologies

            except json.JSONDecodeError as je:
                logger.warning(f"JSON parse error on attempt {attempt + 1}/{max_retries}: {je}")

                # Save failed response for debugging
                if attempt == max_retries - 1:
                    debug_file = f"logs/deep_scan_failed_{repo_name}.json"
                    try:
                        os.makedirs('logs', exist_ok=True)
                        with open(debug_file, 'w') as f:
                            f.write(content)
                        logger.error(f"Saved failed response to {debug_file} for debugging")
                    except:
                        pass

                if attempt < max_retries - 1:
                    logger.info(f"Retrying in 2 seconds...")
                    import time
                    time.sleep(2)
                else:
                    logger.error(f"AI analysis failed for {repo_name} after {max_retries} attempts: Invalid JSON")
                    return set()

            except Exception as e:
                logger.error(f"AI analysis failed for {repo_name} on attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    logger.info(f"Retrying in 2 seconds...")
                    import time
                    time.sleep(2)
                else:
                    return set()
