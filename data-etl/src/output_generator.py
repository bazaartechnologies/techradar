"""
Unified output generator for data.ai.json with review metadata
"""

import json
import logging
from pathlib import Path
from typing import List, Dict

logger = logging.getLogger(__name__)


class UnifiedOutputGenerator:
    """Generates unified data.ai.json with review metadata for all technologies."""

    def generate_output(
        self,
        high_confidence: List[Dict],
        needs_review: List[Dict],
        output_config: Dict,
        stats: Dict
    ) -> Path:
        """
        Generate unified output file with all technologies.

        Args:
            high_confidence: Technologies with high confidence
            needs_review: Technologies needing review
            output_config: Output configuration
            stats: Scanning statistics

        Returns:
            Path to output file
        """
        # Combine all technologies
        all_technologies = self._prepare_unified_output(
            high_confidence,
            needs_review,
            output_config
        )

        # Write unified file
        output_path = self._write_unified_json(
            all_technologies,
            output_config
        )

        # Print summary
        self._print_summary(high_confidence, needs_review, output_path, stats)

        return output_path

    def _prepare_unified_output(
        self,
        high_confidence: List[Dict],
        needs_review: List[Dict],
        config: Dict
    ) -> List[Dict]:
        """Prepare unified output with all technologies."""
        all_technologies = []

        # Add high-confidence entries (needs_review = false)
        for entry in high_confidence:
            unified_entry = {
                'name': entry['name'],
                'quadrant': entry['quadrant'],
                'ring': entry['ring'],
                'description': entry['description'],
                'confidence': entry['confidence'],
                'needs_review': False,
                'metadata': self._prepare_metadata(entry, False)
            }
            all_technologies.append(unified_entry)

        # Add needs-review entries (needs_review = true)
        for entry in needs_review:
            unified_entry = {
                'name': entry['name'],
                'quadrant': entry['quadrant'],
                'ring': entry['ring'],
                'description': entry['description'],
                'confidence': entry['confidence'],
                'needs_review': True,
                'metadata': self._prepare_metadata(entry, True)
            }
            all_technologies.append(unified_entry)

        # Sort data
        sort_by = config.get('sort_by', 'usage')
        sorted_data = self._sort_data(all_technologies, sort_by)

        return sorted_data

    def _prepare_metadata(self, entry: Dict, needs_review: bool) -> Dict:
        """Prepare metadata for unified output."""
        metadata = {
            'repos_count': entry['metadata']['repos_count'],
            'usage_percentage': entry['metadata']['usage_percentage'],
            'total_repos': entry['metadata']['total_repos'],
            'ai_confidence': entry['metadata']['ai_confidence'],
            'ai_model': entry['metadata']['ai_model'],
            'temporal_data': entry['metadata']['temporal_data'],
            'usage_score': entry['metadata']['usage_score'],
            'recency_score': entry['metadata']['recency_score'],
            'activity_score': entry['metadata']['activity_score']
        }

        # Add decision factors for all entries
        if 'decision_factors' in entry:
            metadata['decision_factors'] = entry['decision_factors']

        # Add review metadata only for entries needing review
        if needs_review:
            metadata['review_metadata'] = {
                'reason': entry.get('review_reason', 'Unknown'),
                'status': 'pending',
                'human_decision': {
                    'final_ring': None,
                    'final_quadrant': None,
                    'notes': None
                }
            }
        else:
            metadata['review_metadata'] = None

        return metadata

    def _write_unified_json(
        self,
        all_technologies: List[Dict],
        config: Dict
    ) -> Path:
        """Write unified data.ai.json with all technologies."""
        output_file = config.get('file', '../data.ai.json')
        output_path = Path(output_file)

        # Write full version (internal use, with all metadata)
        full_output_path = output_path.parent / 'data.ai.full.json'
        full_output_path.parent.mkdir(parents=True, exist_ok=True)

        indent = 2 if config.get('format') == 'pretty' else None
        with open(full_output_path, 'w') as f:
            json.dump(all_technologies, f, indent=indent)

        logger.info(f"✓ Written {len(all_technologies)} technologies to {full_output_path} (full version)")

        # Write sanitized version (public use, without sensitive data)
        sanitized_technologies = self._sanitize_data(all_technologies)
        with open(output_path, 'w') as f:
            json.dump(sanitized_technologies, f, indent=indent)

        logger.info(f"✓ Written {len(sanitized_technologies)} technologies to {output_path} (sanitized version)")

        return output_path

    def _sanitize_data(self, technologies: List[Dict]) -> List[Dict]:
        """
        Remove sensitive internal information for public version.

        Removes:
        - repos_list (internal repository names)
        - repos_count (internal usage numbers)
        - usage_percentage (internal adoption metrics)
        - total_repos (organization size)
        - temporal_data (detailed activity patterns)
        - usage_score, recency_score, activity_score (internal metrics)
        - decision_factors (internal decision rationale)
        - review_metadata (internal review process)
        """
        sanitized = []

        for tech in technologies:
            sanitized_tech = {
                'name': tech['name'],
                'quadrant': tech['quadrant'],
                'ring': tech['ring'],
                'description': tech['description'],
                'confidence': tech['confidence'],
                'needs_review': tech['needs_review']
            }

            # Keep minimal metadata (only AI model info, no internal data)
            if 'metadata' in tech:
                sanitized_tech['metadata'] = {
                    'ai_confidence': tech['metadata'].get('ai_confidence'),
                    'ai_model': tech['metadata'].get('ai_model')
                }

            sanitized.append(sanitized_tech)

        return sanitized

    def _sort_data(self, data: List[Dict], sort_by: str) -> List[Dict]:
        """Sort data by specified criteria."""
        if sort_by == 'usage':
            return sorted(data, key=lambda x: x['metadata']['usage_percentage'], reverse=True)
        elif sort_by == 'name':
            return sorted(data, key=lambda x: x['name'])
        elif sort_by == 'ring':
            return sorted(data, key=lambda x: (x['ring'], x['name']))
        elif sort_by == 'confidence':
            return sorted(data, key=lambda x: x.get('confidence', 0), reverse=True)
        else:
            return data

    def _ring_name(self, ring: int) -> str:
        """Get ring name."""
        names = {0: 'Adopt', 1: 'Trial', 2: 'Assess', 3: 'Hold'}
        return names.get(ring, 'Unknown')

    def _quadrant_name(self, quadrant: int) -> str:
        """Get quadrant name."""
        names = {
            0: 'Techniques',
            1: 'Tools',
            2: 'Platforms',
            3: 'Languages & Frameworks'
        }
        return names.get(quadrant, 'Unknown')

    def _print_summary(
        self,
        high_confidence: List[Dict],
        needs_review: List[Dict],
        output_path: Path,
        stats: Dict
    ):
        """Print summary of unified output."""
        all_techs = high_confidence + needs_review

        print("\n" + "=" * 70)
        print("OUTPUT GENERATION SUMMARY")
        print("=" * 70)

        print(f"\n📄 Unified Output File: {output_path}")
        print(f"  Total technologies: {len(all_techs)}")

        print(f"\n✓ Auto-Approved (needs_review: false):")
        print(f"  {len(high_confidence)} technologies with high confidence (≥0.75)")

        if needs_review:
            print(f"\n⚠️  Needs Human Review (needs_review: true):")
            print(f"  {len(needs_review)} technologies require human decision")
            print(f"\n  Review reasons:")
            review_reasons = {}
            for tech in needs_review:
                reason = tech.get('review_reason', 'Unknown')
                review_reasons[reason] = review_reasons.get(reason, 0) + 1

            for reason, count in sorted(review_reasons.items(), key=lambda x: x[1], reverse=True):
                print(f"    - {reason}: {count}")

        print(f"\n📊 Confidence Distribution:")
        high = sum(1 for t in all_techs if t['confidence'] >= 0.85)
        medium = sum(1 for t in all_techs if 0.65 <= t['confidence'] < 0.85)
        low = sum(1 for t in all_techs if t['confidence'] < 0.65)

        print(f"  High (≥0.85):   {high}")
        print(f"  Medium (0.65-0.85): {medium}")
        print(f"  Low (<0.65):    {low}")

        print(f"\n📦 Repository Statistics:")
        print(f"  Scanned: {stats.get('repos_scanned', 0)}")
        print(f"  Skipped: {stats.get('repos_skipped', 0)}")

        if needs_review:
            print(f"\n💡 Next Steps:")
            print(f"  1. Filter technologies where needs_review = true")
            print(f"  2. Review temporal_data, decision_factors, and ai_suggestion")
            print(f"  3. Fill in review_metadata.human_decision (final_ring, notes)")
            print(f"  4. Set needs_review = false when approved")

        print("\n" + "=" * 70 + "\n")
