# Claude Plugin Marketplace Search

A Python script to search and filter Claude Code plugins from the official marketplace.

## Features

- 🔍 **Full-text search** across plugin names and descriptions
- 📂 **Category filtering** to find plugins by type
- 🏷️ **Tag filtering** for community-managed plugins
- 📊 **List categories and tags** to explore available options
- 📋 **Detailed output mode** for comprehensive plugin information
- 💾 **JSON export** for programmatic use
- 🔄 **Auto-update** - Automatically downloads fresh marketplace data if older than 60 minutes

## Installation

No installation needed! Just ensure you have Python 3.6+ installed:

```bash
python3 --version
```

## Quick Start

Get help and see all available options:

```bash
python3 scripts/search_plugins.py -h
# or
python3 scripts/search_plugins.py --help
```

## Usage

### Basic Search

Search for plugins by keyword:

```bash
python3 scripts/search_plugins.py -q "notion"
python3 scripts/search_plugins.py -q "issue tracking"
```

### Filter by Category

List all plugins in a specific category:

```bash
python3 scripts/search_plugins.py -c productivity
python3 scripts/search_plugins.py -c development
```

### Detailed Information

Get detailed plugin information:

```bash
python3 scripts/search_plugins.py -q "github" -d
```

### List Available Options

See all available categories:

```bash
python3 scripts/search_plugins.py --list-categories
```

See all available tags:

```bash
python3 scripts/search_plugins.py --list-tags
```

### Combine Filters

Combine multiple search criteria:

```bash
python3 scripts/search_plugins.py -q "database" -c development
python3 scripts/search_plugins.py -c productivity -t community-managed
```

### JSON Output

Export results as JSON:

```bash
python3 scripts/search_plugins.py -q "api" --json
python3 scripts/search_plugins.py -c productivity --json > productivity-plugins.json
```

## Command-Line Options

```
usage: search_plugins.py [-h] [-f FILE] [-q QUERY] [-c CATEGORY] [-t TAGS [TAGS ...]]
                         [-d] [--list-categories] [--list-tags] [--json]

Search Claude Code plugins marketplace

options:
  -h, --help            show this help message and exit
  -f FILE, --file FILE  Path to marketplace JSON file (default: claude-plugins.json)
  -q QUERY, --query QUERY
                        Search query (searches in name and description)
  -c CATEGORY, --category CATEGORY
                        Filter by category
  -t TAGS [TAGS ...], --tags TAGS [TAGS ...]
                        Filter by tags (space-separated)
  -d, --detailed        Show detailed information
  --list-categories     List all available categories
  --list-tags           List all available tags
  --json                Output results as JSON
```

## Examples

### Find all productivity tools
```bash
python3 scripts/search_plugins.py -c productivity
```

### Search for database-related plugins
```bash
python3 scripts/search_plugins.py -q database
```

### Find Notion and issue tracking tools
```bash
python3 scripts/search_plugins.py -q "notion"
python3 scripts/search_plugins.py -q "issue"
```

### Get detailed info about GitHub plugin
```bash
python3 scripts/search_plugins.py -q github -d
```

### Export all development plugins as JSON
```bash
python3 scripts/search_plugins.py -c development --json > dev-plugins.json
```

## Auto-Update Behavior

The script automatically manages the marketplace data:

- **First run**: Downloads the latest marketplace data to `data/claude-plugins.json`
- **Subsequent runs**: Uses cached data if less than 60 minutes old
- **Auto-refresh**: Automatically downloads fresh data when cache is older than 60 minutes
- **Offline mode**: Uses cached data if download fails (with warning)

The script shows the cache age on each run:
```
Using cached marketplace data (age: 15.3 minutes)
```

To force a fresh download, simply delete the data directory:
```bash
rm -rf data/
```

## Categories

The marketplace includes plugins in these categories:
- **database** - Database integrations (Firebase, Supabase)
- **deployment** - Deployment tools (Vercel)
- **design** - Design tools (Figma)
- **development** - Development tools (LSPs, SDKs)
- **learning** - Educational plugins
- **monitoring** - Error tracking (Sentry)
- **productivity** - Productivity tools (GitHub, Notion, Linear, Slack)
- **security** - Security tools
- **testing** - Testing frameworks (Playwright)

## Plugin Data Source

The script automatically downloads and caches data from the marketplaces in `script/marketplaces.json`

The marketplace data is stored in `data/{marketplace-name}.json` and automatically refreshed when older than 60 minutes.

## License

This tool is provided as-is for searching the Claude Code plugin marketplace.
