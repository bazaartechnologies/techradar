#!/usr/bin/env python3
"""
Quick test to verify all modules work together.
"""

import sys
import os

# Suppress SSL warnings
import warnings
warnings.filterwarnings('ignore')

print("Testing Tech Radar ETL modules...\n")

# Test 1: Config
print("✓ Testing config module...")
try:
    from config import Config
    config = Config()
    print(f"  - Config loaded: {len(config.to_dict())} sections")
    print(f"  - Organizations: {config['github']['organizations']}")
except Exception as e:
    print(f"  ✗ Config failed: {e}")
    sys.exit(1)

# Test 2: Rate Limiter
print("\n✓ Testing rate limiter module...")
try:
    from rate_limiter import CircuitBreaker
    cb = CircuitBreaker()
    print(f"  - Circuit breaker initialized (state: {cb.state})")
except Exception as e:
    print(f"  ✗ Rate limiter failed: {e}")
    sys.exit(1)

# Test 3: Detector
print("\n✓ Testing detector module...")
try:
    from detector import TechnologyDetector
    detector = TechnologyDetector()

    # Test aggregation
    test_data = [
        {'languages': {'Python'}, 'frameworks': {'Django'}},
        {'languages': {'Python'}, 'frameworks': {'Flask'}},
    ]
    counts = detector.aggregate_technologies(test_data)
    print(f"  - Detector working: found {len(counts)} technologies")
    print(f"  - Test aggregation: {counts}")
except Exception as e:
    print(f"  ✗ Detector failed: {e}")
    sys.exit(1)

# Test 4: Classifier
print("\n✓ Testing classifier module...")
try:
    from classifier import TechnologyClassifier
    classifier = TechnologyClassifier(
        config.get_openai_key(),
        config.to_dict()
    )

    # Test ring determination
    ring = classifier._determine_ring(75.0)
    print(f"  - Classifier initialized")
    print(f"  - Ring for 75% usage: {ring} (should be 0=Adopt)")

    # Test quadrant inference
    quadrant = classifier._infer_quadrant('React')
    print(f"  - Quadrant for React: {quadrant} (should be 3=Languages)")
except Exception as e:
    print(f"  ✗ Classifier failed: {e}")
    sys.exit(1)

# Test 5: Progress
print("\n✓ Testing progress module...")
try:
    from progress import ProgressTracker
    progress = ProgressTracker(
        config.get_checkpoint_path(),
        enabled=False
    )
    print(f"  - Progress tracker initialized")
except Exception as e:
    print(f"  ✗ Progress failed: {e}")
    sys.exit(1)

print("\n" + "="*60)
print("✓ All modules loaded successfully!")
print("="*60)
print("\nNext steps:")
print("  1. Add valid GitHub token and OpenAI key to .env")
print("  2. Run: python3 main.py --dry-run")
print("  3. Review output and adjust config if needed")
print("  4. Run full scan: python3 main.py")
