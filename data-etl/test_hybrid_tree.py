#!/usr/bin/env python3
"""
Test the new hybrid tree generation approach.
"""
import sys
import os
import yaml
from dotenv import load_dotenv

sys.path.insert(0, 'src')
from deep_scanner import DeepScanner

def test_hybrid_tree():
    """Test hybrid tree generation on real IAC repo."""

    load_dotenv()
    openai_key = os.getenv('OPENAI_API_KEY')

    if not openai_key:
        print("❌ OPENAI_API_KEY not found")
        return False

    # Load config
    with open('config/config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    scanner = DeepScanner(openai_key, config)
    print("✓ DeepScanner initialized\n")

    # Test on real IAC repo
    iac_path = os.path.expanduser('~/coding/iac')

    if not os.path.exists(iac_path):
        print(f"❌ IAC repo not found at {iac_path}")
        return False

    print(f"📁 Testing hybrid tree on: {iac_path}\n")

    # Generate tree
    tree_output = scanner._generate_tree(iac_path, 'iac')

    print("=" * 80)
    print("HYBRID TREE OUTPUT:")
    print("=" * 80)

    # Show first 2000 chars and last 500 chars
    if len(tree_output) > 2500:
        print(tree_output[:2000])
        print("\n... (middle section) ...\n")
        print(tree_output[-500:])
    else:
        print(tree_output)

    print("=" * 80)
    print(f"\nTotal size: {len(tree_output)} chars")

    # Check what's included
    checks = [
        ('accounts/' in tree_output, 'Has accounts/ structure'),
        ('prod' in tree_output, 'Has prod environment'),
        ('vault' in tree_output, 'Has vault'),
        ('eks' in tree_output or 'Important Files:' in tree_output, 'Has EKS or file list'),
        ('.pre-commit' in tree_output, 'Has .pre-commit-config.yaml'),
        ('.tf' in tree_output or 'Terraform' in tree_output, 'Has Terraform files'),
    ]

    print("\n✅ Content Checks:")
    for check, desc in checks:
        icon = "✓" if check else "✗"
        print(f"  {icon} {desc}")

    print("\n✅ Hybrid tree generation test complete!")
    return True

if __name__ == '__main__':
    try:
        success = test_hybrid_tree()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
