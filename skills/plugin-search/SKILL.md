---
name: skill-plugin-search
description: Search for claude plugins for a specific skill to help user with a task
---

# Skill and Plugin Search

## Instructions
Use the `scripts/search_plugins.py` script to find relevant Claude Code plugins that match the user's requirements.

1. **Start with overview** - List plugins by category or search term:
   ```bash
   python3 scripts/search_plugins.py -q "<user's requirements>"
   python3 scripts/search_plugins.py -c productivity
   ```

2. **Get detailed information** - Use `-d` flag for comprehensive analysis:
   ```bash
   python3 scripts/search_plugins.py -q "<plugin name>" -d
   ```

3. The script automatically:
   - Downloads the latest marketplace data (if needed)
   - Searches across plugin names and descriptions
   - Returns matching results

4. **Detailed mode (`-d`) provides:**
   - ⭐ **GitHub stars** - Repository popularity
   - 🕐 **Last updated** - How recently maintained
   - 🔌 **MCP support** - Whether it has Model Context Protocol integration
   - 📜 **Commands** - Available command shortcuts (count and names)
   - 🎯 **Skills** - Available skills (count and paths)
   - 📥 **Installation instructions** - Copy-paste ready commands:
     ```bash
     /plugin marketplace add anthropics/claude-plugins-official
     /plugin install <plugin-name>@claude-plugins-official
     ```

5. **For each suggested plugin, provide:**
   - Plugin name
   - Brief description
   - Category
   - **Installation commands** (from detailed output)
   - GitHub stats (stars, last updated)
   - Homepage link

## Examples

### Search for database plugins
```bash
python3 scripts/search_plugins.py -q "database"
```

### Search for issue tracking tools
```bash
python3 scripts/search_plugins.py -q "issue tracking"
```

### List all productivity plugins
```bash
python3 scripts/search_plugins.py -c productivity
```

### Get detailed information with stats and installation
```bash
python3 scripts/search_plugins.py -q "notion" -d
```
This shows:
- GitHub stars and last updated date
- MCP support, commands, and skills
- **Ready-to-use installation commands**

### See available categories
```bash
python3 scripts/search_plugins.py --list-categories
```

## Tips
- **Start with overview**: List all plugins first (by category or search), then use `-d` for detailed analysis
- **Always use `-d` when recommending plugins** to provide installation instructions and stats
- Use broad search terms first, then narrow down
- Check multiple categories if the query is ambiguous
- Combine search terms for better results (e.g., "notion database")

## Example Skill/Plugin recommendation output
 1. Notion

  Category: productivity
  ⭐ Stars: 6 | 🔌 MCP: 1 | 📜 Commands: 6 | 🎯 Skills: 4 | 🕐 Last Updated: 2025-12-22

  Great for managing meeting documentation with:
  - meeting-intelligence skill
  - Also: knowledge-capture, research-documentation, spec-to-implementation
  - 6 commands for creating pages, databases, tasks, and querying

  Installation:
  /plugin marketplace add anthropics/claude-plugins-official
  /plugin install Notion@claude-plugins-official

  Homepage: https://github.com/makenotion/claude-code-notion-plugin

  ---
   