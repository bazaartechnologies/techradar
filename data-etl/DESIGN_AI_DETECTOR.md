# AI-Driven Technology Detection Architecture

## Overview

Replace hardcoded technology detection with an AI-driven, agnostic discovery system that can detect ANY technology dynamically.

## Current Problems

1. **Hardcoded Detection**: Only detects technologies explicitly coded in detector.py
2. **Missing Technologies**: GraphQL, gRPC, Prisma, tRPC, and many others are invisible
3. **Maintenance Burden**: Every new technology requires code changes
4. **Cannot Discover**: No way to find emerging/unknown technologies

## New Architecture

### Three-Phase Flow

```
┌─────────────────────────────────────────────────────────────┐
│ PHASE 1: AI Triage (Shallow Scan)                          │
│ Cost: Low | Speed: Fast | Input: File tree only            │
└─────────────────────────────────────────────────────────────┘
Repository → Get file tree (GitHub API)
           ↓
           AI analyzes structure and returns:
           {
             "relevant_files": ["package.json", "schema.graphql", "*.proto"],
             "rationale": "Detected Node.js, GraphQL schema, gRPC services"
           }

┌─────────────────────────────────────────────────────────────┐
│ PHASE 2: Deep Analysis (Targeted Scan)                      │
│ Cost: Medium | Speed: Medium | Input: Specific file content│
└─────────────────────────────────────────────────────────────┘
           Fetch ONLY AI-selected files
           ↓
           AI analyzes content and extracts:
           {
             "technologies": {
               "languages": ["TypeScript", "JavaScript"],
               "frameworks": ["React", "Apollo GraphQL"],
               "tools": ["gRPC", "Protocol Buffers", "Jest"],
               "platforms": ["Docker", "Node.js"]
             },
             "evidence": {
               "GraphQL": "schema.graphql defines types + apollo-server in deps",
               "gRPC": "payment.proto defines service Payment",
               "Jest": "jest in devDependencies"
             },
             "confidence": "high"
           }

┌─────────────────────────────────────────────────────────────┐
│ PHASE 3: Validation & Aggregation (Existing System)        │
│ Cost: None | Speed: Fast | No AI needed                    │
└─────────────────────────────────────────────────────────────┘
           Aggregate across all repos
           ↓
           Apply domain-aware thresholds (min_repos_by_domain)
           ↓
           Apply usage criteria (adopt/trial/assess/hold)
           ↓
           AI classifier generates descriptions
           ↓
           Output to data.ai.json
```

## Implementation Design

### Class: AITechnologyDetector

```python
class AITechnologyDetector:
    """AI-driven technology detection using OpenAI."""

    def __init__(self, openai_api_key: str, config: dict):
        self.client = OpenAI(api_key=openai_api_key)
        self.config = config
        self.cache = {}  # Cache AI responses per repo

    def detect_technologies(self, repo: Repository) -> Dict[str, Set[str]]:
        """
        Main entry point - detects technologies in repository.

        Flow:
        1. Get file tree from GitHub
        2. Phase 1: AI triage (which files to read?)
        3. Phase 2: Fetch files + AI analysis
        4. Return structured technology dict
        """

    def _phase1_triage(self, repo: Repository) -> List[str]:
        """
        Phase 1: AI analyzes file tree and selects relevant files.

        Input: Repository file tree (names only, no content)
        Output: List of file paths to analyze
        """

    def _phase2_deep_analysis(self, repo: Repository, files: List[str]) -> Dict:
        """
        Phase 2: AI analyzes file contents and extracts technologies.

        Input: File contents from selected files
        Output: {technologies: {...}, evidence: {...}, confidence: ...}
        """

    def _get_file_tree(self, repo: Repository, max_depth: int = 3) -> List[str]:
        """Get repository file tree (paths only) up to max_depth."""

    def _fetch_file_contents(self, repo: Repository, paths: List[str]) -> Dict[str, str]:
        """Fetch content of specific files."""

    def aggregate_technologies(self, all_repo_techs: List[Dict]) -> Dict[str, int]:
        """Aggregate technologies across all repositories (same as before)."""
```

