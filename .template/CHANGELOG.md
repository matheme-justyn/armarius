## [0.7.0] - 2026-06-15

### Added
- Added a dashboard-first web entry point for Armarius
- Added dedicated pages for Library, Paradigm Analysis, Concerto Synthesis, Tutorial, and Catalog Assistant
- Added focused web tests for CLI startup hints and dashboard helper content
- Added a milestone-first execution protocol to `AGENTS.md`

### Changed
- Redesigned the web UI into a workflow-oriented research workbench
- Changed navigation from a tab-heavy layout to a sidebar-driven multi-page structure
- Changed local web installation flow to use the optional `web` extra
- Updated README quick start guidance in English and zh-TW

### Fixed
- Improved `armarius serve` error guidance when `streamlit` is missing
- Fixed dashboard/workflow copy alignment with the actual navigation structure
- Fixed pagination reset behavior when search filters or page size change
- Fixed several Streamlit width/deprecation issues in the web UI

### Removed
- Removed the assumption that Streamlit is always part of the core dependency set

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.10.0] - 2026-03-03

### Added
- **README Language Strategy System**: 新增三種 README 生成策略
  - `separate`: 分離語言檔案（推薦）- README.md + README.{lang}.md
  - `bilingual`: 單檔案雙語格式 - 中文 | English 並列
  - `primary_only`: 僅主語言單一檔案
  - 在 `config.toml` 新增 `[i18n.readme]` 配置區塊
  - AI 可根據 strategy 設定自動選擇生成方式

### Changed
- **README_BILINGUAL_FORMAT.md**: 重構為 "README Language Strategies & Formatting Rules"
  - 新增策略選擇指南和適用場景表格
  - 新增 AI Agent 實作範例（pseudocode）
  - 保留 bilingual 格式規則（向後兼容）
  - 新增 separate 策略驗證範例

- **AGENTS.md**: AI Agent Communication Protocol 新增 "6. README Generation Protocol"
  - 強制 AI 讀取 config.toml 檢查 strategy
  - 根據 strategy 生成對應格式的詳細步驟
  - 語言切換器生成規則
  - 驗證檢查清單

## [1.9.0] - 2026-03-02

### Changed
- **README Structure**: 重構 README 為分離語言檔案
  - `README.md`: 英文版（主要版本）
  - `README.zh-TW.md`: 繁體中文版（額外版本）
  - 移除雙語混排格式，提升可讀性
  - 移除「尚未製作」的使用範例章節
  - 移除貢獻 PR 相關內容
  - 精簡內容從 250 行降至 183 行

## [1.8.4] - 2026-03-02

### Added
- **System Environment Detection**: AGENTS.md 新增 System Environment 段落，指導 AI 讀取 config.toml 來使用正確的 OS 特定指令
  - timeout 指令範例（macOS vs Linux）
  - sed in-place 編輯範例
  - 套件管理器檢查

### Changed
- **opencode.json**: 移除硬編碼的 environment 變數，改用 .env 檔案（由 start-opencode.sh 載入）
- **MCP Setup Guide**: 加強 MCP 設定指南的詳細說明
- **INSTALL.md**: 更新環境偵測步驟說明
- **test-mcp-setup.sh**: 改善錯誤報告和診斷訊息

## [1.8.3] - 2026-03-02

### Changed
- **test-release.sh → health-check.sh**: 重新定位為專案健康度檢查腳本，移除發版語氣，使其可隨時執行驗證環境配置
  - 更新標題："Release Testing" → "Project Health Check"
  - 調整成功訊息：從「發版就緒」改為「專案健康良好」
  - 新增提示：如需發版，執行 bump-version.sh

## [1.8.2] - 2026-03-02

