# Tech Radar Data ETL

Automated technology scanning tool that analyzes GitHub repositories and generates tech radar data using AI.

## Features

- 🔍 Scans GitHub organizations for technology usage
- 🤖 AI-powered classification using OpenAI GPT-4o-mini
- 📊 Usage-based adoption level detection with domain-aware analysis
- 🔬 **Deep scanning** for infrastructure repos using tree-based analysis
- 🌐 **Domain segmentation** (infrastructure, backend, frontend, mobile)
- 🔄 Automatic pagination and rate limiting
- 💾 Progress checkpointing for resumability
- 📝 Comprehensive logging and error handling
- 🛡️ Circuit breaker pattern for API reliability
- 🏗️ **Organization-agnostic** design - works with any GitHub org

## Quick Start

### 1. Install Dependencies

```bash
cd data-etl
pip install -r requirements.txt
```

### 2. Configure Environment

Create `.env` file:

```bash
GITHUB_TOKEN=your_github_token_here
OPENAI_API_KEY=your_openai_key_here
```

⚠️ **Never commit `.env` file to git!**

### 3. Configure Scan

Edit `config/config.yaml`:

```yaml
github:
  organizations:
    - bazaartechnologies
  exclude_repos:
    - "*-archived"
    - "test-*"

openai:
  model: gpt-4o-mini
  max_tokens: 1000

output:
  file: ../data.ai.json
  format: pretty
```

### 4. Run Scan

```bash
# Scan all repos in configured organizations
python src/main.py

# Scan specific organization
python src/main.py --org bazaartechnologies

# Dry run (no file output)
python src/main.py --dry-run

# Resume from checkpoint
python src/main.py --resume
```

## How It Works

### 1. Repository Discovery
- Fetches all repositories from configured GitHub organizations
- Applies filters (archived, private, etc.)
- Handles pagination automatically

### 2. Technology Detection

**Standard Detection** scans for technologies in:
- `package.json` (Node.js/JavaScript)
- `requirements.txt`, `Pipfile`, `pyproject.toml` (Python)
- `go.mod`, `go.sum` (Go)
- `Cargo.toml` (Rust)
- `pom.xml`, `build.gradle`, `build.gradle.kts` (Java/Kotlin)
- `Gemfile` (Ruby)
- `composer.json` (PHP)
- `Dockerfile` (Docker)
- `.github/workflows/*.yml` (CI/CD tools)

**Deep Scanning** (for infrastructure repos):
- Shallow clones specified repositories
- Generates full directory tree structure
- AI analyzes tree to discover embedded technologies:
  - Security tools (Trivy, Falco, etc.)
  - Monitoring stack (Prometheus, Grafana, etc.)
  - Kubernetes tools (ArgoCD, Helm charts, etc.)
  - Cloud services and infrastructure patterns
- Completely organization-agnostic - no hardcoded patterns

### 3. Domain Detection

AI automatically analyzes each repository to determine its domain:
- **Infrastructure**: IaC repos, Kubernetes configs, CI/CD pipelines
- **Backend**: APIs, services, microservices
- **Frontend**: Web apps, mobile web, UI libraries
- **Mobile**: iOS, Android, cross-platform mobile apps

Domain detection uses:
- Repository structure analysis
- File pattern recognition
- Technology stack inference
- No hardcoded organization patterns

### 4. AI Classification

For each discovered technology, AI determines:

**Quadrant** (Category):
- 0: Techniques (methodologies, practices)
- 1: Tools (development tools, testing frameworks)
- 2: Platforms (infrastructure, databases, cloud)
- 3: Languages & Frameworks

**Ring** (Adoption Level) - Domain-aware classification:

**Primary Logic** (checks domain dominance first):
- 50+ repos in a domain + 50% active → **Adopt** for that domain
- 70+ repos in a domain + 40% active → **Adopt** for that domain
- 30+ repos in a domain + 65% active → **Trial** for that domain

**Fallback Logic** (global usage):
- 40%+ usage + 50%+ active → **Adopt**
- 35%+ usage + 60%+ active → **Adopt**
- 30%+ usage + 50%+ active → **Trial**
- 15%+ usage + 40%+ active → **Assess**
- Below thresholds → **Hold**

**Activity Window**: Repos with commits in last 90 days considered active

**Description**: AI-generated summary explaining:
- What the technology is
- Why it's in that ring
- Domain-specific recommendations

