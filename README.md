# Bazaar Tech Radar

Interactive visualization of our technology landscape and strategic choices, inspired by Thoughtworks Technology Radar.

🔗 **Live Demo:** https://techradar.bazaar-engineering.com/

## Features

### 🔀 Dual Mode System
- **Manual Mode**: Curated strategic technology selections
- **AI Mode**: Comprehensive AI-discovered technologies from GitHub repositories
- **Toggle instantly** between modes with one click

### ✨ Interactive UI
- Modern glassmorphism design with dark/light themes
- Real-time search and filtering by quadrant
- Bidirectional highlighting between radar and list
- Click any technology for detailed information
- SVG export for presentations
- Keyboard shortcuts (T: theme, E: export)

## Quick Start

Visit **https://techradar.bazaar-engineering.com/** in your browser.

### Local Development
```bash
# Serve locally
python3 -m http.server 8000

# Open http://localhost:8000
```

## Understanding the Radar

### Rings (Adoption Level)
- **Adopt** - Proven and recommended for production use
- **Trial** - Worth pursuing in select projects
- **Assess** - Worth exploring and evaluating
- **Hold** - Proceed with caution, consider alternatives

### Quadrants (Categories)
- **Techniques** - Practices, methodologies, processes
- **Tools** - Development tools, testing frameworks, DevOps tools
- **Platforms** - Infrastructure, cloud services, databases
- **Languages & Frameworks** - Programming languages and frameworks

## Managing Technologies (Manual Mode)

### Adding a Technology

Edit `data.json`:

```json
{
  "name": "Kotlin",
  "quadrant": 3,
  "ring": 0,
  "description": "Proven and recommended for Android and JVM development."
}
```

**Field reference:**
- `quadrant`: 0=Techniques, 1=Tools, 2=Platforms, 3=Languages
- `ring`: 0=Adopt, 1=Trial, 2=Assess, 3=Hold

### Moving Between Rings

1. Find the technology in `data.json`
2. Change the `ring` value
3. Update the `description` to explain why
4. Commit and push

### Best Practices
- Be specific about **why** a technology is in that ring
- Keep descriptions concise (1-3 sentences)
- Focus on strategic context, not just features
- Update quarterly or when major decisions are made

## AI-Powered Tech Radar

The AI mode automatically scans GitHub repositories and generates a comprehensive technology radar.

### Quick Setup

```bash
cd data-etl

# Install dependencies
pip3 install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add GITHUB_TOKEN and OPENAI_API_KEY

# Edit config/config.yaml with your organization name

# Run scanner
cd src
python main.py --limit 100  # Start with 100 repos for testing
```

### What It Does

1. Scans all repositories in your GitHub organization
2. Detects technologies from files, languages, and dependencies
3. Uses AI to classify by domain (mobile, backend, infrastructure, etc.)
4. Analyzes usage patterns and temporal trends
5. Automatically classifies into Adopt/Trial/Assess/Hold rings
6. Generates two files:
   - `data.ai.json` - Sanitized (safe for public GitHub Pages)
   - `data.ai.full.json` - Full metadata (internal use, gitignored)

### Privacy & Security

The dual-file system protects internal data:

| File | Public Safe? | Commit to GitHub? |
|------|--------------|-------------------|
| `data.json` | ✅ Yes | ✅ Yes |
| `data.ai.json` | ✅ Yes (sanitized) | ✅ Yes |
| `data.ai.full.json` | ❌ No (has repo names, usage stats) | ❌ No (gitignored) |

**For detailed ETL documentation**, see [`data-etl/README.md`](data-etl/README.md)

## Using the AI/Manual Toggle

The toggle switch is in the top-right header. Click to switch between:
- **Manual**: Strategic, curated view from `data.json`
- **AI**: Comprehensive, auto-discovered view from `data.ai.json`

Data reloads instantly when toggled.

## File Structure

```
├── index.html           # Main page
├── styles.css           # Styling and themes
├── radar.js             # Interactive radar logic
├── data.json            # Manual curated data
├── data.ai.json         # AI-generated (public, sanitized)
└── data-etl/            # AI scanner (see data-etl/README.md)
```

## Deployment

### GitHub Pages

1. Push to GitHub
2. Go to Settings → Pages
3. Select `main` branch → Save
4. Access at `https://username.github.io/repo-name`

### Custom Domain

1. Add CNAME record in your DNS pointing to `username.github.io`
2. Create `CNAME` file in repo with your domain
3. Enable HTTPS in GitHub Pages settings

## Troubleshooting

**Radar not loading:**
- Use a local server (not `file://`)
- Hard refresh: `Cmd+Shift+R` (Mac) or `Ctrl+Shift+R` (Windows)

**Toggle not switching data:**
- Clear browser cache with hard refresh
- Check both `data.json` and `data.ai.json` exist

**Invalid JSON:**
- Validate at [jsonlint.com](https://jsonlint.com)
- Common: missing commas or comma after last entry

**AI scanner failing:**
- Verify tokens in `.env`
- Start with `--limit 50` for testing
- Check `data-etl/README.md` for detailed troubleshooting

## Contributing

### Suggest Technology Changes
1. Edit `data.json`
2. Commit: `"Add Kotlin to Adopt ring"`
3. Open pull request

### Improve the Tool
1. Fork repository
2. Create feature branch
3. Submit pull request

## Credits

- Design inspired by Thoughtworks Technology Radar
- Built with Vanilla JavaScript, CSS3, SVG
- AI-powered by OpenAI GPT-4o-mini
- Scans GitHub repos using PyGithub

---

**Made for engineering teams who care about their technology stack** ❤️
