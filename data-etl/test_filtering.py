"""
Test script for AI-driven technology filtering.

Tests filtering on existing data.json and shows:
- What gets removed and why
- Duplicate merges
- Hierarchy consolidations
- Strategic value decisions
"""

import os
import sys
import json
import logging
from pathlib import Path
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from ai_filter import AITechnologyFilter
from config import Config

# Load environment
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_data(data_path: str) -> list:
    """Load data.json"""
    with open(data_path, 'r') as f:
        return json.load(f)


def print_section(title: str):
    """Print formatted section header"""
    print(f"\n{'='*70}")
    print(f" {title}")
    print(f"{'='*70}")


def analyze_filtering_results(original: list, decisions: dict, filtered: list):
    """Analyze and display filtering results"""

    print_section("FILTERING SUMMARY")
    print(f"Original technologies: {len(original)}")
    print(f"Filtered technologies: {len(filtered)}")
    print(f"Removed: {len(original) - len(filtered)}")
    print(f"AI calls made: {decisions['stats']['ai_calls']}")

    # Strategic decisions
    print_section("REMOVED TECHNOLOGIES (Low Strategic Value)")
    strategic_decisions = decisions.get('strategic_decisions', {})
    removed = [(name, dec) for name, dec in strategic_decisions.items()
               if not dec.get('should_include', True)]

    if removed:
        print(f"\nTotal removed: {len(removed)}\n")
        for i, (name, decision) in enumerate(removed[:20], 1):  # Show first 20
            print(f"{i}. {name}")
            print(f"   Reason: {decision.get('reason', 'N/A')}")
            print(f"   Strategic value: {decision.get('strategic_value', 'N/A')}")
            print()

        if len(removed) > 20:
            print(f"... and {len(removed) - 20} more")
    else:
        print("None")

    # Merge groups
    print_section("MERGED DUPLICATES")
    merge_groups = decisions.get('merge_groups', [])

    if merge_groups:
        print(f"\nTotal merge groups: {len(merge_groups)}\n")
        for i, group in enumerate(merge_groups, 1):
            print(f"{i}. {group['canonical_name']} ← {group['merge_candidates']}")
            print(f"   Reason: {group.get('reason', 'N/A')}")
            print()
    else:
        print("No duplicates detected")

    # Consolidations
    print_section("CONSOLIDATED HIERARCHIES")
    consolidations = decisions.get('consolidations', [])

    if consolidations:
        print(f"\nTotal consolidations: {len(consolidations)}\n")
        for i, cons in enumerate(consolidations, 1):
            print(f"{i}. {cons['parent']}")
            print(f"   └─ Sub-features: {', '.join(cons['children'])}")
            print(f"   Reason: {cons.get('reason', 'N/A')}")
            print()
    else:
        print("No hierarchies detected")

    # Deprecated
    print_section("DEPRECATED TECHNOLOGIES")
    deprecated = decisions.get('deprecated', [])

    if deprecated:
        print(f"\nTotal deprecated: {len(deprecated)}\n")
        for i, dep in enumerate(deprecated, 1):
            print(f"{i}. {dep['name']} ({dep['repos_count']} repos)")
            print(f"   Replacement: {dep.get('replacement', 'N/A')}")
            print(f"   Note: {dep.get('note', 'N/A')}")
            print()
    else:
        print("No deprecated technologies")

    # Check for key technologies
    print_section("KEY TECHNOLOGIES CHECK")
    filtered_names = {t['name'] for t in filtered}

    key_techs = ['GraphQL', 'gRPC', 'Kubernetes', 'Docker', 'PostgreSQL']
    for tech in key_techs:
        status = "✅ KEPT" if tech in filtered_names else "❌ REMOVED"
        print(f"  {status} - {tech}")