### 5. Output Generation

Creates `data.ai.json` with comprehensive metadata:

```json
[
  {
    "name": "Java",
    "quadrant": 3,
    "ring": 0,
    "description": "Enterprise-grade language. Dominant in backend (95% of backend repos), 58% active. Strategic choice for microservices.",
    "metadata": {
      "repos_count": 105,
      "usage_percentage": 48.2,
      "total_repos_scanned": 218,
      "recency_score": 0.42,
      "activity_score": 0.58,
      "trend": "stable",
      "confidence": 0.9
    },
    "temporal_data": {
      "recent_repos": 15,
      "new_repos": 8,
      "active_repos": 61,
      "legacy_repos": 42,
      "by_domain": {
        "backend": {
          "total_repos": 100,
          "recent_repos": 12,
          "active_repos": 58,
          "usage_percentage": 95.2,
          "activity_score": 0.58,
          "trend": "stable"
        },
        "infrastructure": {
          "total_repos": 5,
          "recent_repos": 3,
          "active_repos": 3,
          "usage_percentage": 4.8,
          "activity_score": 0.60,
          "trend": "growing"
        }
      }
    },
    "domain_breakdown": {
      "backend": {
        "ring": 0,
        "description": "Dominant backend language (95% usage). Production-ready, actively maintained.",
        "confidence": 0.95
      },
      "infrastructure": {
        "ring": 2,
        "description": "Limited infrastructure usage (5 repos). Assess for specific use cases.",
        "confidence": 0.70
      }
    }
  }
]
```

**Key Fields**:
- `temporal_data.by_domain`: Domain-specific usage statistics
- `domain_breakdown`: Different classifications per domain
- `activity_score`: Percentage of repos active in last 90 days
- `trend`: "growing", "stable", "declining", "new"

User can review and manually rename to `data.json` when ready.

## Configuration Reference

### config.yaml

```yaml
github:
  # Organizations to scan
  organizations:
    - bazaartechnologies
    - another-org

  # Repository filters
  exclude_repos:
    - "*-archived"    # Exclude archived repos
    - "test-*"        # Exclude test repos
    - "legacy-*"      # Exclude legacy repos

  # Repository requirements
  min_stars: 0
  include_forks: false
  include_archived: false
  include_private: true

openai:
  # Model to use
  model: gpt-4o-mini  # or gpt-4o, gpt-4-turbo

  # Token limits
  max_tokens: 1000
  temperature: 0.3    # Lower = more consistent

  # Retry configuration
  max_retries: 3
  timeout: 30

classification:
  # Usage-based thresholds
  thresholds:
    adopt: 0.7    # 70%+
    trial: 0.4    # 40-70%
    assess: 0.1   # 10-40%
    # Below 10% = Hold

  # Minimum repos to be considered
  min_repos: 2

  # Technology filters
  exclude_patterns:
    - "*-internal"  # Exclude internal tools
    - "custom-*"    # Exclude custom tools

output:
  # Output file path (relative to data-etl/)
  file: ../data.ai.json

  # Format: pretty or compact
  format: pretty

  # Include metadata
  include_metadata: true

  # Sort by usage
  sort_by: usage  # or name, ring

logging:
  # Log level
  level: INFO  # DEBUG, INFO, WARNING, ERROR

  # Log file
  file: logs/scan.log

  # Console output
  console: true

# Rate limiting
rate_limit:
  # Max requests per minute (GitHub search API limit is 30)
  max_per_minute: 25

  # Safety threshold (pause if remaining < this)
  safety_threshold: 100

# Progress tracking
checkpoint:
  enabled: true
  file: .scan_progress.json
  save_interval: 10  # Save every N repos

# Deep scanning for infrastructure repositories
deep_scan:
  # Enable deep scanning
  enabled: true

  # Repositories to deep scan (by name)
  repositories:
    - iac
    - kubernetes-artifacts
    - infrastructure

  # Tree generation settings
  tree:
    max_depth: 6  # Maximum directory depth
    ignore_patterns:  # Directories/files to ignore
      - '.git'
      - 'node_modules'
      - '.terraform'
      - '__pycache__'
      - '*.pyc'
      - 'vendor'
      - 'dist'
      - 'build'
```

## Deep Scanning Feature

### What is Deep Scanning?

Deep scanning unlocks hidden technologies in infrastructure repositories that standard file detection misses.

