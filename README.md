# SkillIssue - Claude Plugin & Skill Search

A Claude Code skill for discovering and recommending plugins and skills from multiple marketplaces with analysis and installation instructions.

## Overview

SkillIssue helps users find the right Claude Code plugins and skills for their needs by searching across multiple marketplaces, analyzing plugin capabilities, and providing ready-to-use installation commands.

**Currently indexes 52 plugins and 100s of skills across 3 marketplaces!**
Add your marketplace with a [Pull Request](#adding-more-marketplaces)

## Features

- 🔍 **Smart Search** - Search across name, description, category, tags, and keywords
- 🌐 **Multi-Marketplace** - Searches official and community marketplaces (claude-plugins-official, anthropics-skills, claude-code-templates)
- 📊 **Comprehensive Analysis** - Shows GitHub stats, MCP support, commands, and skills in one line
- 📥 **Installation Ready** - Copy-paste installation commands with correct marketplace URLs
- ⚡ **Token Optimized** - Compact output format by default, detailed mode on demand
- 🔄 **Auto-Update** - Fresh marketplace data every 60 minutes via GitHub API

## Installation

```bash
claude plugin marketplace add daamitt/skill-issue
claude plugin i SkillIssue
```

### Requirements
- Python 3.6+
- `curl` (for downloading marketplace data via GitHub API)

## Usage

### As a Skill
The skill is invoked automatically when you ask Claude to search for plugins:

```
> Find me plugins for database management
```

Or use the `/search` command:
```
> /SkillIssue:search notion meetings
```

## Example Output 

```
================================================================================
📦 Notion
================================================================================
Category: productivity
Description: Notion workspace integration. Search pages, create and update documents...

⭐ Stars: 6 | 🔌 MCP: Yes | 📜 Commands: 6 | 🎯 Skills: 4 | 🕐 Last Updated: 2025-12-22

Commands:
  - notion-create-page.md
  - notion-database-query.md
  - notion-create-task.md
  ...

Skills:
  - notion/knowledge-capture
  - notion/meeting-intelligence
  - notion/research-documentation
  ...

────────────────────────────────────────────────────────────────────────────────
📥 Installation:
  /plugin marketplace add anthropics/claude-plugins-official
  /plugin install Notion@claude-plugins-official

Homepage: https://github.com/makenotion/claude-code-notion-plugin
```


### Adding More Marketplaces

Edit `skills/plugin-search/scripts/marketplaces.json`:

```json
{
  "marketplaces": [
    {
      "name": "marketplace-name",
      "base_url": "https://github.com/owner/repo"
    }
  ]
}
```

## Directory Structure

```
skill-issue/
├── README.md                           # This file
├── commands/
│   └── search.md                       # /search command definition
├── skills/
│   └── plugin-search/
│       ├── SKILL.md                    # Skill definition for Claude
│       ├── reference.md                # Detailed documentation
│       └── scripts/
│           ├── search_plugins.py       # Main search script
│           ├── marketplaces.json       # Marketplace config
│           └── data/                   # Cached marketplace data (auto-created)
└── .claude-plugin/
    ├── plugin.json                     # Plugin metadata
    └── marketplace.json                # Marketplace entry for this plugin
```

## Technical Details

### Search Script Features
The Python script at `skills/plugin-search/scripts/search_plugins.py` provides:
- Multi-marketplace data loading and caching (60-minute cache)
- GitHub API integration for repository stats
- Repository tree analysis for commands/skills/MCP detection
- OR logic search across multiple fields
- Token-optimized output formats

### GitHub API Integration
- Fetches marketplace.json via GitHub API 
- Automatically decodes base64 content
- Extracts repository stats (stars, last updated)
- Analyzes repository structure for MCP, commands, and skills

### Available Options

```
-q, --query QUERY         Search query (OR logic for multiple terms)
-c, --category CATEGORY   Filter by category
-t, --tags TAGS          Filter by tags (space-separated)
-d, --detailed           Show detailed information with installation
--all                    List all plugins (compact format)
-m, --marketplace        Filter by marketplace name
--list                   List all marketplaces and categories
```

## Examples

```bash
# Find database plugins
python scripts/search_plugins.py -q "database"

# Find plugins for git workflow
python scripts/search_plugins.py -q "git github workflow"

# See all productivity plugins with details
python scripts/search_plugins.py --all -c productivity -d

# Explore claude-code-templates marketplace
python scripts/search_plugins.py --all -m claude-code-templates

# Get installation instructions for Notion
python scripts/search_plugins.py -q "notion" -d
```

## License

MIT License - This tool is provided as-is for searching Claude Code plugin marketplaces.
