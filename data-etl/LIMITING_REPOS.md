# Repository Limiting Feature

The ETL tool supports limiting the number of repositories scanned. This is useful for:
- **Quick testing** - Test the pipeline with a small sample
- **Fast iterations** - Quickly validate changes without scanning all repos
- **Cost control** - Limit OpenAI API calls during development
- **Targeted scans** - Focus on most important repos first

## Usage

### 1. Via Command Line (Recommended)

```bash
# Scan only first 50 repos
python3 main.py --limit 50

# Quick test: 100 repos in dry-run mode
python3 main.py --limit 100 --dry-run

# Scan 200 repos and save output
python3 main.py --limit 200
```

### 2. Via Configuration File

Edit `config/config.yaml`:

```yaml
github:
  organizations:
    - bazaartechnologies

  # Set repository limit (0 = unlimited)
  repo_limit: 100  # Scan only first 100 repos
```

Then run normally:
```bash
python3 main.py
```

### 3. Priority Order

Command line flag **overrides** config file:

```bash
# Config says 100, but this will scan 50
python3 main.py --limit 50
```

## How It Works

The limiter:
1. Fetches ALL repositories from GitHub
2. Shows total count: `Found 332 repositories, limiting to 100`
3. Scans only the first N repositories
4. Applies filters (archived, forks, etc.) to the limited set
5. Generates radar data based on the limited sample

## Examples

### Quick 5-Minute Test
```bash
# Scan 20 repos to test the pipeline
python3 main.py --limit 20 --dry-run

# Output:
# Found 332 repositories in bazaartechnologies, limiting to 20
# ... scans 20 repos ...
# Found 15 unique technologies
```

### Production-Like Test
```bash
# Scan 100 repos for a representative sample
python3 main.py --limit 100

# This will:
# - Scan 100 repos (~10 minutes)
# - Generate data.ai.json
# - Call OpenAI for each unique technology found
```

### Full Scan
```bash
# Scan all repos (no limit)
python3 main.py

# Or explicitly set to 0
python3 main.py --limit 0

# Or set in config.yaml:
# repo_limit: 0
```

## Tips

### For Testing
- Start with `--limit 10 --dry-run` to test quickly
- Increase to 50-100 for realistic sample
- Use `--verbose` to see detailed progress

### For Production
- Remove limit or set to 0 for complete scan
- First 100 repos usually capture major technologies
- Can run multiple scans: first 100, then full scan later

### With Resume
```bash
# Scan first 100
python3 main.py --limit 100

# Later, scan all (will re-scan same repos)
python3 main.py --fresh

# Or use checkpoint to skip already scanned
python3 main.py --resume --limit 200
```

## Which Repos Are Selected?

The limiter takes the **first N repositories** as returned by GitHub API, which is typically:
- Ordered by push date (most recently updated first)
- Or by creation date (newest first)

This means you'll get the **most active repositories**, which usually represent your current tech stack better.

### To scan specific repos:
```yaml
github:
  organizations:
    - bazaartechnologies

  # Exclude patterns to focus on specific repos
  exclude_repos:
    - "test-*"      # Exclude test repos
    - "*-archived"  # Exclude archived
    - "legacy-*"    # Exclude legacy
```

## Cost Estimation

**GitHub API**: Free (within rate limits)
- 5,000 requests/hour
- ~3-5 API calls per repo
- 100 repos ≈ 300-500 API calls (well within limit)

**OpenAI API**: Paid
- ~1,000 tokens per technology classification
- Cost: ~$0.00015 per technology (gpt-4o-mini)
- 50 unique technologies ≈ $0.0075
- 100 repos typically find 30-60 unique technologies

**Time Estimation**:
- 10 repos: ~1-2 minutes
- 50 repos: ~5-8 minutes
- 100 repos: ~10-15 minutes
- 332 repos: ~30-45 minutes

## Validation

To see how many repos would be scanned:

```bash
# Dry run shows the limit
python3 main.py --limit 100 --dry-run --verbose

# Check logs
tail -f logs/scan.log | grep "limiting to"
# Output: Found 332 repositories in bazaartechnologies, limiting to 100
```

## FAQ

**Q: Does the limit affect AI classification?**
A: Yes, usage percentages are based on the limited set. If you scan 100 repos and React is in 80, it shows 80% usage.

**Q: Can I scan specific repos by name?**
A: Not directly. Use exclude patterns to filter, or modify the scanner code to select by name.

**Q: Does --resume work with --limit?**
A: Yes, but be careful. If you scanned 50 then resume with --limit 100, it will scan repos 51-100.

**Q: What if I want repos ordered by stars?**
A: Currently not supported. GitHub API returns by push date. You could modify scanner.py to sort by stars.

**Q: Can I have different limits per organization?**
A: Not currently. The limit applies to all organizations equally.

## Summary

```bash
# Quick commands to remember:

# Fast test (2 min)
python3 main.py --limit 20 --dry-run

# Medium test (10 min)
python3 main.py --limit 100 --dry-run

# Production sample (15 min)
python3 main.py --limit 100

# Full scan (30-45 min)
python3 main.py

# Or set in config.yaml
repo_limit: 100
```

The limit feature makes the ETL tool much more practical for iterative development and testing!