**Problem**: Repos like `iac` (Infrastructure as Code) or `kubernetes-artifacts` contain:
- Security tools embedded in pre-commit hooks (Trivy, TFLint)
- Monitoring stack in Helm charts (Prometheus, Grafana, Loki)
- Kubernetes tools in directory structure (ArgoCD, Falco, External Secrets)
- Cloud services in Terraform modules

Standard detection only looks at dependency files and misses these embedded tools.

**Solution**: Tree-based AI analysis
1. Shallow clone the repository (fast, 1-2 seconds)
2. Generate full directory tree structure
3. AI analyzes tree to discover technologies from:
   - Directory names (e.g., `prometheus/` → Prometheus)
   - File patterns (e.g., `*.tf` → Terraform)
   - Configuration files (e.g., `Chart.yaml` → Helm)
   - Structural patterns

**Key Benefits**:
- ✅ **Fast**: Shallow clone + tree generation (~2-3 seconds per repo)
- ✅ **Cheap**: Single AI call per repo (~$0.0005 per repo)
- ✅ **Complete**: Full repository context in one analysis
- ✅ **Agnostic**: No hardcoded patterns or cloud provider assumptions
- ✅ **Clean**: Automatic cleanup of temp files

### Configuring Deep Scan

Add repositories to deep scan in `config.yaml`:

```yaml
deep_scan:
  enabled: true

  # List repos by name (not full path)
  repositories:
    - iac
    - kubernetes-artifacts
    - infrastructure
    - platform-configs

  tree:
    max_depth: 6  # How deep to traverse
    ignore_patterns:  # Skip these directories
      - '.git'
      - 'node_modules'
      - '.terraform'
      - '__pycache__'
      - 'vendor'
      - 'dist'
      - 'build'
```

**When scanner encounters these repos**, it automatically:
1. Performs standard detection first
2. Then performs deep scan
3. Merges results (deep scan discoveries added to `tools` category)
4. Logs discoveries: "✅ Deep scan added 8 new technologies"

### Example Output

```
🔍 Deep scanning iac...
Cloning iac to /tmp/scan_iac_xyz...
✓ Cloned iac
Generating tree for iac...
✓ Generated tree (12,543 chars)
  Found: Terraform (high confidence) - *.tf files throughout
  Found: Trivy (high confidence) - .trivyignore and pre-commit config
  Found: AWS Secrets Manager (medium confidence) - terraform modules
  Found: TFLint (medium confidence) - pre-commit hooks
  Pattern: Multi-account AWS structure - accounts/ directory
✅ Deep scan added 8 new technologies to iac
```

### Technologies Typically Discovered

**Infrastructure Repos** (`iac`, `terraform`):
- Security: Trivy, TFLint, terraform-docs, Checkov
- Cloud Services: AWS services from module names
- Tools: Pre-commit, Makefiles, shell scripts

**Kubernetes Repos** (`kubernetes-artifacts`, `k8s-configs`):
- Monitoring: Prometheus, Grafana, Loki, Thanos
- Security: Falco, OPA/Gatekeeper, External Secrets
- GitOps: ArgoCD, Flux, Helm
- Ingress: NGINX Ingress, Traefik, Istio
- Service Mesh: Linkerd, Consul

**Platform Repos**:
- CI/CD: GitHub Actions, GitLab CI, Jenkins
- Databases: From chart dependencies
- Message Queues: Kafka, RabbitMQ, Redis

### Cost Analysis

**Per Repository**:
- Tree generation: Free (local command)
- AI analysis: ~12K tokens input + 500 tokens output = ~$0.0005
- Total: **$0.0005 per repo**

**For 5 infrastructure repos**: $0.0025 (~¼ cent)

**Compared to manual analysis**: Saves hours of work for minimal cost

## CLI Commands

```bash
# Basic scan (includes deep scan if enabled)
python src/main.py

# Scan specific org
python src/main.py --org myorg

# Dry run (preview only)
python src/main.py --dry-run

# Resume from checkpoint
python src/main.py --resume

# Clear checkpoint and start fresh
python src/main.py --fresh

# Verbose output
python src/main.py --verbose

# Custom config file
python src/main.py --config custom-config.yaml

# Output to custom file
python src/main.py --output custom-output.json
```

## Error Handling

### Rate Limiting
- Automatically pauses when approaching GitHub API limits
- Uses exponential backoff for retries
- Displays estimated wait time

