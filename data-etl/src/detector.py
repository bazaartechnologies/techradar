"""
Technology detection from repository files.
"""

import json
import re
import logging
from typing import Dict, List, Set
from github.Repository import Repository
from github.GithubException import GithubException

logger = logging.getLogger(__name__)


class TechnologyDetector:
    """Detects technologies used in repositories."""

    # File patterns to look for
    TECH_FILES = {
        'package.json': 'detect_node',
        'requirements.txt': 'detect_python',
        'Pipfile': 'detect_python_pipfile',
        'pyproject.toml': 'detect_python_pyproject',
        'go.mod': 'detect_go',
        'Cargo.toml': 'detect_rust',
        'pom.xml': 'detect_java_maven',
        'build.gradle': 'detect_java_gradle',
        'Gemfile': 'detect_ruby',
        'composer.json': 'detect_php',
        'Dockerfile': 'detect_docker',
        '.github/workflows': 'detect_github_actions',
    }

    def __init__(self):
        """Initialize detector."""
        self.detected_cache = {}

    def detect_technologies(self, repo: Repository) -> Dict[str, Set[str]]:
        """
        Detect all technologies in a repository.

        Args:
            repo: GitHub repository object

        Returns:
            Dict mapping tech categories to sets of technology names
        """
        technologies = {
            'languages': set(),
            'frameworks': set(),
            'tools': set(),
            'platforms': set(),
        }

        try:
            # Detect from GitHub's language detection
            languages = repo.get_languages()
            for lang in languages.keys():
                technologies['languages'].add(lang)

            # Detect from specific files
            for file_pattern, detect_method in self.TECH_FILES.items():
                try:
                    if hasattr(self, detect_method):
                        detected = getattr(self, detect_method)(repo)
                        for category, techs in detected.items():
                            technologies[category].update(techs)
                except GithubException as e:
                    if e.status != 404:  # File not found is expected
                        logger.debug(f"Error checking {file_pattern} in {repo.name}: {e}")
                except Exception as e:
                    logger.debug(f"Error detecting from {file_pattern}: {e}")

        except Exception as e:
            logger.error(f"Error detecting technologies in {repo.name}: {e}")

        return technologies

    def detect_node(self, repo: Repository) -> Dict[str, Set[str]]:
        """Detect Node.js/JavaScript technologies."""
        techs = {'frameworks': set(), 'tools': set()}

        try:
            content = repo.get_contents("package.json")
            package_json = json.loads(content.decoded_content.decode())

            # Check dependencies
            deps = package_json.get('dependencies', {})
            dev_deps = package_json.get('devDependencies', {})
            all_deps = {**deps, **dev_deps}

            # Frameworks
            if 'react' in all_deps:
                techs['frameworks'].add('React')
            if 'next' in all_deps:
                techs['frameworks'].add('Next.js')
            if 'vue' in all_deps:
                techs['frameworks'].add('Vue.js')
            if 'angular' in all_deps or '@angular/core' in all_deps:
                techs['frameworks'].add('Angular')
            if 'svelte' in all_deps:
                techs['frameworks'].add('Svelte')
            if 'express' in all_deps:
                techs['frameworks'].add('Express.js')
            if 'nestjs' in all_deps or '@nestjs/core' in all_deps:
                techs['frameworks'].add('NestJS')

            # Tools
            if 'typescript' in all_deps:
                techs['tools'].add('TypeScript')
            if 'webpack' in all_deps:
                techs['tools'].add('Webpack')
            if 'vite' in all_deps:
                techs['tools'].add('Vite')
            if 'jest' in all_deps:
                techs['tools'].add('Jest')
            if 'playwright' in all_deps or '@playwright/test' in all_deps:
                techs['tools'].add('Playwright')
            if 'eslint' in all_deps:
                techs['tools'].add('ESLint')
            if 'prettier' in all_deps:
                techs['tools'].add('Prettier')
            if 'tailwindcss' in all_deps:
                techs['frameworks'].add('Tailwind CSS')

        except Exception as e:
            logger.debug(f"Error parsing package.json: {e}")

        return techs

    def detect_python(self, repo: Repository) -> Dict[str, Set[str]]:
        """Detect Python technologies from requirements.txt."""
        techs = {'frameworks': set(), 'tools': set()}

        try:
            content = repo.get_contents("requirements.txt")
            requirements = content.decoded_content.decode().split('\n')

            for line in requirements:
                line = line.strip().lower()
                if not line or line.startswith('#'):
                    continue

                # Extract package name (before ==, >=, etc.)
                package = re.split('[=<>!]', line)[0].strip()

                # Frameworks
                if 'django' in package:
                    techs['frameworks'].add('Django')
                elif 'flask' in package:
                    techs['frameworks'].add('Flask')
                elif 'fastapi' in package:
                    techs['frameworks'].add('FastAPI')
                elif 'streamlit' in package:
                    techs['frameworks'].add('Streamlit')
                elif 'pytorch' in package or 'torch' in package:
                    techs['frameworks'].add('PyTorch')
                elif 'tensorflow' in package:
                    techs['frameworks'].add('TensorFlow')

                # Tools
                elif 'pytest' in package:
                    techs['tools'].add('pytest')
                elif 'black' in package:
                    techs['tools'].add('Black')
                elif 'mypy' in package:
                    techs['tools'].add('mypy')

        except Exception as e:
            logger.debug(f"Error parsing requirements.txt: {e}")

        return techs

    def detect_python_pipfile(self, repo: Repository) -> Dict[str, Set[str]]:
        """Detect Python technologies from Pipfile."""
        techs = {'tools': set()}
        try:
            repo.get_contents("Pipfile")
            techs['tools'].add('Pipenv')
        except:
            pass
        return techs

    def detect_python_pyproject(self, repo: Repository) -> Dict[str, Set[str]]:
        """Detect Python technologies from pyproject.toml."""
        techs = {'tools': set()}
        try:
            repo.get_contents("pyproject.toml")
            techs['tools'].add('Poetry')
        except:
            pass
        return techs

    def detect_go(self, repo: Repository) -> Dict[str, Set[str]]:
        """Detect Go technologies."""
        techs = {'languages': set()}
        try:
            repo.get_contents("go.mod")
            techs['languages'].add('Go')
        except:
            pass
        return techs

    def detect_rust(self, repo: Repository) -> Dict[str, Set[str]]:
        """Detect Rust technologies."""
        techs = {'languages': set()}
        try:
            repo.get_contents("Cargo.toml")
            techs['languages'].add('Rust')
        except:
            pass
        return techs

    def detect_java_maven(self, repo: Repository) -> Dict[str, Set[str]]:
        """Detect Java/Maven technologies."""
        techs = {'languages': set(), 'tools': set()}
        try:
            repo.get_contents("pom.xml")
            techs['languages'].add('Java')
            techs['tools'].add('Maven')
        except:
            pass
        return techs

    def detect_java_gradle(self, repo: Repository) -> Dict[str, Set[str]]:
        """Detect Java/Gradle technologies."""
        techs = {'languages': set(), 'tools': set()}
        try:
            repo.get_contents("build.gradle")
            techs['languages'].add('Java')
            techs['tools'].add('Gradle')
        except:
            pass
        return techs

    def detect_ruby(self, repo: Repository) -> Dict[str, Set[str]]:
        """Detect Ruby technologies."""
        techs = {'languages': set(), 'frameworks': set()}
        try:
            content = repo.get_contents("Gemfile")
            gemfile = content.decoded_content.decode()
            techs['languages'].add('Ruby')
            if 'rails' in gemfile.lower():
                techs['frameworks'].add('Ruby on Rails')
        except:
            pass
        return techs

    def detect_php(self, repo: Repository) -> Dict[str, Set[str]]:
        """Detect PHP technologies."""
        techs = {'languages': set(), 'frameworks': set(), 'tools': set()}
        try:
            content = repo.get_contents("composer.json")
            composer = json.loads(content.decoded_content.decode())
            techs['languages'].add('PHP')
            techs['tools'].add('Composer')

            deps = composer.get('require', {})
            if 'laravel/framework' in deps:
                techs['frameworks'].add('Laravel')
            if 'symfony/symfony' in deps:
                techs['frameworks'].add('Symfony')

        except:
            pass
        return techs

    def detect_docker(self, repo: Repository) -> Dict[str, Set[str]]:
        """Detect Docker usage."""
        techs = {'platforms': set()}
        try:
            repo.get_contents("Dockerfile")
            techs['platforms'].add('Docker')
        except:
            pass
        return techs

    def detect_github_actions(self, repo: Repository) -> Dict[str, Set[str]]:
        """Detect GitHub Actions usage."""
        techs = {'tools': set()}
        try:
            workflows = repo.get_contents(".github/workflows")
            if workflows:
                techs['tools'].add('GitHub Actions')
        except:
            pass
        return techs

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
