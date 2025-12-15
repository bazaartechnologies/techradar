#!/usr/bin/env python3
"""
Test domain-aware min_repos threshold.
"""
import sys
sys.path.insert(0, 'src')

from classifier_enhanced import EnhancedTechnologyClassifier
import yaml

def test_domain_aware_threshold():
    """Test that infrastructure techs with 1 repo are included."""

    # Load config
    with open('config/config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    classifier = EnhancedTechnologyClassifier("fake-key", config)

    # Simulate scenario: Prometheus found in 1 repo (iac, infrastructure domain)
    tech_name = "Prometheus"
    total_count = 1
    default_min_repos = 2
    min_repos_by_domain = config['classification']['min_repos_by_domain']

    # Mock repo_details (domain is a dict in actual scan results)
    repo_details = [
        {
            'name': 'iac',
            'domain': {'domain': 'infrastructure', 'confidence': 0.95},
            'technologies': {
                'tools': {'Prometheus', 'Grafana', 'Terraform'}
            }
        }
    ]

    # Test 1: Infrastructure domain with 1 repo should pass
    result = classifier._meets_domain_threshold(
        tech_name,
        total_count,
        repo_details,
        default_min_repos,
        min_repos_by_domain
    )

    print("Test 1: Infrastructure tech with 1 repo")
    print(f"  Tech: {tech_name}")
    print(f"  Domain: infrastructure")
    print(f"  Repo count: {total_count}")
    print(f"  Default threshold: {default_min_repos}")
    print(f"  Infrastructure threshold: {min_repos_by_domain.get('infrastructure')}")
    print(f"  Result: {'✅ PASS' if result else '❌ FAIL'}")
    print()

    # Test 2: Backend tech with 1 repo should NOT pass
    tech_name2 = "Express.js"
    repo_details2 = [
        {
            'name': 'api-service',
            'domain': {'domain': 'backend', 'confidence': 0.90},
            'technologies': {
                'frameworks': {'Express.js'}
            }
        }
    ]

    result2 = classifier._meets_domain_threshold(
        tech_name2,
        1,  # Only 1 repo
        repo_details2,
        default_min_repos,
        min_repos_by_domain
    )

    print("Test 2: Backend tech with 1 repo")
    print(f"  Tech: {tech_name2}")
    print(f"  Domain: backend")
    print(f"  Repo count: 1")
    print(f"  Default threshold: {default_min_repos}")
    print(f"  Backend threshold: {min_repos_by_domain.get('backend')}")
    print(f"  Result: {'❌ FAIL (expected)' if not result2 else '✅ PASS (unexpected)'}")
    print()

    # Test 3: Backend tech with 2 repos should pass
    repo_details3 = [
        {
            'name': 'api-service-1',
            'domain': {'domain': 'backend', 'confidence': 0.92},
            'technologies': {
                'frameworks': {'Express.js'}
            }
        },
        {
            'name': 'api-service-2',
            'domain': {'domain': 'backend', 'confidence': 0.88},
            'technologies': {
                'frameworks': {'Express.js'}
            }
        }
    ]

    result3 = classifier._meets_domain_threshold(
        tech_name2,
        2,  # 2 repos
        repo_details3,
        default_min_repos,
        min_repos_by_domain
    )

    print("Test 3: Backend tech with 2 repos")
    print(f"  Tech: {tech_name2}")
    print(f"  Domain: backend")
    print(f"  Repo count: 2")
    print(f"  Backend threshold: {min_repos_by_domain.get('backend')}")
    print(f"  Result: {'✅ PASS' if result3 else '❌ FAIL'}")
    print()

    # Summary
    all_pass = result and not result2 and result3
    print("=" * 60)
    print(f"Overall: {'✅ ALL TESTS PASSED' if all_pass else '❌ SOME TESTS FAILED'}")
    print("=" * 60)

    return all_pass

if __name__ == '__main__':
    try:
        success = test_domain_aware_threshold()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