### Network Errors
- Automatic retry with exponential backoff (max 5 attempts)
- Circuit breaker opens after 5 consecutive failures
- Progress saved via checkpoints - resume anytime

### API Errors
- Invalid tokens → Clear error message with setup instructions
- Quota exceeded → Pause and notify user
- Parse errors → Log and skip problematic repos

## Monitoring

### Progress Tracking
```
Scanning repositories...
[=========>        ] 45/100 repos (45%)
Current: bazaartechnologies/frontend-app
Technologies found: 23
ETA: 5 minutes
```

### Logs
All operations logged to:
- Console (INFO level)
- `logs/scan.log` (DEBUG level)
- `logs/errors.log` (ERROR level only)

### Metrics
Final report includes:
- Repositories scanned
- Technologies discovered
- API calls made
- Errors encountered
- Duration and rate

## Troubleshooting

### "Authentication failed"
- Check your GitHub token in `.env`
- Ensure token has `repo` and `read:org` scopes
- Regenerate token if compromised

### "Rate limit exceeded"
- Wait for rate limit reset (check logs for time)
- Reduce `max_per_minute` in config
- Use GitHub GraphQL API (more efficient)

### "OpenAI API error"
- Check API key in `.env`
- Verify OpenAI account has credits
- Check model name is correct (`gpt-4o-mini`)

### Empty or incomplete results
- Check logs in `logs/scan.log`
- Verify organization name is correct
- Ensure repos contain recognizable tech files
- Use `--verbose` flag for detailed output

### Scan is too slow
- GitHub has strict rate limits (5000/hour)
- Use GraphQL mode (add `--graphql` flag)
- Scan fewer repositories
- Run during off-peak hours

## Best Practices

### Regular Scans
Schedule weekly scans via cron:
```bash
# Every Monday at 2 AM
0 2 * * 1 cd /path/to/data-etl && python src/main.py >> logs/cron.log 2>&1
```

### Review AI Results
Always review `data.ai.json` before using:
1. Check classifications make sense
2. Verify descriptions are accurate
3. Adjust rings if needed
4. Remove irrelevant entries
5. Rename to `data.json` when ready

### Version Control
- Commit `data.ai.json` to track changes over time
- Use git diff to see what changed
- Keep history of tech stack evolution

### Multi-Org Scanning
For multiple organizations:
```yaml
github:
  organizations:
    - bazaartechnologies
    - partner-org
    - client-org
```

## Security

### API Keys
- Store in `.env` (never commit!)
- Use environment variables in CI/CD
- Rotate keys regularly
- Use minimum required scopes

### Data Privacy
- Tool only reads public repository data
- No code content is sent to OpenAI
- Only package names and versions analyzed
- Review logs before sharing

## Development

### Running Tests
```bash
pytest tests/
pytest tests/ --cov=src  # With coverage
```

### Adding New Tech Detectors
Edit `src/detectors.py`:
```python
def detect_scala(repo):
    """Detect Scala projects"""
    if repo.has_file('build.sbt'):
        return parse_sbt_file(repo.get_file('build.sbt'))
    return []
```

### Custom Classification Logic
Edit `src/classifier.py`:
```python
def classify_custom(tech, usage_data):
    """Custom classification logic"""
    if tech.name == 'SpecialTool':
        return Ring.ADOPT  # Force specific ring
    return classify_by_usage(tech, usage_data)
```

## Architecture

```
data-etl/
├── src/
│   ├── main.py           # Entry point, CLI
│   ├── scanner.py        # GitHub scanning logic
│   ├── detector.py       # Technology detection
│   ├── classifier.py     # AI classification
│   ├── rate_limiter.py   # Rate limiting
│   ├── utils.py          # Helpers
│   └── config.py         # Config loader
├── tests/
│   ├── test_scanner.py
│   ├── test_detector.py
│   └── test_classifier.py
├── config/
│   ├── config.yaml       # Main config
│   └── config.example.yaml
├── logs/                 # Generated logs
├── .env                  # API keys (git-ignored)
├── .env.example          # Template
├── requirements.txt      # Dependencies
└── README.md
```

## License

Open source - use and modify as needed.

## Support

For issues or questions:
1. Check logs in `logs/scan.log`
2. Review this README
3. Check GitHub API status: https://www.githubstatus.com
4. Check OpenAI status: https://status.openai.com
