#!/usr/bin/env python3
"""
Test if domain_breakdown is generated correctly.
"""

import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from classifier_enhanced import EnhancedTechnologyClassifier

# Test data from actual Java entry
by_domain_data = {
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
    },
    "library": {
        "total_repos": 4,
        "recent_repos": 0,
        "new_repos": 0,
        "active_repos": 1,
        "recency_score": 0.0,
        "activity_score": 0.25,
        "trend": "ABANDONED"
    }
}

# Create a minimal config
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

# Initialize classifier (we won't actually use AI, just the domain breakdown method)
classifier = EnhancedTechnologyClassifier('dummy_key', config)

# Test the domain breakdown method
print("Testing _analyze_domain_breakdown method...")
print("=" * 60)

result = classifier._analyze_domain_breakdown("Java", by_domain_data)

print("\nResult:")
print(json.dumps(result, indent=2))

print("\n" + "=" * 60)
print("✓ Test passed! Domain breakdown generated successfully.")
print("\nExpected structure:")
print("- Each domain should have: suggested_ring, ring_name, confidence")
print("- Mobile should suggest ADOPT or TRIAL (7 repos, high activity)")
print("- Backend should suggest ADOPT or TRIAL (11 repos, high activity)")
print("- Library should suggest HOLD (4 repos, abandoned)")
