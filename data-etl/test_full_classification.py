#!/usr/bin/env python3
"""
Test full classification with domain breakdown.
"""

import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from classifier_enhanced import EnhancedTechnologyClassifier

# Test data simulating Java
temporal_data = {
    "total_repos": 24,
    "recent_repos": 0,
    "new_repos": 0,
    "legacy_repos": 24,
    "active_repos": 16,
    "stale_repos": 8,
    "avg_age_months": 58.2,
    "trend": "STABLE",
    "recency_score": 0.0,
    "activity_score": 0.667,
    "repos_list": ["repo1", "repo2"],
    "by_domain": {
        "mobile": {
            "total_repos": 7,
            "recent_repos": 0,
            "new_repos": 0,
            "active_repos": 5,
            "recency_score": 0.0,
            "activity_score": 0.714,
            "trend": "STABLE"
        },
        "backend": {
            "total_repos": 11,
            "recent_repos": 0,
            "new_repos": 0,
            "active_repos": 9,
            "recency_score": 0.0,
            "activity_score": 0.818,
            "trend": "STABLE"
        }
    }
}

# Minimal config
config = {
    'openai': {
        'model': 'gpt-4o-mini',
        'max_tokens': 1000,
        'temperature': 0.3
    },
    'classification': {
        'min_repos': 2,
        'exclude_patterns': []
    }
}

# Mock AI result
class MockClassifier(EnhancedTechnologyClassifier):
    def _ai_classify_enhanced(self, tech_name, usage_percentage, temporal_data, suggested_ring):
        """Mock AI classification to avoid API calls."""
        return {
            "quadrant": 3,
            "description": f"Test description for {tech_name}",
            "ai_confidence": "high"
        }

# Initialize classifier
classifier = MockClassifier('dummy_key', config)

# Test full classification
print("Testing full classification with domain breakdown...")
print("=" * 70)

result = classifier._classify_single_enhanced(
    tech_name="Java",
    count=24,
    total_repos=39,
    usage_percentage=61.5,
    temporal_data=temporal_data,
    repo_details=[]
)

print("\nClassification Result:")
print(json.dumps(result, indent=2))

# Verify domain_breakdown exists
if 'domain_breakdown' in result.get('metadata', {}):
    print("\n" + "=" * 70)
    print("✓ SUCCESS! domain_breakdown field is present in metadata")
    print("\nDomain Breakdown:")
    for domain, data in result['metadata']['domain_breakdown'].items():
        print(f"  {domain}: {data['ring_name']} (confidence: {data['confidence']})")
else:
    print("\n" + "=" * 70)
    print("✗ FAILED! domain_breakdown field is MISSING")
    print("\nAvailable metadata keys:", list(result.get('metadata', {}).keys()))
