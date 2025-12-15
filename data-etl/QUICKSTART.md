# Quick Start Guide

Get started with Tech Radar Data ETL in 5 minutes.

## 1. Install Dependencies

```bash
cd data-etl
pip install -r requirements.txt
```

## 2. Setup Environment Variables

Create `.env` file:

```bash
cp .env.example .env
```

Edit `.env` and add your tokens:

```bash
# .env
GITHUB_TOKEN=ghp_your_real_token_here
OPENAI_API_KEY=sk-proj-your_real_key_here
```

### Getting Tokens

**GitHub Token:**
1. Go to https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Select scopes: `repo`, `read:org`, `read:user`
4. Copy the token

**OpenAI API Key:**
1. Go to https://platform.openai.com/api-keys
2. Click "Create new secret key"
3. Copy the key

⚠️ **Never commit `.env` to git!**

## 3. Configure Organization

Edit `config/config.yaml`:

```yaml
github:
  organizations:
    - bazaartechnologies  # Change this to your org
```

## 4. Run the Scanner

```bash
cd src
python main.py
```

You'll see progress like:

```
Scanning repositories...
[===============>              ] 15/30 (50%) | ETA: 3m 20s | repo-name

Classifying technologies with AI...
  React (25/30 repos, 83.3%)
  TypeScript (22/30 repos, 73.3%)
  Docker (20/30 repos, 66.7%)
  ...

✓ Written 45 technologies to ../data.ai.json
```

## 5. Review Output

Check the generated file:

```bash
cat ../data.ai.json
```

You'll see entries like:

```json
[
  {
    "name": "React",
    "quadrant": 3,
    "ring": 0,
    "description": "JavaScript library for building user interfaces. Found in 83% of repositories, indicating strong adoption. Recommended for new frontend projects.",
    "metadata": {
      "repos_count": 25,
      "usage_percentage": 83.3,
      "total_repos": 30,
      "confidence": "high"
    }
  }
]
```

## 6. Use in Tech Radar

When satisfied with the results:

```bash
# Backup current data (if exists)
cp ../data.json ../data.json.backup

# Use AI-generated data
cp ../data.ai.json ../data.json

# Refresh your tech radar in browser
```

## Common Issues

### "Authentication failed"
- Check your GitHub token in `.env`
- Verify token has correct scopes (`repo`, `read:org`)

### "OpenAI API error"
- Check API key in `.env`
- Verify your OpenAI account has credits
- Model name should be `gpt-4o-mini`

### Empty or few results
- Verify organization name is correct
- Check if repos contain recognizable tech files (package.json, etc.)
- Look at logs: `cat logs/scan.log`

### Rate limit errors
- Wait for rate limit to reset (check logs for time)
- Reduce `max_per_minute` in config.yaml
- Use `--resume` flag to continue from checkpoint

## Next Steps

- **Customize classifications**: Edit AI descriptions in `data.ai.json`
- **Adjust thresholds**: Modify ring thresholds in `config.yaml`
- **Exclude technologies**: Add patterns to `exclude_patterns` in config
- **Schedule scans**: Setup cron job to run weekly
- **Review README**: Full documentation in `README.md`

## CLI Options

```bash
# Dry run (preview without saving)
python main.py --dry-run

# Resume from checkpoint
python main.py --resume

# Start fresh (clear checkpoint)
python main.py --fresh

# Scan different organization
python main.py --org another-org

# Verbose output
python main.py --verbose

# Custom output file
python main.py --output custom.json

# Help
python main.py --help
```

## Tips

1. **Review AI classifications** - AI is smart but not perfect
2. **Adjust manually** - Edit `data.ai.json` before renaming
3. **Keep metadata** - Helps understand AI decisions
4. **Run periodically** - Tech stacks evolve, update quarterly
5. **Compare with current** - Use git diff to see changes

## Support

If you encounter issues:
1. Check logs: `tail -f logs/scan.log`
2. Review README.md troubleshooting section
3. Run with `--verbose` flag for details
4. Check GitHub/OpenAI API status pages
