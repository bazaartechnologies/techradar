#!/usr/bin/env python3
"""
Tech Radar Data ETL - Main Entry Point

Scans GitHub repositories and generates tech radar data using AI.
"""

import sys
import json
import argparse
import logging
from pathlib import Path
from datetime import datetime

from config import Config, setup_logging
from scanner import GitHubScanner
from classifier_enhanced import EnhancedTechnologyClassifier
from ai_filter import AITechnologyFilter
from output_generator import UnifiedOutputGenerator
from progress import ProgressTracker, ProgressDisplay

logger = logging.getLogger(__name__)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Tech Radar Data ETL - Scan GitHub repos and generate tech radar data',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with default config
  python main.py

  # Scan specific organization
  python main.py --org myorg

  # Limit to first 100 repos (fast testing)
  python main.py --limit 100

  # Dry run (no file output)
  python main.py --dry-run

  # Quick test: scan 50 repos in dry-run mode
  python main.py --limit 50 --dry-run

  # Resume from checkpoint
  python main.py --resume

  # Start fresh (clear checkpoint)
  python main.py --fresh

  # Custom config and output
  python main.py --config custom.yaml --output custom.ai.json
        """
    )

    parser.add_argument(
        '--config',
        type=str,
        help='Path to config YAML file (default: config/config.yaml)'
    )

    parser.add_argument(
        '--org',
        type=str,
        help='Override organization to scan (overrides config)'
    )

    parser.add_argument(
        '--output',
        type=str,
        help='Override output file path (overrides config)'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Run scan but do not write output file'
    )

    parser.add_argument(
        '--resume',
        action='store_true',
        help='Resume from checkpoint (skip already scanned repos)'
    )

    parser.add_argument(
        '--fresh',
        action='store_true',
        help='Start fresh (clear checkpoint and rescan all)'
    )

    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='Enable verbose output (DEBUG level)'
    )

    parser.add_argument(
        '--limit',
        type=int,
        help='Limit number of repositories to scan (e.g., --limit 100)'
    )

    return parser.parse_args()




def main():
    """Main entry point."""
    args = parse_args()

    try:
        # Load configuration
        config = Config(args.config)

        # Setup logging
        if args.verbose:
            config.config['logging']['level'] = 'DEBUG'
        setup_logging(config)

        logger.info("=" * 70)
        logger.info("Tech Radar Data ETL")
        logger.info("=" * 70)

        # Override config with CLI args
        if args.org:
            config.config['github']['organizations'] = [args.org]
            logger.info(f"Overriding organization: {args.org}")

        output_path = Path(args.output) if args.output else config.get_output_path()

        # Initialize progress tracker
        # Enabled by default (from config), unless --fresh is used
        checkpoint_enabled = config['checkpoint'].get('enabled', True)
        if args.fresh:
            checkpoint_enabled = False

        progress_tracker = ProgressTracker(
            config.get_checkpoint_path(),
            enabled=checkpoint_enabled,
            resume=args.resume  # Only load checkpoint if --resume flag is used
        )

        if args.fresh:
            progress_tracker.clear()
            logger.info("Starting fresh scan (checkpoint cleared)")
        elif args.resume:
            progress = progress_tracker.get_progress()
            scanned_count = progress['scanned_repos']
            if scanned_count > 0:
                logger.info(f"Resuming scan ({scanned_count} repos already scanned)")
            else:
                logger.info("No previous checkpoint found, starting fresh scan")

        progress_tracker.start_scan()

        # Initialize scanner with progress tracker
        logger.info("Initializing GitHub scanner...")
        scanner = GitHubScanner(
            config.get_github_token(),
            config.to_dict(),
            progress_tracker,
            config.get_openai_key()  # Enable domain detection
        )

        # Set repo limit if specified
        if args.limit:
            scanner.repo_limit = args.limit
            logger.info(f"Limiting scan to {args.limit} repositories")

        # Scan repositories
        logger.info("Scanning repositories...")
        print()

        tech_counts, repo_details = scanner.scan_organizations()

        stats = scanner.get_stats()
        progress_tracker.update_stats(stats)

        logger.info(f"Found {len(tech_counts)} unique technologies")

        if not tech_counts:
            logger.warning("No technologies found! Check your configuration and repository access.")
            return 1

        # Classify technologies with enhanced temporal analysis
        logger.info("Classifying technologies with AI and temporal analysis...")
        classifier = EnhancedTechnologyClassifier(
            config.get_openai_key(),
            config.to_dict()
        )

        total_repos = stats['repos_scanned']
        high_confidence, needs_review = classifier.classify_technologies(
            tech_counts,
            total_repos,
            repo_details
        )

        logger.info(f"Classified {len(high_confidence)} high-confidence + {len(needs_review)} needs-review technologies")

        # Combine for filtering
        all_classified = high_confidence + needs_review

        # Apply AI-driven filtering
        filtered_techs = all_classified
        filtering_report = None

        if config.get('filtering', {}).get('enabled', False):
            logger.info("Applying AI-driven filtering...")
            filter = AITechnologyFilter(config.get_openai_key(), config.to_dict())

            # Get filter decisions
            filter_decisions = filter.filter_technologies(all_classified)

            # Apply transformations
            filtered_techs = filter.apply_filter_decisions(all_classified, filter_decisions)

            # Save filtering report
            filtering_report = {
                'summary': {
                    'original_count': len(all_classified),
                    'filtered_count': len(filtered_techs),
                    'removed_count': len(all_classified) - len(filtered_techs),
                    'ai_calls': filter.stats.get('ai_calls', 0)
                },
                'decisions': filter_decisions,
                'stats': filter.get_stats()
            }

            logger.info(f"Filtering complete: {len(all_classified)} → {len(filtered_techs)} technologies")
            logger.info(f"Removed {len(all_classified) - len(filtered_techs)} low-value technologies")

            # Save filtering report to separate file
            if not args.dry_run:
                report_path = output_path.parent / 'filtering_report.json'
                with open(report_path, 'w') as f:
                    json.dump(filtering_report, f, indent=2, default=str)
                logger.info(f"Filtering report saved to: {report_path}")
        else:
            logger.info("Filtering disabled in config")

        # Separate back into high_confidence and needs_review for output
        high_confidence = [t for t in filtered_techs if not t.get('needs_review', False)]
        needs_review = [t for t in filtered_techs if t.get('needs_review', False)]

        # Generate unified output
        if args.dry_run:
            logger.info("Dry run - skipping file write")

            all_techs = high_confidence + needs_review
            print(f"\n📋 Preview (first 5 technologies):")
            for entry in all_techs[:5]:
                review_status = "⚠️  NEEDS REVIEW" if entry.get('needs_review', False) else "✓ AUTO-APPROVED"
                print(f"\n  {entry['name']} [{review_status}]")
                print(f"    Ring: {entry['ring']} | Quadrant: {entry['quadrant']}")
                print(f"    Confidence: {entry['confidence']}")
                print(f"    Usage: {entry['metadata']['usage_percentage']:.1f}%")
                print(f"    {entry['description'][:80]}...")
                if entry.get('needs_review'):
                    print(f"    Reason: {entry['review_reason']}")
        else:
            output_generator = UnifiedOutputGenerator()
            output_path = output_generator.generate_output(
                high_confidence,
                needs_review,
                config['output'],
                stats
            )

        # Finalize
        progress_tracker.finalize()

        logger.info("Scan completed successfully!")
        return 0

    except KeyboardInterrupt:
        logger.warning("\nScan interrupted by user")
        # Save checkpoint before exit
        try:
            if 'progress_tracker' in locals():
                progress_tracker.finalize()
                logger.info("Progress saved. Resume with: python main.py --resume")
        except Exception as e:
            logger.error(f"Error saving checkpoint: {e}")
        return 130

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        # Save checkpoint on error
        try:
            if 'progress_tracker' in locals():
                progress_tracker.finalize()
                logger.info("Progress saved despite error. Resume with: python main.py --resume")
        except Exception as checkpoint_error:
            logger.error(f"Error saving checkpoint: {checkpoint_error}")

        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting:")
        print("  1. Check your .env file has valid tokens")
        print("  2. Verify organization name is correct")
        print("  3. Check logs in logs/scan.log")
        print("  4. Run with --verbose for detailed output")
        if 'progress_tracker' in locals() and progress_tracker.enabled:
            print("  5. Resume scan with: python main.py --resume")
        return 1


if __name__ == '__main__':
    sys.exit(main())
