# Plugin/Skill to search for toher Claude Plugin/Skills

A Claude Code skill for discovering and recommending plugins and skills from multiple marketplaces with analysis and installation instructions.

## Overview

This skill helps users find the right Claude Code plugins for their needs based on the current context or a user driven query by searching across multiple marketplaces, analyzing plugin capabilities, and providing ready-to-use installation commands.

## Features

- 🔍 **Smart Search** - Find plugins by name, description, or category
- 🌐 **Multi-Marketplace** - Searches both official and community marketplaces
- 📊 **Comprehensive Analysis** - Shows GitHub stats, MCP support, commands, and skills
- 📥 **Installation Ready** - Provides copy-paste installation commands
- 🔄 **Auto-Update** - Fresh marketplace data every 60 minutes

## Installation
```bash
claude plugin marketplace add daamitt/skill-issue
claude plugin i Skill-issue
```

## Example Output

```
1. Notion
   Category: productivity
   ⭐ Stars: 6 | 🔌 MCP: Yes | 📜 Commands: 6 | 🎯 Skills: 4 | 🕐 Last Updated: 2025-12-22

   Great for managing documentation with:
   - 4 skills: knowledge-capture, meeting-intelligence, research-documentation, spec-to-implementation
   - 6 commands for creating pages, databases, tasks, and querying

   Installation:
   /plugin marketplace add anthropics/claude-plugins-official
   /plugin install Notion@claude-plugins-official

   Homepage: https://github.com/makenotion/claude-code-notion-plugin
```

## What the Skill Provides

When you ask Claude to search for plugins (e.g., "find plugins for issue tracking"), the skill returns:

### Basic Information
- Plugin name and description
- Category
- Homepage link

### Detailed Analysis 
- ⭐ GitHub stars (popularity)
- 🕐 Last updated date (maintenance status)
- 🔌 MCP support (Model Context Protocol integration)
- 📜 Commands (count and names)
- 🎯 Skills (count and paths)
- 📥 Installation instructions


### Requirements
- Python 3.6+
- `curl` (for downloading marketplace data)

### Usage
The skill is invoked automatically when you ask Claude to search for plugins, or you can use the `/search` command:

```
/search notion and issue tracking
```


## Marketplaces Supported

The skill searches across multiple marketplaces configured in `skills/plugin-search/scripts/marketplaces.json`:
eg:
`~/.claude/plugins/cache/1xn-plugins/SkillIssue/0.1.0/skills/plugin-search/scripts/marketplaces.json`

- **claude-plugins-official** - Official Anthropic plugins
- **anthropics-skills** - Skills marketplace

To add more marketplaces, edit the config file:
```json
{
  "marketplaces": [
    {
      "name": "marketplace-name",
      "base_url": "https://raw.githubusercontent.com/owner/repo"
    }
  ]
}
```

## Directory Structure

```
claude-plugin-search/
├── README.md                           # This file
├── skills/
│   └── plugin-search/
│       ├── SKILL.md                    # Skill definition
│       ├── README.md                   # Detailed documentation
│       ├── .gitignore                  # Ignore data cache
│       └── scripts/
│           ├── search_plugins.py       # Main search script
│           ├── marketplaces.json       # Marketplace config
│           └── data/                   # Cached marketplace data (auto-created)
```

## For Developers

### Search Script
The Python script at `skills/plugin-search/scripts/search_plugins.py` provides:
- Multi-marketplace data loading and caching
- Full-text search across plugins
- GitHub API integration for stats
- Repository tree analysis for commands/skills/MCP detection

### Direct Usage
```bash
cd skills/plugin-search
python3 scripts/search_plugins.py -q "database" -d
```

See `skills/plugin-search/README.md` for complete script documentation.

## License

This tool is provided as-is for searching Claude Code plugin marketplaces.