### Added
- **File Structure Reorganization**: Clear separation between scaffolding and project layers
  - Root `CHANGELOG.md`: Project-level template (user's project changes)
  - `.template/CHANGELOG.md`: Template version history (scaffolding changes)
  - Root `README.md`: Template documentation with identification banner
  - `.template/README.md`: Synchronized backup in scaffolding mode

- **README Synchronization System** (Scaffolding Mode Only)
  - New script: `.template/scripts/sync-readme.sh`
  - Automatic sync: Root README.md → `.template/README.md`
  - Pre-push hook integration: Blocks push if README out of sync
  - bump-version.sh integration: Auto-sync during version bump
  - Configuration: `config.toml` → `sync_readme = true`

- **MCP (Model Context Protocol) Integration**
  - 4 MCP servers configured in `opencode.json`:
    - filesystem: File operations
    - git: Git operations
    - memory: AI memory persistence
    - github: GitHub API (requires token)
  - Interactive setup in `init-project.sh`
  - Comprehensive test script: `.template/scripts/test-mcp-setup.sh`
  - Detailed setup guide: `.template/docs/MCP_SETUP_GUIDE.md`
  - GitHub token permission guide (3 levels: Read-only / Recommended / Full)

- **Documentation Enhancements**
  - MCP priority rules in AGENTS.md (check MCP first, fallback to CLI)
  - Updated AGENTS.md with file layer separation explanation
  - Template identification banner in README.md

### Changed
- **All CHANGELOG references updated**:
  - README.md: Links to both template and project CHANGELOGs
  - SECURITY.md: Points to `.template/CHANGELOG.md`
  - AGENTS.md: Explains CHANGELOG usage in both modes
  - bump-version.sh: Updates `.template/CHANGELOG.md` path

- **Pre-push hook enhanced**:
  - Added README sync check (if `sync_readme = true`)
  - Scaffolding mode now validates both VERSION and README sync

- **config.toml expanded**:
  - Added `sync_readme` configuration option
  - Documented README sync behavior

### Fixed
- VERSION and README synchronization in scaffolding mode
- File organization clarity between template and project layers

## [1.8.1] - 2026-03-02

### Fixed
- **pre-push hook remote tag checking**: Hook now correctly checks remote tags instead of local tags
  - Bug: Previously used `git describe --tags --abbrev=0` which only checked local repository
  - Fix: Now uses `git ls-remote --tags origin` to check actual remote tags
  - Impact: Prevents false "VERSION NOT UPDATED" errors when tag exists locally but not pushed yet
  - Validation: Tested with v1.8.0 tag - correctly identifies remote version


## [1.8.0] - 2026-03-02

### Added
- **VERSION Sync Enforcement System** for Scaffolding Mode
  - New script: `.template/scripts/check-version-sync.sh`
  - Ensures `VERSION` and `.template/VERSION` stay synchronized in scaffolding mode
  - Integrated into pre-push hook for automatic validation
  - Prevents accidental version mismatch in template development

- **README.md Comprehensive Improvements** (6 major enhancements)
  - **AGENTS.md Preview**: Collapsible snippet showing coding conventions, commit format, and best practices
  - **superpowers Explanation**: Added "Core Concept" section with GitHub link explaining reusable AI workflows
  - **VERSION Dual-File Design**: Complete directory structure diagram, version file purposes, and scaffolding mode sync requirements
  - **Git Hook Mechanism**: Full workflow explanation with automatic checks, failure handling, and emergency bypass instructions
  - **.opencode/ Directory Structure**: Clear explanation of AI assistant configuration directory
  - **Usage Examples Placeholder**: Section for future screenshots/demos (AI installation, version management, AGENTS.md-driven development)

### Changed
- **bump-version.sh**: Now detects working mode from `config.toml` and automatically syncs both VERSION files in scaffolding mode
- **pre-push hook**: Enhanced with version sync check for scaffolding mode before allowing push to main

### Fixed
- **VERSION inconsistency**: Synchronized `.template/VERSION` and `VERSION` to 1.7.0
- **README badge**: Updated version badge to match actual VERSION file (1.7.0 → 1.8.0)



## [1.7.0] - 2026-02-26

### Added
- **Post-Installation Cleanup System**
  - New script: `.template/scripts/post-install-cleanup.sh`
  - Interactive cleanup of unnecessary scaffolding content:
    - Marketing assets (logo, illustrations) - saves ~6MB
    - Unused language configs (Go, Python, Rust if not needed)
    - Scaffolding guides (README_GUIDE.md, TEMPLATE_SYNC.md after reading)
    - Unused AI tool configs (.claude/, .roo/ if not used)
  - New guide: `.template/docs/POST_INSTALL_CLEANUP.md`
    - Complete cleanup instructions
    - What to keep vs what to delete
    - Worth learning: ADR examples, Root Directory Policy
    - Not worth learning: Bilingual comments in code

### Changed
- **INSTALL.md**: Added Step 6 (Post-Installation Cleanup) to integration workflow

### Philosophy
- **Scaffolding is temporary support**: Keep only what you need, remove the rest
- After setup, projects should be lightweight and contain only relevant content


## [1.6.0] - 2026-02-26

### Added
- **Intelligent Conflict Analysis** (`.template/scripts/analyze-conflicts.sh`)
  - Pre-merge analysis of file differences between project and scaffolding
  - Automatic categorization into 5 categories:
    - Category 1: Must rewrite (following scaffolding guides)
    - Category 2: Direct import/overwrite (e.g., AGENTS.md replaces CLAUDE.md)
    - Category 3: Can convert to new format (merge/convert)
    - Category 4: Project is better, keep yours
    - Category 5: New files from scaffolding
  - Generates detailed markdown report with file-by-file recommendations
  - Execution suggestions with bash commands
  - Backup strategy before integration

### Changed
- **INSTALL.md Option 2**: Complete rewrite with conflict analysis workflow
  - Added AI-assisted integration section
  - Added manual integration with analysis report
  - Clear categorization of conflict resolution strategies
  - Emphasis: CLAUDE.md → AGENTS.md is replacement, not choice

### Improved
- Integration workflow now intelligence-driven, not guesswork
- Users can make informed decisions based on categorized analysis
- Reduced manual conflict resolution effort


## [1.5.4] - 2026-02-26

### Changed
- **README Format**: Complete restructure to proper bilingual format
  - Headers: `## 中文 | English` (same line)
  - Bullet lists: Chinese line, then English line (two-space line break)
  - Tables: `<br>` for line breaks within cells (Chinese<br>English)
  - Code blocks: Appear only once (no duplication)
  - Links: Inline bilingual `詳細說明 | For details:`

### Added
- **README_BILINGUAL_FORMAT.md**: Complete bilingual formatting rules for AI agents
  - Language pairing rules (zh-TW+EN, ja-JP+EN, etc.)
  - Formatting rules for headers, paragraphs, lists, tables, code
  - AI agent implementation guidelines
  - Validation examples and common mistakes

### Fixed
- AGENTS.md now references README_BILINGUAL_FORMAT.md for bilingual generation


## [1.5.3] - 2026-02-26

### Changed
- **README Quick Install**: Fixed bilingual format - code blocks appear only once (not duplicated for each language)
  - Chinese description + English description + Code block (once)
  - Comments in code blocks are bilingual where appropriate


## [1.5.2] - 2026-02-26

### Changed
- **README Bilingual Format**: Restructured to paragraph-by-paragraph format (Chinese then English)
- **README Illustrations**: Added back two illustrations under scaffolding theory section
- **README Tech Stack**: Core philosophy changed from heading to italic text


### Changed
- **README Simplification**: Drastically simplified README to focus on core message
  - What is this scaffolding
  - Core features (bullet points)
  - **Vibe Tech Stack**: Replaced generic tech choices (BCP 47, SemVer, TOML) with actual Vibe methodology
    - OpenCode, AGENTS.md, superpowers Skills, Subagents, Single-instance workflow, MCP
  - Quick installation (one-line AI command)
  - Removed detailed sections (moved to INSTALL.md and .template/docs/)


### Changed
- **README Simplification**: Drastically simplified README to focus on core message
  - What is this scaffolding
  - Core features (bullet points)
  - Vibe Coding tech stack choices
  - Quick installation (one-line AI command)
  - Removed detailed sections (moved to INSTALL.md and .template/docs/)


## [1.5.0] - 2026-02-26

### Added
- **One-Line Installation for AI Assistants**:
  - Created `.opencode/INSTALL.md` with comprehensive installation guide
  - Support for OpenCode, Cursor, and other AI assistants
  - Three installation options: New project, Existing project, Cherry-pick features
  - AI can read and guide users through the entire setup process

### Changed
- **README Updates**:
  - Added Quick Install section with AI-friendly one-liner
  - Reorganized installation instructions for clarity
  - Added manual installation alternatives

### Documentation
- **INSTALL.md Sections**:
  - Option 1: New Project (GitHub template method)
  - Option 2: Integrate into Existing Project (git merge method)
  - Option 3: Cherry-Pick Features (selective installation)
  - Configuration guide (mode, language, project info)
  - Troubleshooting section
  - What You Get overview

### Infrastructure
- Cleaned up duplicate lines in pre-push hook


## [1.4.0] - 2026-02-26

### Added
- **Version Management Enforcement**:
  - Pre-push git hook automatically checks if VERSION has been updated
  - Push to main branch is blocked if version hasn't changed since last tag
  - install-hooks.sh script to install version check hook
  - Clear error messages with instructions when version check fails

### Changed
- **AGENTS.md Updates**:
  - Added strict semantic versioning rules (MAJOR.MINOR.PATCH)
  - Defined clear criteria for breaking changes
  - Added "When in doubt: Choose MINOR over MAJOR" guideline
  - Updated version management workflow with hook enforcement
- **init-project.sh Enhancement**:
  - Added interactive Git hooks installation step
  - Prompts user to install version check hook for their project

### Documentation
- **Semantic Versioning Clarification**:
  - Explicit PATCH examples (bug fixes, docs, comments)
  - Explicit MINOR examples (new features, backward compatible)
  - Explicit MAJOR criteria (ONLY user-impacting breaking changes)
  - Common misconceptions listed (NOT breaking changes)
- **Version Management Protocol**:
  - Mandatory version bump before every push to main
  - Why: Direct main workflow means every commit is "released"
  - Enforcement: Pre-push hook verification

### Infrastructure
- **.template/hooks/pre-push**: Git hook for version enforcement
- **.template/scripts/install-hooks.sh**: Hook installation script
- Removed empty root directories: `docs/` and `scripts/` (scaffolding mode)


## [1.3.0] - 2026-02-26

### Added
- **Complete Scaffolding Template Isolation**:
  - All scaffolding infrastructure moved to `.template/` directory
  - Clear separation between scaffolding and project files
  - Mode system: `scaffolding` (developing template) vs `project` (using template)
- **Working Mode Configuration**:
  - `config.toml` mode setting determines file organization
  - Template mode: ADRs, scripts, assets in `.template/`
  - Project mode: ADRs, scripts, assets in root directories
- **AI Agent i18n Integration**:
  - AI Agent Communication Protocol in AGENTS.md
  - Session start checklist for language configuration
  - Automatic translation loading from `.template/i18n/locales/`
  - Communication language adapts to user's `primary_locale`
- **Project Policy Files Management**:
  - Dual-location strategy for LICENSE, CONTRIBUTING.md, SECURITY.md
  - Root files for current context (scaffolding or project)
  - `.template/` copies as permanent reference
  - Comprehensive project guides for creating policies
- **Project Setup Guides**:
  - PROJECT_LICENSE_GUIDE.md - License selection and creation
  - PROJECT_CONTRIBUTING_GUIDE.md - Contribution policy writing
  - PROJECT_SECURITY_GUIDE.md - Security policy creation

### Changed
- **File Organization**:
  - Moved ADRs: `docs/adr/` → `.template/docs/adr/`
  - Moved scripts: `scripts/` → `.template/scripts/`
  - Moved assets: `assets/` → `.template/assets/`
  - TEMPLATE_SYNC.md → `.template/docs/TEMPLATE_SYNC.md`
- **Terminology Consistency**:
  - Unified use of "scaffolding" (鷹架) throughout
  - Mode values: `scaffolding` and `project` (not `template` or `framework`)
- **Enhanced init-project.sh**:
  - Interactive LICENSE creation (MIT or custom)
  - CONTRIBUTING.md generation (accepting PRs or not)
  - Optional SECURITY.md creation with contact info
  - Project VERSION initialization to 0.1.0

### Documentation
- **AGENTS.md Updates**:
  - Added Working Mode section explaining scaffolding vs project mode
  - Added AI Agent Communication Protocol (mandatory for all agents)
  - Updated file organization rules based on mode
- **README Updates**:
  - Updated all asset paths to `.template/assets/`
  - VERSION badge points to `.template/VERSION`
  - Clear documentation of dual-mode system
- **Path References**:
  - All documentation updated to reference `.template/` paths
  - CHANGELOG.md reflects new file structure

### Architecture
- **ADR 0006**: Template Directory Isolation
  - Documents the rationale for `.template/` structure
  - Explains scaffolding vs project file separation
  - Outlines migration strategy and benefits


## [1.2.0] - 2026-02-26

### Added
- **Multi-language Support**: Comprehensive language-specific configuration modules
  - `languages/go/` - Go development module (golangci-lint, Makefile, go.mod example)
  - `languages/python/` - Python development module (pyproject.toml, .python-version)
  - `languages/typescript/` - TypeScript development module (tsconfig, ESLint, package.json)
  - `languages/rust/` - Rust development module (Cargo.toml, rust-toolchain.toml)
- **Enhanced Core Configs**:
  - `.gitignore` - Added patterns for Go, Python, TypeScript, Rust
  - `.editorconfig` - Added language-specific formatting rules

### Documentation
- Each language module includes comprehensive README with:
  - Quick start guide
  - Configuration explanations
  - Best practices
  - Common workflows
  - Troubleshooting tips
- **README.md**: Added "Language Support" section explaining out-of-box and deep module support

### Philosophy
- Hybrid approach: basic support out-of-box, opt-in deep configurations
- Language modules in `languages/` directory (not `templates/` to avoid confusion)
- Each module is self-contained and optional

## [1.1.0] - 2026-02-25

### Added
- **LICENSE**: MIT License for open source distribution
- **CONTRIBUTING.md**: Contribution guidelines (no PRs accepted, issues welcome)
- **SECURITY.md**: Security policy and vulnerability reporting guidelines
- **ADR Examples**: Three comprehensive Architecture Decision Record templates:
  - `.template/docs/adr/0002-example-tech-stack-selection.md` - Technology stack selection example
  - `.template/docs/adr/0003-example-api-design-principles.md` - API design principles example
  - `.template/docs/adr/0004-example-testing-strategy.md` - Testing strategy example
- **Visual Branding**: Logo and illustration assets
  - `.template/assets/images/20260225_vibe-scaffolding-logo.png` - Primary logo
  - `.template/assets/images/20260225_vibe-scaffolding-illustration-american.png` - American style illustration
  - `.template/assets/images/20260225_vibe-scaffolding-illustration-japanese.png` - Japanese style illustration

### Changed
- **CHANGELOG.md**: Converted to English for international accessibility
- **README.md**: Added Vygotsky's scaffolding theory explanation and visual branding
- **PR Template**: Simplified to Angular style with bilingual (EN/ZH) format

### Documentation
- Enhanced README with concept explanation inspired by Vygotsky's scaffolding theory
- Added comprehensive ADR examples covering different decision types
- Clarified contribution policy (clone/fork encouraged, PRs not accepted)


## [1.0.0] - 2026-02-25

### Added
- Initial release of vibe coding template
- Core configuration files:
  - `AGENTS.md` - OpenCode AI agent instructions
  - `README.md` - Project documentation
  - `.gitignore` - Git ignore rules
  - `.editorconfig` - Editor configuration
  - `.env.example` - Environment variables example
  - `opencode.json` - OpenCode project configuration
- GitHub Templates:
  - `.github/ISSUE_TEMPLATE/bug_report.md` - Bug report template
  - `.github/ISSUE_TEMPLATE/feature_request.md` - Feature request template
  - `.github/pull_request_template.md` - Pull request template (Angular style)
  - `.github/workflows/ci-placeholder.yml` - CI workflow placeholder
- Documentation:
  - `.template/docs/adr/0001-record-architecture-decisions.md` - First ADR example
- Version management:
  - `.template/VERSION` - Scaffolding version number file
  - `CHANGELOG.md` - Version changelog
  - `.template/docs/TEMPLATE_SYNC.md` - Template synchronization guide
  - `.template/scripts/bump-version.sh` - Version management script

### Coding Conventions
- Test-driven development (TDD) approach
- All functions require docstrings and type annotations
- Avoid over-engineering
- Commit messages in Traditional Chinese

### Version Management
- Semantic Versioning 2.0.0
- Git tags for version marking
- Template sync mechanism for updating existing projects

---

## Version Rules

Following [Semantic Versioning 2.0.0](https://semver.org/):

- **MAJOR version** (X.0.0): Incompatible API changes, major architectural adjustments
- **MINOR version** (0.X.0): Backward-compatible new features
- **PATCH version** (0.0.X): Backward-compatible bug fixes, documentation updates

### Examples

- `1.0.0` → `1.0.1`: Fix documentation typos, update .gitignore
- `1.0.0` → `1.1.0`: Add Docker support, add testing framework configuration
- `1.0.0` → `2.0.0`: Change project structure, remove certain files

[Unreleased]: https://github.com/matheme-justyn/my-vibe-scaffolding/compare/v1.2.0...HEAD
[1.2.0]: https://github.com/matheme-justyn/my-vibe-scaffolding/compare/v1.1.0...v1.2.0
[1.0.0]: https://github.com/matheme-justyn/my-vibe-scaffolding/releases/tag/v1.0.0