### AI Prompts

#### Phase 1: Triage Prompt

```
You are a technology detection expert analyzing a software repository.

**Your task**: Analyze the file structure and identify which files contain technology information.

**Repository**: {repo_name}
**File Tree** (up to 3 levels deep):
{file_tree}

**Look for**:
- Dependency manifests: package.json, pom.xml, go.mod, Cargo.toml, requirements.txt, Pipfile, composer.json, Gemfile, etc.
- Configuration files: Dockerfile, docker-compose.yml, .github/workflows/*.yml, terraform/*.tf, kubernetes/*.yaml
- Schema files: *.graphql, *.gql, *.proto, schema.sql, migrations/*
- Framework indicators: next.config.js, nuxt.config.js, angular.json, tsconfig.json
- Build tools: Makefile, webpack.config.js, vite.config.ts, rollup.config.js

**Respond in JSON**:
{
  "relevant_files": ["path/to/file1", "path/to/file2"],
  "rationale": "Brief explanation of what technologies you expect to find"
}

**Important**:
- Select ONLY files that definitively indicate technologies
- Limit to max 10 most important files
- Prioritize root-level dependency manifests
- Include schema/config files if they indicate specific technologies
```

#### Phase 2: Deep Analysis Prompt

```
You are a technology detection expert analyzing repository files.

**Your task**: Extract ALL technologies from these files.

**Repository**: {repo_name}

**Files analyzed**:
{files_with_content}

**Your task**:
1. Identify programming languages, frameworks, tools, and platforms
2. Provide evidence for each technology (which file + why)
3. Rate your confidence (high/medium/low)

**Respond in JSON**:
{
  "technologies": {
    "languages": ["TypeScript", "Python"],
    "frameworks": ["React", "Apollo GraphQL", "FastAPI"],
    "tools": ["Jest", "gRPC", "ESLint", "Docker"],
    "platforms": ["Node.js", "PostgreSQL", "Redis"]
  },
  "evidence": {
    "React": "react in package.json dependencies",
    "GraphQL": "schema.graphql defines types + apollo-server in deps",
    "gRPC": "services.proto defines gRPC service definitions",
    "PostgreSQL": "postgres connection in config + pg npm package"
  },
  "confidence": "high"
}

**Categories**:
- **languages**: Programming languages (Python, JavaScript, TypeScript, Go, Java, etc.)
- **frameworks**: Application frameworks (React, Django, Express, Spring Boot, etc.)
- **tools**: Development tools (Jest, ESLint, Webpack, gRPC, Protocol Buffers, etc.)
- **platforms**: Infrastructure & services (Docker, Kubernetes, PostgreSQL, Redis, AWS, etc.)

**Important**:
- Be comprehensive - include ALL technologies found
- Use canonical names (e.g., "PostgreSQL" not "postgres", "GraphQL" not "graphql")
- Include version managers as tools (npm, pip, Maven, Gradle)
- Infer technologies from imports/configurations (e.g., gRPC from .proto files)
```

## Key Benefits

### 1. **Truly Agnostic**
- No hardcoded patterns
- Discovers technologies not in code
- Works for future/unknown technologies

### 2. **Comprehensive**
- Detects GraphQL from: `.graphql` files, `apollo-server`, `graphql` package, schema definitions
- Detects gRPC from: `.proto` files, `grpc` packages, service definitions
- Detects anything with a discoverable signature

### 3. **Efficient**
- Phase 1 only reads file tree (lightweight)
- Phase 2 only reads AI-selected files (targeted)
- Caching prevents redundant AI calls

### 4. **Maintainable**
- Zero code updates for new technologies
- AI handles edge cases and variations
- Self-documenting via evidence field

## Migration Strategy

### Step 1: Implement AITechnologyDetector
- Create new class alongside existing TechnologyDetector
- Implement both phases with AI prompts
- Add comprehensive error handling

