# Technology Radar - AI-Powered & Interactive

A world-class interactive technology radar with AI-powered data collection and stunning UI/UX, inspired by Thoughtworks. Features a dual-mode system: **manually curated** tech selections or **AI-discovered** comprehensive analysis from GitHub repositories.

## 🎯 Key Features

### 🔀 Dual Mode System (NEW!)
- **Manual Mode**: Clean, curated technology selections you control
- **AI Mode**: Comprehensive AI-discovered technologies from your GitHub organization
- **Toggle instantly** between both modes with a single click
- Perfect for both strategic overviews and detailed analysis

### 🤖 AI-Powered Technology Detection
- **Automatic Scanning**: Scans GitHub repositories to identify technologies
- **Domain-Aware Classification**: Segments by engineering domain (mobile, backend, frontend, infrastructure, etc.)
- **Temporal Analysis**: Tracks adoption trends over time (recent, legacy, active, stale repos)
- **Smart Ring Decisions**: AI-assisted classification into Adopt/Trial/Assess/Hold rings
- **Privacy Protection**: Sanitized public version removes sensitive internal data

### ✨ Premium Interactive UI
- **Modern Glassmorphism** design with dark/light themes
- **Zoom & Pan** with smooth interactions
- **Real-time Search** and filtering
- **Bidirectional Highlighting** between radar and list
- **Keyboard Shortcuts** for power users
- **SVG Export** for presentations
- **Fully Responsive** on all devices

## 🚀 Quick Start

### Step 1: Run the Radar Locally

**⚠️ Important:** Due to browser security (CORS), you must run a local server. Opening `index.html` directly won't work.

#### Easiest Method - Use the Startup Script

**macOS/Linux:**
```bash
./start.sh
```

**Windows:**
```cmd
start.bat
```

Then open **http://localhost:8000** in your browser.

#### Alternative Methods

```bash
# Option 1: Python (recommended)
python3 -m http.server 8000

# Option 2: Node.js
npx serve

# Option 3: PHP
php -S localhost:8000
```

### Step 2: Choose Your Mode

Once the radar is running, you'll see a **toggle switch** in the top-right header:

```
[Manual] ◯———◉ [AI]
```

- **Toggle LEFT (Manual)**: Shows `data.json` - your curated selections
- **Toggle RIGHT (AI)**: Shows `data.ai.json` - AI-discovered comprehensive data

The radar reloads automatically when you switch modes!

## 📝 How to Add Technologies (Manual Mode)

### Quick Add

1. **Open `data.json`** in your text editor
2. **Add a new entry**:

```json
{
  "name": "Technology Name",
  "quadrant": 3,
  "ring": 0,
  "description": "Brief description explaining the technology and our stance on it."
}
```

3. **Save the file**
4. **Refresh your browser** (or switch toggle off/on)

### Understanding the Fields

**`quadrant`** - Category (0-3):
- `0` = **Techniques** (practices, methodologies, processes)
- `1` = **Tools** (development tools, testing frameworks, DevOps tools)
- `2` = **Platforms** (infrastructure, cloud services, databases)
- `3` = **Languages & Frameworks** (programming languages and frameworks)

**`ring`** - Adoption Level (0-3):
- `0` = **Adopt** - Proven and recommended. Use these when appropriate.
- `1` = **Trial** - Worth pursuing. Worth investing to see if they have impact.
- `2` = **Assess** - Worth exploring to understand how they will affect you.
- `3` = **Hold** - Proceed with caution. Not recommended for new projects.

### Complete Examples

**Example 1 - Adding Kotlin to Adopt:**
```json
{
  "name": "Kotlin",
  "quadrant": 3,
  "ring": 0,
  "description": "Proven and recommended for Android and JVM development. Modern, concise, and fully interoperable with Java."
}
```

**Example 2 - Adding GitOps to Techniques/Adopt:**
```json
{
  "name": "GitOps",
  "quadrant": 0,
  "ring": 0,
  "description": "Git-based operational practices for infrastructure and application deployment. Proven approach for declarative infrastructure and continuous delivery."
}
```

