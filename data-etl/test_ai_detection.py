"""
Test script for AI-driven technology detection.

This script tests the new AI detector on sample repos and compares
with legacy detector to validate improvements.
"""

import os
import sys
import json
import logging
from pathlib import Path
from dotenv import load_dotenv
from github import Github

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from ai_detector import AITechnologyDetector
from detector import TechnologyDetector
from config import Config, setup_logging

# Load environment
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_single_repo(repo_name: str, github_token: str, openai_key: str, config: Config):
    """
    Test both detectors on a single repository.

    Args:
        repo_name: Full repo name (org/repo)
        github_token: GitHub token
        openai_key: OpenAI API key
        config: Config object
    """
    logger.info(f"\n{'='*60}")
    logger.info(f"Testing Repository: {repo_name}")
    logger.info(f"{'='*60}")

    # Initialize GitHub
    gh = Github(github_token)
    repo = gh.get_repo(repo_name)

    # Initialize detectors
    legacy_detector = TechnologyDetector()
    ai_detector = AITechnologyDetector(openai_key, config.to_dict())

    # Test legacy detector
    logger.info("\n[LEGACY DETECTOR]")
    try:
        legacy_result = legacy_detector.detect_technologies(repo)
        logger.info("Technologies found:")
        for category, techs in legacy_result.items():
            if techs:
                logger.info(f"  {category}: {sorted(techs)}")
        legacy_count = sum(len(techs) for techs in legacy_result.values())
        logger.info(f"Total: {legacy_count} technologies")
    except Exception as e:
        logger.error(f"Legacy detector failed: {e}")
        legacy_result = {}
        legacy_count = 0

    # Test AI detector
    logger.info("\n[AI DETECTOR]")
    try:
        ai_result = ai_detector.detect_technologies(repo)
        logger.info("Technologies found:")
        for category, techs in ai_result.items():
            if techs:
                logger.info(f"  {category}: {sorted(techs)}")
        ai_count = sum(len(techs) for techs in ai_result.values())
        logger.info(f"Total: {ai_count} technologies")

        # Show AI stats
        stats = ai_detector.get_stats()
        logger.info(f"\nAI Stats: {stats}")
    except Exception as e:
        logger.error(f"AI detector failed: {e}")
        ai_result = {}
        ai_count = 0

    # Compare results
    logger.info("\n[COMPARISON]")

    # Find new discoveries (in AI but not legacy)
    all_legacy = set()
    for techs in legacy_result.values():
        all_legacy.update(techs)

    all_ai = set()
    for techs in ai_result.values():
        all_ai.update(techs)

    new_discoveries = all_ai - all_legacy
    if new_discoveries:
        logger.info(f"✅ NEW discoveries by AI: {sorted(new_discoveries)}")
    else:
        logger.info("No new discoveries")

    # Find missing (in legacy but not AI)
    missing = all_legacy - all_ai
    if missing:
        logger.warning(f"⚠️  Missing in AI: {sorted(missing)}")

    # Summary
    logger.info(f"\nSummary:")
    logger.info(f"  Legacy: {legacy_count} technologies")
    logger.info(f"  AI: {ai_count} technologies")
    logger.info(f"  New discoveries: {len(new_discoveries)}")
    logger.info(f"  Missing: {len(missing)}")

    return {
        'repo': repo_name,
        'legacy_count': legacy_count,
        'ai_count': ai_count,
        'new_discoveries': list(new_discoveries),
        'missing': list(missing),
        'legacy_result': {k: list(v) for k, v in legacy_result.items()},
        'ai_result': {k: list(v) for k, v in ai_result.items()}
    }


def main():
    """Run tests on sample repositories."""
    # Get credentials
    github_token = os.getenv('GITHUB_TOKEN')
    openai_key = os.getenv('OPENAI_API_KEY')

    if not github_token or not openai_key:
        logger.error("Missing GITHUB_TOKEN or OPENAI_API_KEY")
        sys.exit(1)

    # Load config
    config = Config()

    # Test repositories (mix of different tech stacks)
    test_repos = [
        'bazaartechnologies/bazaar-analytic-platform',  # Python/data
        'bazaartechnologies/bazaar-payment-service',    # Java backend
        'bazaartechnologies/nucleus',                   # Frontend
        'bazaartechnologies/terraform-modules',         # Infrastructure
    ]

    # Run tests
    all_results = []
    for repo_name in test_repos:
        try:
            result = test_single_repo(repo_name, github_token, openai_key, config)
            all_results.append(result)
        except Exception as e:
            logger.error(f"Failed to test {repo_name}: {e}")

    # Overall summary
    logger.info(f"\n{'='*60}")
    logger.info("OVERALL SUMMARY")
    logger.info(f"{'='*60}")

    total_legacy = sum(r['legacy_count'] for r in all_results)
    total_ai = sum(r['ai_count'] for r in all_results)
    total_new = sum(len(r['new_discoveries']) for r in all_results)
    total_missing = sum(len(r['missing']) for r in all_results)

    logger.info(f"Repositories tested: {len(all_results)}")
    logger.info(f"Total technologies (legacy): {total_legacy}")
    logger.info(f"Total technologies (AI): {total_ai}")
    logger.info(f"Total new discoveries: {total_new}")
    logger.info(f"Total missing: {total_missing}")

    # Aggregate new discoveries
    all_new = set()
    for r in all_results:
        all_new.update(r['new_discoveries'])

    logger.info(f"\nUnique new technologies discovered by AI:")
    for tech in sorted(all_new):
        logger.info(f"  - {tech}")

    # Check for GraphQL and gRPC
    logger.info(f"\n✅ Key Technologies Check:")
    if 'GraphQL' in all_new or any('graphql' in t.lower() for t in all_new):
        logger.info(f"  ✅ GraphQL DETECTED (was missing before!)")
    else:
        logger.warning(f"  ⚠️  GraphQL not found")

    if 'gRPC' in all_new or any('grpc' in t.lower() for t in all_new):
        logger.info(f"  ✅ gRPC DETECTED (was missing before!)")
    else:
        logger.warning(f"  ⚠️  gRPC not found")

    # Save results
    output_file = Path(__file__).parent / 'test_results_ai_detection.json'
    with open(output_file, 'w') as f:
        json.dump(all_results, f, indent=2)
    logger.info(f"\nDetailed results saved to: {output_file}")


if __name__ == '__main__':
    main()
