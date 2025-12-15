#!/usr/bin/env python3
"""
Test tree generation functionality.
"""
import sys
import os
import tempfile
import shutil
import subprocess
import yaml
from dotenv import load_dotenv

sys.path.insert(0, 'src')
from deep_scanner import DeepScanner

def create_test_repo():
    """Create a test repository structure."""
    temp_dir = tempfile.mkdtemp(prefix='test_tree_')

    # Create infrastructure-like structure
    os.makedirs(f'{temp_dir}/terraform/modules/eks')
    os.makedirs(f'{temp_dir}/kubernetes/prometheus/templates')
    os.makedirs(f'{temp_dir}/kubernetes/grafana/dashboards')
    os.makedirs(f'{temp_dir}/.github/workflows')

    # Create some files
    open(f'{temp_dir}/terraform/main.tf', 'w').write('# Terraform config')
    open(f'{temp_dir}/terraform/modules/eks/cluster.tf', 'w').write('# EKS cluster')
    open(f'{temp_dir}/kubernetes/prometheus/Chart.yaml', 'w').write('apiVersion: v2\nname: prometheus')
    open(f'{temp_dir}/kubernetes/grafana/Chart.yaml', 'w').write('apiVersion: v2\nname: grafana')
    open(f'{temp_dir}/.pre-commit-config.yaml', 'w').write('repos:\n  - repo: https://github.com/aquasecurity/trivy')
    open(f'{temp_dir}/.github/workflows/ci.yaml', 'w').write('name: CI')

    return temp_dir

def test_tree_generation():
    """Test tree generation with real tree command."""

    load_dotenv()
    openai_key = os.getenv('OPENAI_API_KEY')

    if not openai_key:
        print("❌ OPENAI_API_KEY not found")
        return False

    # Load config
    with open('config/config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    scanner = DeepScanner(openai_key, config)

    # Create test repo
    test_dir = create_test_repo()
    print(f"✓ Created test repo at: {test_dir}")

    try:
        # Test tree generation
        print("\n📁 Generating tree...")
        tree_output = scanner._generate_tree(test_dir, 'test-repo')

        print("\n📊 Tree output:")
        print("=" * 60)
        print(tree_output)
        print("=" * 60)

        # Verify expected patterns
        checks = [
            ('terraform/' in tree_output, 'Contains terraform/'),
            ('kubernetes/' in tree_output, 'Contains kubernetes/'),
            ('prometheus' in tree_output, 'Contains prometheus'),
            ('grafana' in tree_output, 'Contains grafana'),
            ('Chart.yaml' in tree_output, 'Contains Chart.yaml'),
            ('.pre-commit-config.yaml' in tree_output, 'Contains .pre-commit-config.yaml'),
            ('.tf' in tree_output, 'Contains .tf files'),
        ]

        print("\n✅ Verification:")
        all_passed = True
        for check, desc in checks:
            icon = "✓" if check else "✗"
            print(f"  {icon} {desc}")
            all_passed = all_passed and check

        if all_passed:
            print("\n✅ Tree generation test PASSED")
        else:
            print("\n❌ Some checks failed")

        return all_passed

    finally:
        # Cleanup
        shutil.rmtree(test_dir, ignore_errors=True)
        print(f"\n🗑️  Cleaned up test repo")

if __name__ == '__main__':
    try:
        success = test_tree_generation()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
