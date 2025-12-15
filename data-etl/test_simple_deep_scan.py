#!/usr/bin/env python3
"""
Test the simplified deep scanner on IAC repo.
"""
import sys
import os
import yaml
from dotenv import load_dotenv

sys.path.insert(0, 'src')
from deep_scanner import DeepScanner

def test_iac_deep_scan():
    """Test deep scan on real IAC repo."""

    load_dotenv()
    openai_key = os.getenv('OPENAI_API_KEY')

    if not openai_key:
        print("❌ OPENAI_API_KEY not found")
        return False

    print("✓ OpenAI API key found\n")

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

    print(f"📁 Testing on: {iac_path}\n")
    print("=" * 80)

    # Generate tree
    print("Phase 1: Generating tree structure...")
    tree_output = scanner._generate_tree(iac_path, 'iac')

    print(f"✓ Tree generated: {len(tree_output)} chars\n")

    # Show sample
    print("Tree preview (first 1500 chars):")
    print("-" * 80)
    print(tree_output[:1500])
    print("-" * 80)
    print(f"... (showing first 1500 of {len(tree_output)} chars)\n")

    # Quick checks
    checks = [
        ('accounts' in tree_output, 'Has accounts structure'),
        ('prod' in tree_output or 'vault' in tree_output, 'Has environments'),
        ('.tf' in tree_output or 'terraform' in tree_output.lower(), 'Has Terraform indicators'),
        ('.pre-commit' in tree_output, 'Has pre-commit config'),
        ('Makefile' in tree_output, 'Has Makefile'),
    ]

    print("Content checks:")
    for check, desc in checks:
        icon = "✓" if check else "✗"
        print(f"  {icon} {desc}")

    # Now do AI analysis
    print(f"\n{'=' * 80}")
    print("Phase 2: AI Analysis (this takes ~10-20 seconds)...")
    print("=" * 80)

    technologies = scanner._ai_analyze_tree('iac', tree_output)

    print(f"\n✅ AI Analysis Complete!\n")
    print(f"📦 Discovered {len(technologies)} Technologies:")
    print("-" * 80)
    for tech in sorted(technologies):
        print(f"  • {tech}")
    print("-" * 80)

    # Expected technologies
    expected_categories = {
        'Infrastructure': ['Terraform', 'AWS'],
        'Security': ['Trivy', 'TFLint', 'terraform-docs'],
        'Tools': ['Make', 'Shell', 'Pre-commit'],
        'CI/CD': ['GitHub Actions'],
    }

    print(f"\n📊 Analysis by Category:")
    for category, expected_techs in expected_categories.items():
        found = [t for t in technologies if any(exp.lower() in t.lower() for exp in expected_techs)]
        if found:
            print(f"\n  {category}:")
            for tech in found:
                print(f"    ✓ {tech}")

    # Success metrics
    min_expected = 8
    if len(technologies) >= min_expected:
        print(f"\n✅ SUCCESS: Found {len(technologies)} technologies (expected: {min_expected}+)")
        return True
    else:
        print(f"\n⚠️  WARNING: Only found {len(technologies)} technologies (expected: {min_expected}+)")
        print("This might indicate the tree depth was too shallow.")
        return False

if __name__ == '__main__':
    try:
        success = test_iac_deep_scan()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
