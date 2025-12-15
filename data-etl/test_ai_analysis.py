#!/usr/bin/env python3
"""
Test AI analysis of tree structure.
"""
import sys
import os
import yaml
from dotenv import load_dotenv

sys.path.insert(0, 'src')
from deep_scanner import DeepScanner

def test_ai_analysis():
    """Test AI analysis with sample tree."""

    load_dotenv()
    openai_key = os.getenv('OPENAI_API_KEY')

    if not openai_key:
        print("❌ OPENAI_API_KEY not found")
        return False

    print("✓ OpenAI API key found")

    # Load config
    with open('config/config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    scanner = DeepScanner(openai_key, config)
    print("✓ DeepScanner initialized")

    # Sample tree (simulating infrastructure repo)
    sample_tree = """
test-infrastructure-repo
├── .github
│   └── workflows
│       ├── terraform-ci.yaml
│       └── security-scan.yaml
├── kubernetes
│   ├── prometheus
│   │   ├── templates
│   │   │   ├── deployment.yaml
│   │   │   └── service.yaml
│   │   ├── Chart.yaml
│   │   └── values.yaml
│   ├── grafana
│   │   ├── dashboards
│   │   │   └── main.json
│   │   └── Chart.yaml
│   └── loki
│       └── Chart.yaml
├── terraform
│   ├── modules
│   │   ├── eks
│   │   │   ├── main.tf
│   │   │   └── variables.tf
│   │   └── rds
│   │       └── main.tf
│   └── environments
│       ├── prod
│       │   └── main.tf
│       └── staging
│           └── main.tf
├── .pre-commit-config.yaml
└── Makefile
"""

    print("\n📊 Sample tree structure:")
    print("=" * 60)
    print(sample_tree.strip())
    print("=" * 60)

    print("\n🤖 Analyzing with AI (this may take 5-10 seconds)...")

    try:
        technologies = scanner._ai_analyze_tree('test-infrastructure-repo', sample_tree)

        print(f"\n✅ AI Analysis Complete!")
        print(f"\n📦 Discovered Technologies ({len(technologies)}):")
        for tech in sorted(technologies):
            print(f"  • {tech}")

        # Expected technologies
        expected = ['Terraform', 'Kubernetes', 'Helm', 'Prometheus', 'Grafana']

        print(f"\n🎯 Expected Technologies Check:")
        for exp in expected:
            found = any(exp.lower() in tech.lower() for tech in technologies)
            icon = "✓" if found else "✗"
            print(f"  {icon} {exp}")

        if len(technologies) > 0:
            print("\n✅ AI analysis is WORKING!")
            return True
        else:
            print("\n❌ No technologies found - check AI prompt or API")
            return False

    except Exception as e:
        print(f"\n❌ AI analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    try:
        success = test_ai_analysis()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