def compare_before_after(original: list, filtered: list):
    """Compare statistics before and after filtering"""

    print_section("BEFORE/AFTER COMPARISON")

    # Count by ring
    def count_by_ring(techs):
        rings = {0: 0, 1: 0, 2: 0, 3: 0}
        for t in techs:
            rings[t['ring']] = rings.get(t['ring'], 0) + 1
        return rings

    original_rings = count_by_ring(original)
    filtered_rings = count_by_ring(filtered)

    print("\nBy Ring:")
    print(f"  Ring 0 (Adopt):  {original_rings[0]:3d} → {filtered_rings[0]:3d}")
    print(f"  Ring 1 (Trial):  {original_rings[1]:3d} → {filtered_rings[1]:3d}")
    print(f"  Ring 2 (Assess): {original_rings[2]:3d} → {filtered_rings[2]:3d}")
    print(f"  Ring 3 (Hold):   {original_rings[3]:3d} → {filtered_rings[3]:3d}")

    # Count by repos
    def count_by_repos(techs):
        counts = {'1': 0, '2-4': 0, '5-9': 0, '10+': 0}
        for t in techs:
            repos = t['metadata']['repos_count']
            if repos == 1:
                counts['1'] += 1
            elif repos <= 4:
                counts['2-4'] += 1
            elif repos <= 9:
                counts['5-9'] += 1
            else:
                counts['10+'] += 1
        return counts

    original_repos = count_by_repos(original)
    filtered_repos = count_by_repos(filtered)

    print("\nBy Usage:")
    print(f"  1 repo:      {original_repos['1']:3d} → {filtered_repos['1']:3d}")
    print(f"  2-4 repos:   {original_repos['2-4']:3d} → {filtered_repos['2-4']:3d}")
    print(f"  5-9 repos:   {original_repos['5-9']:3d} → {filtered_repos['5-9']:3d}")
    print(f"  10+ repos:   {original_repos['10+']:3d} → {filtered_repos['10+']:3d}")


def main():
    """Run filtering test"""
    print_section("AI-DRIVEN TECHNOLOGY FILTERING TEST")

    # Check for data.json
    data_path = Path(__file__).parent.parent / 'data.json'
    if not data_path.exists():
        logger.error(f"data.json not found at: {data_path}")
        logger.error("Run detection first: cd data-etl && python src/main.py")
        return 1

    # Load config
    logger.info("Loading configuration...")
    config = Config()

    # Check API key
    openai_key = os.getenv('OPENAI_API_KEY')
    if not openai_key:
        logger.error("OPENAI_API_KEY not found in environment")
        return 1

    # Load data
    logger.info(f"Loading data from: {data_path}")
    original_data = load_data(str(data_path))
    logger.info(f"Loaded {len(original_data)} technologies")

    # Initialize filter
    logger.info("Initializing AI filter...")
    filter = AITechnologyFilter(openai_key, config.to_dict())

    # Run filtering
    logger.info("Running AI filtering (this may take 1-2 minutes)...")
    print()

    decisions = filter.filter_technologies(original_data)

    logger.info("Applying filter decisions...")
    filtered_data = filter.apply_filter_decisions(original_data, decisions)

    # Analyze results
    analyze_filtering_results(original_data, decisions, filtered_data)

    # Compare before/after
    compare_before_after(original_data, filtered_data)

    # Save filtered output
    filtered_path = data_path.parent / 'data.filtered.json'
    report_path = data_path.parent / 'filtering_report.json'

    logger.info(f"\nSaving filtered data to: {filtered_path}")
    with open(filtered_path, 'w') as f:
        json.dump(filtered_data, f, indent=2, default=str)

    logger.info(f"Saving filtering report to: {report_path}")
    with open(report_path, 'w') as f:
        json.dump(decisions, f, indent=2, default=str)

    print_section("FILTERING COMPLETE")
    print(f"✅ Original:  {data_path}")
    print(f"✅ Filtered:  {filtered_path}")
    print(f"✅ Report:    {report_path}")
    print()
    print("Review the filtered data and report, then use:")
    print("  cp data.filtered.json data.json  # Replace with filtered version")

    return 0


if __name__ == '__main__':
    sys.exit(main())
