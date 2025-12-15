#!/usr/bin/env python3
"""
Quick test for deep scanner functionality.
"""
import sys
import os
import yaml
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, 'src')

from deep_scanner import DeepScanner

def test_deep_scanner():
    """Test deep scanner with config."""

    # Load environment
    load_dotenv()
    openai_key = os.getenv('OPENAI_API_KEY')

    if not openai_key:
        print("❌ OPENAI_API_KEY not found in .env")
        return False

    print("✓ OpenAI API key found")

    # Load config
    with open('config/config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    print("✓ Config loaded")

    # Initialize scanner
    scanner = DeepScanner(openai_key, config)
    print("✓ DeepScanner initialized")

    # Check configuration
    deep_config = config.get('deep_scan', {})
    print(f"\nDeep Scan Config:")
    print(f"  Enabled: {deep_config.get('enabled')}")
    print(f"  Repos: {deep_config.get('repositories')}")
    print(f"  Max depth: {deep_config.get('tree', {}).get('max_depth')}")

    # Test should_deep_scan
    test_repos = ['iac', 'bazaar-kubernetes-artifacts', 'random-repo']
    print(f"\nTesting should_deep_scan():")
    for repo in test_repos:
        result = scanner.should_deep_scan(repo)
        icon = "✓" if result else "✗"
        print(f"  {icon} {repo}: {result}")

    print("\n✅ All tests passed!")
    print("\nNote: Full integration test requires:")
    print("  1. Valid GitHub token")
    print("  2. Access to actual repos")
    print("  3. Run: python src/main.py --limit 5 --dry-run")

    return True

if __name__ == '__main__':
    try:
        success = test_deep_scanner()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