### Step 2: Parallel Testing
- Run both detectors on same repos
- Compare results
- Log differences for analysis

### Step 3: Configuration Flag
```yaml
detection:
  mode: "ai"  # or "legacy" or "hybrid"
  ai_detection:
    enabled: true
    phase1_model: "gpt-4o-mini"  # Fast for triage
    phase2_model: "gpt-4o-mini"  # Accurate for analysis
    max_files_per_repo: 10
    cache_results: true
```

### Step 4: Gradual Rollout
1. Test on 10 repos → validate results
2. Test on 50 repos → measure cost/performance
3. Test on all repos → full comparison
4. Switch default to AI mode

### Step 5: Deprecate Legacy
- Keep legacy detector for 1 release as fallback
- Remove after AI detector proven stable

## Cost Analysis

### Per Repository:
- **Phase 1** (triage): ~500 tokens = $0.0003 (gpt-4o-mini)
- **Phase 2** (analysis): ~2000 tokens = $0.0012 (gpt-4o-mini)
- **Total per repo**: ~$0.0015

### For 255 Repos:
- **Total cost**: ~$0.38 per full scan
- **With caching**: ~$0.10 for incremental scans

### Comparison:
- Current: Manual updates + missed technologies = HIGH maintenance cost
- AI-driven: ~$0.40 per scan + ZERO maintenance = LOW total cost

## Performance Metrics

### Targets:
- **Phase 1**: <2s per repo (tree only)
- **Phase 2**: <5s per repo (file content)
- **Total**: ~7s per repo × 255 repos = **~30 minutes** (with parallelization: ~10 minutes)

### Rate Limiting:
- GitHub API: 5000 calls/hour (handled by existing rate limiter)
- OpenAI API: 3500 requests/minute (more than enough)

## Success Criteria

### Must Have:
✅ Detects GraphQL in all repos using it
✅ Detects gRPC in all repos using it
✅ Detects 100% of technologies current detector finds
✅ Discovers at least 20+ new technologies

### Should Have:
✅ Costs <$1 per full scan
✅ Completes scan in <20 minutes
✅ 95%+ accuracy vs manual validation
✅ Evidence field explains every detection

### Nice to Have:
✅ Detects emerging technologies automatically
✅ Suggests obsolete technologies for removal
✅ Identifies technology conflicts/incompatibilities

## Risk Mitigation

### Risk 1: AI Hallucination
**Mitigation**:
- Require evidence field (must cite file/line)
- Validate against file content
- Aggregate across repos (hallucinations won't correlate)

### Risk 2: API Costs
**Mitigation**:
- Cache results per repo
- Use gpt-4o-mini (10x cheaper than gpt-4)
- Only re-scan repos that changed

### Risk 3: API Downtime
**Mitigation**:
- Fallback to legacy detector
- Retry with exponential backoff
- Cache previous results

### Risk 4: Accuracy Issues
**Mitigation**:
- Parallel run both detectors initially
- Manual validation on 50 sample repos
- Confidence scoring for human review

## Future Enhancements

### Phase 4: Relationship Detection
AI can identify technology relationships:
- "React + Apollo Client → GraphQL frontend"
- "Spring Boot + gRPC → Java microservices"
- "Terraform + AWS → Cloud infrastructure"

### Phase 5: Trend Analysis
AI can spot patterns:
- "3 new repos adopted GraphQL in Q4"
- "Java repos declining, Kotlin repos growing"
- "gRPC adoption accelerating in microservices"

### Phase 6: Recommendation Engine
AI can suggest:
- "Consider adopting gRPC for inter-service communication"
- "GraphQL might replace REST in 5 frontend repos"
- "Consolidate 3 different ORMs to improve consistency"

## Conclusion

This AI-driven architecture transforms technology detection from:
- **Manual** → Automated
- **Static** → Dynamic
- **Limited** → Comprehensive
- **Brittle** → Resilient

It solves the immediate problem (GraphQL/gRPC missing) while future-proofing the entire system.
