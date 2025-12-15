# Domain-Aware Technology Filtering

## Overview

Successfully implemented domain-aware minimum repository thresholds to handle the architectural difference between centralized and distributed technology deployments.

## Problem Solved

**Infrastructure technologies** are centralized - a single repo (like `iac`) serves as the source of truth. Technologies like Prometheus, Grafana, or AWS RDS defined 50× in one infrastructure repo indicate high maturity.

**Application technologies** are distributed - technologies like Java or React appear across multiple microservices/apps. Finding them in many repos indicates maturity.

The previous `min_repos: 2` threshold filtered out valid infrastructure technologies found only in the centralized IAC repo.

## Solution

### Config-Based Domain Thresholds

Added domain-specific minimum repository thresholds in `config/config.yaml`:

```yaml
classification:
  # Default threshold
  min_repos: 2

  # Domain-aware thresholds
  min_repos_by_domain:
    infrastructure: 1  # Centralized architecture
    data: 1           # Centralized pipelines
    backend: 2        # Distributed microservices
    frontend: 2       # Multiple apps
    mobile: 2         # Multiple apps
    ml: 2             # Multiple projects
    library: 2        # Used across projects
    tooling: 2        # Various tools
    unknown: 2        # Default fallback
```

### Implementation

Modified `classifier_enhanced.py` to check domain-specific thresholds:

1. **Global check first**: If technology appears in 2+ repos (any domain), include it
2. **Domain check second**: Check if technology meets its domain-specific threshold
3. **Transparent logging**: Log which technologies pass/fail and why

Key method: `_meets_domain_threshold()`

## Test Results

### Unit Test (`test_domain_aware_threshold.py`)

```
Test 1: Infrastructure tech with 1 repo ✅ PASS
Test 2: Backend tech with 1 repo ❌ FAIL (expected)
Test 3: Backend tech with 2 repos ✅ PASS
```

### Integration Test (`test_integration_domain_aware.py`)

```
Prometheus      | infrastructure | 1 repo  | ✅ PASS
Grafana         | infrastructure | 1 repo  | ✅ PASS
Falco           | infrastructure | 1 repo  | ✅ PASS
ArgoCD          | infrastructure | 1 repo  | ✅ PASS
AWS RDS         | infrastructure | 1 repo  | ✅ PASS
AWS EKS         | infrastructure | 1 repo  | ✅ PASS

Java            | backend        | 2 repos | ✅ PASS
PostgreSQL      | backend        | 2 repos | ✅ PASS
```

## Impact

### Before
- Deep scan found 30+ technologies in IAC repo
- All filtered out by `min_repos: 2` threshold
- Infrastructure technologies invisible in tech radar

### After
- Infrastructure technologies with 1 repo pass threshold
- Application technologies still require 2+ repos
- Tech radar accurately reflects infrastructure maturity

## Deep Scan Integration

The domain-aware filtering works seamlessly with deep scanning:

1. Deep scan discovers infrastructure technologies (Prometheus, Grafana, etc.)
2. AI classifier detects repo domain (`infrastructure`)
3. Domain-aware threshold allows technologies with 1 repo
4. Technologies appear in final `data.ai.json` output

## Running a Scan

```bash
# Full scan (all repos)
python3 src/main.py

# Limited scan (faster testing)
python3 src/main.py --limit 50

# Resume from checkpoint
python3 src/main.py --resume
```

## Expected Results

Infrastructure technologies from IAC repo will now appear in `data.ai.json`:

- **Monitoring**: Prometheus, Grafana, Loki
- **Security**: Falco, Trivy, Keycloak
- **GitOps**: ArgoCD
- **Cloud Services**: AWS RDS, AWS EKS, AWS Lambda, AWS S3
- **IaC**: Terraform, CloudFormation
- **Container**: Kubernetes, Docker, ECR

## Configuration

To adjust thresholds, edit `config/config.yaml`:

```yaml
min_repos_by_domain:
  infrastructure: 1  # Lower = more permissive
  backend: 3         # Higher = more strict
```

## Files Changed

1. `config/config.yaml` - Added domain-specific thresholds
2. `src/classifier_enhanced.py` - Implemented domain-aware logic
3. `test_domain_aware_threshold.py` - Unit tests
4. `test_integration_domain_aware.py` - Integration tests

## Logging

The classifier logs threshold decisions:

```
✓ Prometheus meets infrastructure domain threshold (1 repos >= 1 required)
✗ Express.js below thresholds (total:1, by domain: backend:1)
```

Use `logs/scan.log` to debug filtering decisions.

## Next Steps

1. Run a full scan to generate updated `data.ai.json`
2. Verify infrastructure technologies appear in tech radar
3. Adjust domain thresholds if needed based on results
4. Consider adding more domain-specific rules (e.g., domain-specific ring thresholds)
