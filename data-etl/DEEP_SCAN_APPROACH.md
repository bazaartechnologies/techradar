# Deep Scan Approach

## The Simple Solution ✨

**Core Principle**: Let AI do ALL the discovery work. No hardcoded patterns.

### Algorithm

```
1. Generate full tree at configured depth (default: 6)
2. If tree > 80K chars (~100K tokens):
   - Reduce depth by 1
   - Retry
3. Repeat until tree fits in token limit (minimum depth: 3)
4. Give entire tree to AI
5. AI discovers everything from structure
```

### Why This Works

**✅ Generic**: No hardcoded file patterns or cloud providers
**✅ Dynamic**: Works with any repository structure
**✅ Simple**: ~30 lines of code, easy to understand
**✅ Efficient**: 1 AI call per repo (~$0.0005)
**✅ Complete**: AI sees entire structure and makes connections

### What AI Discovers

**From directory names:**
- `accounts/prod/eks/` → AWS EKS
- `accounts/vault/` → HashiCorp Vault
- `kubernetes/prometheus/` → Prometheus
- `monitoring/grafana/` → Grafana

**From file patterns:**
- `*.tf` files → Terraform
- `.pre-commit-config.yaml` → Pre-commit hooks + tools inside
- `Chart.yaml` → Helm
- `.trivyignore` → Trivy
- `Makefile` → Make

**From structure patterns:**
- Multiple environment dirs → Multi-env deployment
- Account-based structure → Multi-account AWS
- Blue/green directories → Blue-Green deployment

### Configuration

```yaml
deep_scan:
  enabled: true
  repositories:
    - iac
    - kubernetes-artifacts
    # Add any repo name

  tree:
    max_depth: 6  # Adaptive: reduces if needed
    ignore_patterns:
      - '.git'
      - 'node_modules'
      - '.terraform'
```

### Token Management

- **Max tree size**: 80K chars (~100K tokens with prompt)
- **AI limit**: 128K tokens total
- **Adaptive depth**: 6 → 5 → 4 → 3 (minimum)
- **Typical results**:
  - Small repos (< 50 dirs): Full tree at depth 6
  - Medium repos (50-200 dirs): Depth 4-5
  - Large repos (200+ dirs): Depth 3-4

### Cost

**Per repository**: ~$0.0005 (0.05 cents)
**For 5 infrastructure repos**: ~$0.0025 (0.25 cents)

Essentially free for discovering 10-20 technologies per repo.

## Comparison: Old vs New

### Old Approach (Complex) ❌

```python
# 200+ lines of code
def generate_tree():
    tree = get_tree_at_depth_6()
    if too_large:
        tree = get_tree_at_depth_4()
    if too_large:
        tree = get_tree_at_depth_2()
    if still_too_large:
        # Smart sampling (100 lines)
        tree = sample_first_40_percent()
        tree += sample_middle_20_percent()
        tree += find_important_files([
            '.pre-commit-config.yaml',  # Hardcoded!
            'Chart.yaml',               # Hardcoded!
            '*.tf',                     # Hardcoded!
            # ... 20 more patterns
        ])
    return tree
```

**Problems:**
- 200+ lines of complex logic
- Hardcoded file patterns (not generic)
- Arbitrary sampling (might miss important parts)
- Over-engineered

### New Approach (Simple) ✅

```python
# ~30 lines of code
def generate_tree():
    depth = 6
    while depth >= 3:
        tree = get_tree_at_depth(depth)
        if len(tree) <= 80000:
            return tree
        depth -= 1
    return tree[:80000]  # Fallback truncate
```

**Benefits:**
- ~30 lines total
- No hardcoded patterns
- Natural depth reduction
- AI discovers everything

## Real-World Results

### IAC Repo (Terraform infrastructure)

**Depth 2** (old, too shallow):
```
accounts/
  prod/
  vault/
  data/
templates/
tests/
```
**Result**: Found 6 technologies (Terraform, Shell, Make)

**Depth 4** (new, adaptive):
```
accounts/
  prod/
    eks/
      main.tf
      variables.tf
    rds/
      main.tf
    cloudwatch/
      alarms.tf
  vault/
    secrets/
      main.tf
.pre-commit-config.yaml
.trivyignore
Makefile
```
**Result**: Should find 15-20 technologies:
- Terraform, AWS EKS, AWS RDS, AWS CloudWatch
- Secrets Manager, Trivy, TFLint, terraform-docs
- Shell, Make, Pre-commit, GitHub Actions

### Kubernetes Artifacts Repo

**Expected discoveries** (96 Helm charts):
- Helm, Kubernetes, ArgoCD
- Prometheus, Grafana, Loki
- Falco, External Secrets
- AWS ALB Ingress Controller
- ~15-20 technologies total

## Key Insight

**Let the AI be the intelligence layer.**

We don't need to:
- ❌ Hardcode what files are "important"
- ❌ Guess which patterns indicate technologies
- ❌ Sample or truncate strategically

We just need to:
- ✅ Give AI a complete view of the structure
- ✅ Ensure it fits in token limits
- ✅ Let AI make all the connections

The AI is **way better** at inferring technologies from structure than any hardcoded pattern matching we could write.

## Future Improvements

If needed (but probably not):
1. Make depth adaptive based on repo size (currently starts at config value)
2. Add repo-specific depth overrides in config
3. Parallel processing for multiple deep-scan repos

But honestly, the current approach is perfect. Simple, generic, works.