**Example 3 - Adding Trivy to Tools/Assess:**
```json
{
  "name": "Trivy",
  "quadrant": 1,
  "ring": 2,
  "description": "Comprehensive security scanner for containers and other artifacts. Worth exploring for vulnerability detection in CI/CD pipelines."
}
```

### Moving Technologies Between Rings

1. **Open `data.json`**
2. **Find the technology** you want to move
3. **Change the `ring` value**
4. **Update the description** to explain the change
5. **Save and refresh**

**Example - Moving Go from Assess (2) to Trial (1):**
```json
{
  "name": "Go (Golang)",
  "quadrant": 3,
  "ring": 1,  // Changed from 2 to 1
  "description": "Fast, statically typed language for microservices. After successful POCs, now recommended for trial usage in production services."
}
```

### Removing Technologies

1. **Open `data.json`**
2. **Find and delete the entire entry** (including the curly braces)
3. **Remove the comma** if it's now the last entry
4. **Save and refresh**

⚠️ **Important:** Maintain valid JSON format - use commas between entries, but NOT after the last one.

## 🤖 How to Generate AI-Powered Tech Radar

The AI mode automatically scans your GitHub organization and generates a comprehensive technology radar with rich metadata.

### Prerequisites

- **Python 3.8+**
- **GitHub Personal Access Token** ([Create here](https://github.com/settings/tokens))
  - Required scopes: `repo`, `read:org`, `read:user`
- **OpenAI API Key** ([Get here](https://platform.openai.com/api-keys))

### Setup (One-Time)

1. **Navigate to data-etl directory:**
```bash
cd data-etl
```

2. **Install dependencies:**
```bash
pip3 install -r requirements.txt
```

3. **Create environment file:**
```bash
cp .env.example .env
```

4. **Edit `.env` and add your tokens:**
```bash
# .env
GITHUB_TOKEN=ghp_your_actual_github_token_here
OPENAI_API_KEY=sk-proj-your_actual_openai_key_here
```

⚠️ **Security:** Never commit `.env` to git! It's already in `.gitignore`.

5. **Configure your organization:**
```bash
# Edit config/config.yaml
# Change this line:
github:
  organizations:
    - your-organization-name  # Replace with your GitHub org
```

### Running the Scanner

**Basic usage (scan all repositories):**
```bash
cd data-etl/src
python main.py
```

**Limit to first 100 repos (recommended for testing):**
```bash
python main.py --limit 100
```

**Resume from checkpoint (if interrupted):**
```bash
python main.py --resume
```

**Start fresh (clear checkpoint):**
```bash
python main.py --fresh
```

**Combine options:**
```bash
python main.py --limit 50 --resume
```

### What the Scanner Does

The ETL pipeline will:

1. ✅ **Scan repositories** in your GitHub organization
2. 🔍 **Detect technologies** from file patterns, languages, and dependencies
3. 🤖 **Use AI** to determine repository domain (mobile, backend, infrastructure, etc.)
4. 📊 **Analyze temporal patterns** (recent adoption, legacy usage, activity trends)
5. 🎯 **Classify technologies** into rings (Adopt/Trial/Assess/Hold) with AI assistance
6. 📈 **Generate domain breakdowns** showing adoption per engineering domain
7. 📁 **Output two files**:
   - `../data.ai.json` - **Sanitized** (safe for public GitHub Pages)
   - `../data.ai.full.json` - **Full metadata** (internal use only, gitignored)

### Output Files Explained

#### `data.ai.json` (Public/Sanitized)
- ✅ Safe to commit to public GitHub
- ✅ No sensitive internal information
- ✅ Contains: tech names, classifications, descriptions, AI confidence
- ❌ Excludes: repository names, usage counts, temporal details

**What's included:**
```json
{
  "name": "React",
  "quadrant": 3,
  "ring": 0,
  "description": "JavaScript library for building user interfaces...",
  "confidence": 0.92,
  "needs_review": false,
  "metadata": {
    "ai_confidence": "high",
    "ai_model": "gpt-4o-mini"
  }
}
```

#### `data.ai.full.json` (Internal)
- ❌ **DO NOT commit** to public repositories (auto-gitignored)
- ✅ For internal analysis and decision-making
- ✅ Contains everything: repos, usage %, trends, activity scores

**Additional fields:**
```json
{
  // ... all fields from data.ai.json, plus:
  "metadata": {
    "repos_count": 143,
    "usage_percentage": 48.6,
    "total_repos": 294,
    "temporal_data": {
      "repos_list": ["repo-1", "repo-2", ...],
      "recent_repos": 12,
      "active_repos": 98,
      "trend": "STABLE",
      "by_domain": { /* domain-specific metrics */ }
    },
    "decision_factors": [
      "✓ High usage (48.6%)",
      "• 68% of repos actively maintained"
    ]
  }
}
```

### Privacy & Security 🔒

The dual-file system protects your internal data:

| File | Public Safe? | Contains Sensitive Data? | Commit to GitHub? |
|------|--------------|--------------------------|-------------------|
| `data.json` | ✅ Yes | ❌ No | ✅ Yes |
| `data.ai.json` | ✅ Yes | ❌ No (sanitized) | ✅ Yes |
| `data.ai.full.json` | ❌ No | ✅ Yes (repos, usage) | ❌ No (gitignored) |

**What's removed in sanitization:**
- Repository names
- Repository counts and usage percentages
- Total org repository count
- Temporal data (activity patterns, trends)
- Internal metrics (usage scores, recency scores)
- Decision rationales

**What's kept:**
- Technology names
- Ring classifications
- Quadrant assignments
- Descriptions
- AI confidence levels
- Metadata about AI model used

## 🎛️ Using the AI/Manual Toggle

### Toggle Location

The toggle switch is in the **top-right header** of the radar, next to the theme/export buttons.

### Toggle States

```
Manual Mode:  [●———○] Manual ← AI
AI Mode:      [○———●] Manual → AI
```

### When to Use Each Mode

**Manual Mode (`data.json`):**
- ✅ Strategic discussions and presentations
- ✅ High-level technology decisions
- ✅ Executive summaries
- ✅ Clean, curated view
- ✅ Full control over content

**AI Mode (`data.ai.json`):**
- ✅ Comprehensive technology audit
- ✅ Discovering forgotten or shadow tech
- ✅ Understanding actual usage patterns
- ✅ Data-driven decision making
- ✅ Engineering team reviews

### Toggle Behavior

- **Instant reload** - Data refreshes immediately when toggled
- **No page refresh** needed
- **Preference not saved** - Always starts in AI mode (right/checked)
- **Works offline** - Both JSON files are local

## 📋 Data Schema Reference

### Manual Mode Schema (`data.json`)

Minimal, clean schema:

```json
[
  {
    "name": "string",           // Required: Technology name
    "quadrant": 0-3,           // Required: Category (0=Techniques, 1=Tools, 2=Platforms, 3=Languages)
    "ring": 0-3,               // Required: Ring (0=Adopt, 1=Trial, 2=Assess, 3=Hold)
    "description": "string"    // Required: Brief explanation
  }
]
```

### AI Mode Schema (`data.ai.json`)

Enhanced with AI metadata:

```json
[
  {
    "name": "string",
    "quadrant": 0-3,
    "ring": 0-3,
    "description": "string",
    "confidence": 0.0-1.0,     // AI confidence score
    "needs_review": boolean,   // Flags technologies needing human review
    "metadata": {
      "ai_confidence": "high|medium|low",
      "ai_model": "gpt-4o-mini"
    }
  }
]
```

## ⚙️ Configuration

### Scanner Configuration (`data-etl/config/config.yaml`)

```yaml
github:
  organizations:
    - your-org-name           # Your GitHub organization
  repo_limit: 0               # 0 = all repos, or set a number (e.g., 100)
  min_stars: 0
  include_private: true
  include_archived: false

openai:
  model: gpt-4o-mini          # Fast and cost-effective
  max_tokens: 1000
  temperature: 0.3            # Lower = more consistent

classification:
  min_repos: 2                # Min repos to include a technology
  thresholds:
    adopt: 0.70               # 70%+ usage → Adopt
    trial: 0.40               # 40-70% usage → Trial
    assess: 0.10              # 10-40% usage → Assess
    # Below 10% → Hold

  # Domain-aware minimum repos
  min_repos_by_domain:
    infrastructure: 1         # Centralized: single infra repo counts
    data: 1                   # Centralized: data pipelines often in one repo
    backend: 2                # Distributed: microservices across repos
    frontend: 2               # Distributed: multiple apps
    mobile: 2                 # Distributed: multiple apps

checkpoint:
  enabled: true
  save_interval: 10           # Save progress every 10 repos

rate_limit:
  max_per_minute: 60
  safety_threshold: 100       # Pause if remaining requests < 100
```

## 🎨 Customization

### Changing Ring Colors

**Edit `radar.js` (around line 27-32):**
```javascript
this.rings = [
    { name: 'Adopt', radius: 0.25, color: '#10b981' },   // Green
    { name: 'Trial', radius: 0.5, color: '#06b6d4' },    // Cyan
    { name: 'Assess', radius: 0.75, color: '#f59e0b' },  // Amber
    { name: 'Hold', radius: 1.0, color: '#ef4444' }      // Red
];
```

### Changing Quadrant Names

**Edit `radar.js` (around line 20-25):**
```javascript
this.quadrants = [
    { name: 'Techniques', angle: 0 },
    { name: 'Tools', angle: 90 },
    { name: 'Platforms', angle: 180 },
    { name: 'Languages & Frameworks', angle: 270 }
];
```

**Also update filter buttons in `index.html`** (lines 62-66):
```html
<button class="filter-btn" data-quadrant="0">Techniques</button>
<button class="filter-btn" data-quadrant="1">Tools</button>
<button class="filter-btn" data-quadrant="2">Platforms</button>
<button class="filter-btn" data-quadrant="3">Languages & Frameworks</button>
```

### Changing Theme Colors

**Edit `styles.css` (lines 1-21) CSS variables:**
```css
:root {
    --bg-primary: #0f0f23;
    --bg-secondary: #1a1a2e;
    --accent-primary: #8b5cf6;      /* Purple */
    --accent-secondary: #06b6d4;    /* Cyan */
    --ring-adopt: #10b981;          /* Green */
    --ring-trial: #06b6d4;          /* Cyan */
    --ring-assess: #f59e0b;         /* Amber */
    --ring-hold: #ef4444;           /* Red */
}
```

## ⌨️ Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `Scroll` | Zoom in/out |
| `Drag` | Pan the radar view |
| `R` or `0` | Reset zoom and pan |
| `+` or `=` | Zoom in |
| `-` | Zoom out |
| `T` | Toggle theme (dark/light) |
| `E` | Export as SVG |

## 🔧 Troubleshooting

### Radar not loading
**Symptoms:** Blank page or error message

**Solutions:**
1. Make sure you're using a local server (not opening `file://`)
2. Check browser console (F12) for errors
3. Validate JSON at [jsonlint.com](https://jsonlint.com)
4. Hard refresh: `Ctrl+Shift+R` (Win) or `Cmd+Shift+R` (Mac)

### Toggle not switching data
**Symptoms:** Same data shown for both modes

**Solutions:**
1. Clear browser cache: `Ctrl+Shift+R` / `Cmd+Shift+R`
2. Check both files exist: `ls -la data*.json`
3. Verify files are different: `diff data.json data.ai.json`
4. Check browser console for fetch errors

### AI scan failing
**Symptoms:** Scanner crashes or produces errors

**Common issues:**
1. **Rate limit hit:** Wait a few minutes or reduce `max_per_minute` in config
2. **Invalid tokens:** Verify `GITHUB_TOKEN` and `OPENAI_API_KEY` in `.env`
3. **Network issues:** Check internet connection and GitHub API status
4. **Large org:** Use `--limit 100` for initial testing

### Invalid JSON format
**Symptoms:** Radar doesn't load after editing `data.json`

**Common mistakes:**
```json
// ❌ WRONG - Missing comma
{
  "name": "React"
  "quadrant": 3
}

// ❌ WRONG - Extra comma after last entry
[
  { "name": "React", "quadrant": 3, "ring": 0 },
]

// ✅ CORRECT
[
  { "name": "React", "quadrant": 3, "ring": 0 },
  { "name": "Vue", "quadrant": 3, "ring": 1 }
]
```

**Fix:** Validate at [jsonlint.com](https://jsonlint.com)

### Scanner can't find repositories
**Symptoms:** "0 repositories found"

**Solutions:**
1. Verify organization name in `config/config.yaml`
2. Check `GITHUB_TOKEN` has correct scopes (`repo`, `read:org`)
3. Ensure token has access to the organization
4. Check `include_private` and `include_archived` settings

## 📁 File Structure

```
tech-radar/
├── index.html              # Main HTML structure
├── styles.css              # All styling and themes
├── radar.js                # Radar logic and interactions
├── data.json               # Manual curated data (YOUR EDITS)
├── data.ai.json            # AI-generated sanitized data (SAFE FOR PUBLIC)
├── data.ai.full.json       # AI-generated full data (GITIGNORED - INTERNAL ONLY)
├── .gitignore              # Excludes data.ai.full.json and temp files
├── README.md               # This file
├── start.sh                # Startup script for macOS/Linux
├── start.bat               # Startup script for Windows
│
└── data-etl/               # AI-powered ETL pipeline
    ├── src/
    │   ├── main.py                  # Entry point with CLI arguments
    │   ├── scanner.py               # GitHub repository scanner
    │   ├── domain_detector.py       # AI-powered domain detection
    │   ├── temporal_analyzer.py     # Temporal pattern analysis
    │   ├── classifier_enhanced.py   # AI-assisted classification
    │   ├── output_generator.py      # Dual-file generation (sanitized + full)
    │   ├── progress.py              # Checkpoint/resume management
    │   └── rate_limiter.py          # GitHub API rate limiting
    │
    ├── config/
    │   └── config.yaml              # Configuration file
    │
    ├── .env.example                 # Template for environment variables
    ├── .env                         # Your tokens (GITIGNORED)
    ├── .gitignore                   # Excludes .env, logs, checkpoints
    ├── requirements.txt             # Python dependencies
    ├── .scan_progress.json          # Checkpoint file (auto-generated)
    └── README.md                    # ETL detailed documentation
```

## 🎯 Best Practices

### For Manual Mode (`data.json`)

**When to add technologies:**
- ✅ Technology is being actively used or seriously considered
- ✅ There's a clear opinion about its strategic fit
- ✅ It's relevant to your team's current or future work

**When to update ring positions:**
- **→ Adopt**: After successful production use in multiple projects
- **→ Trial**: When you want teams to start experimenting seriously
- **→ Assess**: When a technology first appears on your radar
- **→ Hold**: When you want to discourage further adoption

**Writing good descriptions:**
- Be specific about **why** it's in that ring
- Mention context: "for microservices" or "for frontend development"
- Keep it concise (1-3 sentences)
- Focus on the "why" not just the "what"

### For AI Mode (Scanner)

**Initial setup:**
1. Start with `--limit 50` to test configuration
2. Review output and adjust thresholds in config
3. Run full scan once satisfied
4. Schedule regular scans (weekly/monthly)

**Regular maintenance:**
1. Run scanner periodically to catch new technologies
2. Review `needs_review: true` entries in `data.ai.full.json`
3. Adjust classification thresholds based on your org's size
4. Keep `.env` tokens fresh and secured

**Using the full metadata:**
1. Use `data.ai.full.json` for internal analysis
2. Check `temporal_data.repos_list` to see where tech is used
3. Review `decision_factors` to understand AI reasoning
4. Examine domain breakdowns for context-specific decisions

## 🚀 Deployment

### GitHub Pages (Recommended)

1. **Push to GitHub:**
```bash
git add .
git commit -m "Update tech radar"
git push
```

2. **Enable GitHub Pages:**
   - Go to repository Settings → Pages
   - Select `main` branch
   - Save

3. **Access at:**
   - `https://username.github.io/repo-name`

**Security Note:** Only `data.ai.json` is committed (sanitized). The full version (`data.ai.full.json`) is gitignored.

### Netlify

1. **Drag and drop** your folder to [netlify.com/drop](https://netlify.com/drop)
2. **Done!** - Instant URL

### Vercel

```bash
npx vercel --prod
```

## 💡 Tips for Teams

### For Technology Leadership
1. **Use Manual Mode** for strategic discussions
2. **Reference AI Mode** for data-driven decisions
3. **Update quarterly** or when major tech decisions are made
4. **Document reasons** in descriptions for future reference

### For Engineering Teams
1. **Start with AI Mode** to audit current usage
2. **Switch to Manual Mode** to see strategic direction
3. **Compare both modes** to identify gaps
4. **Propose changes** by editing `data.json` and opening PRs

### For Presentations
1. **Export to SVG** (`E` key) for high-quality slides
2. **Use zoom** to focus on specific areas
3. **Filter by quadrant** to discuss categories separately
4. **Toggle theme** to match presentation background

## 🌍 Organization-Agnostic Design

This tool works with **any GitHub organization** without modification:

- ✅ **No hardcoded patterns** - AI analyzes repository structure dynamically
- ✅ **No org-specific logic** - All organization names in `config/config.yaml`
- ✅ **Fully configurable** - All thresholds and rules in configuration
- ✅ **Universal domains** - Standard domains work for any organization
- ✅ **Extensible** - Easy to add custom domains or classification rules

**To use with your organization:**
1. Edit `data-etl/config/config.yaml`
2. Replace organization name
3. Set API keys in `.env`
4. Run - it adapts automatically!

## 📝 CLI Reference

### Scanner Commands

```bash
# Basic scan
python main.py

# Limit repositories (testing)
python main.py --limit 100

# Resume from checkpoint
python main.py --resume

# Start fresh (clear checkpoint)
python main.py --fresh

# Specify custom config
python main.py --config ../custom-config.yaml

# Override organization
python main.py --org my-other-org

# Dry run (don't write output)
python main.py --dry-run

# Verbose logging
python main.py --verbose

# Combine flags
python main.py --limit 50 --resume --verbose
```

### Common Workflows

**First-time setup:**
```bash
cd data-etl
pip3 install -r requirements.txt
cp .env.example .env
# Edit .env with your tokens
python src/main.py --limit 10  # Test with 10 repos
```

**Regular scan:**
```bash
cd data-etl/src
python main.py --limit 100 --resume
```

**Full organization scan:**
```bash
cd data-etl/src
python main.py
```

**Clean slate:**
```bash
cd data-etl/src
python main.py --fresh
```

## 🤝 Contributing

### To suggest technology changes:

**Manual Mode:**
1. Edit `data.json`
2. Commit with clear message: `"Add Kotlin to Adopt ring"`
3. Open pull request

**AI Mode:**
1. Re-run scanner: `python main.py --limit 100`
2. Review generated `data.ai.json`
3. Commit and push

### To improve the tool:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit pull request

## 📄 License

Open source - use and modify as needed for your organization.

## 🙏 Credits

**Built with:**
- Frontend: Vanilla JavaScript, CSS3, SVG
- ETL Pipeline: Python 3.8+, PyGithub, OpenAI API
- AI Models: GPT-4o-mini for classification and domain detection
- Design: Inspired by Thoughtworks Technology Radar

---

**Made with ❤️ for engineering teams who care about their technology stack**

For detailed ETL documentation, see [`data-etl/README.md`](data-etl/README.md)
