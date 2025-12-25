#!/usr/bin/env python3
"""
Claude Plugin Marketplace Search Tool
Search and filter Claude Code plugins from the marketplace JSON file.
"""

import json
import argparse
import sys
import os
import time
import subprocess
import re
from typing import List, Dict, Any, Optional, Tuple


CACHE_DURATION = 60 * 60  # 60 minutes in seconds
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, "data")
MARKETPLACES_CONFIG = os.path.join(SCRIPT_DIR, "marketplaces.json")
MARKETPLACE_PATH_SUFFIX = "/main/.claude-plugin/marketplace.json"


def load_marketplaces_config() -> List[Dict[str, str]]:
    """Load marketplace configurations from marketplaces.json"""
    try:
        with open(MARKETPLACES_CONFIG, 'r') as f:
            config = json.load(f)
            return config.get('marketplaces', [])
    except FileNotFoundError:
        print(f"Error: {MARKETPLACES_CONFIG} not found", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {MARKETPLACES_CONFIG}: {e}", file=sys.stderr)
        sys.exit(1)


def needs_update(file_path: str, max_age_seconds: int = CACHE_DURATION) -> bool:
    """
    Check if the file needs to be updated.

    Args:
        file_path: Path to the file to check
        max_age_seconds: Maximum age in seconds before refresh

    Returns:
        True if file doesn't exist or is older than max_age_seconds
    """
    if not os.path.exists(file_path):
        return True

    file_age = time.time() - os.path.getmtime(file_path)
    return file_age > max_age_seconds


def download_marketplace(url: str, file_path: str) -> bool:
    """
    Download the marketplace JSON file from the given URL using curl.

    Args:
        url: URL to download from
        file_path: Local path to save the file

    Returns:
        True if successful, False otherwise
    """
    try:
        # Ensure directory exists
        dir_path = os.path.dirname(file_path)
        if dir_path:  # Only create if there's a directory component
            os.makedirs(dir_path, exist_ok=True)

        print(f"Downloading marketplace data from {url}...", file=sys.stderr)

        # Use curl to download (works better on macOS with SSL)
        result = subprocess.run(
            ['curl', '-sL', url, '-o', file_path],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            print(f"Error: curl failed with code {result.returncode}", file=sys.stderr)
            if result.stderr:
                print(f"curl error: {result.stderr}", file=sys.stderr)
            return False

        # Validate JSON
        with open(file_path, 'r') as f:
            json.load(f)

        print(f"Successfully downloaded to {file_path}", file=sys.stderr)
        return True

    except subprocess.TimeoutExpired:
        print("Error: Download timeout", file=sys.stderr)
        return False
    except json.JSONDecodeError as e:
        print(f"Error: Downloaded data is not valid JSON: {e}", file=sys.stderr)
        return False
    except FileNotFoundError:
        print("Error: curl command not found", file=sys.stderr)
        return False
    except Exception as e:
        print(f"Unexpected error downloading marketplace data: {e}", file=sys.stderr)
        return False


def ensure_all_marketplaces() -> Dict[str, Any]:
    """
    Ensure all marketplace data is downloaded and fresh.
    Returns merged marketplace data from all sources.
    """
    marketplaces = load_marketplaces_config()
    all_plugins = []

    for marketplace in marketplaces:
        name = marketplace['name']
        base_url = marketplace['base_url']
        url = f"{base_url}{MARKETPLACE_PATH_SUFFIX}"
        file_path = os.path.join(DATA_DIR, f"{name}.json")

        # Download or use cached data
        if needs_update(file_path):
            if not download_marketplace(url, file_path):
                if not os.path.exists(file_path):
                    print(f"Warning: Skipping {name} marketplace (download failed)", file=sys.stderr)
                    continue
                else:
                    print(f"Warning: Using cached {name} data due to download failure.", file=sys.stderr)
        else:
            age_minutes = (time.time() - os.path.getmtime(file_path)) / 60
            print(f"Using cached {name} marketplace (age: {age_minutes:.1f} minutes)", file=sys.stderr)

        # Load and merge plugins
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                plugins = data.get('plugins', [])
                # Add marketplace name to each plugin
                for plugin in plugins:
                    plugin['_marketplace'] = name
                all_plugins.extend(plugins)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Warning: Could not load {name} marketplace: {e}", file=sys.stderr)
            continue

    # Flush stderr to ensure messages appear before results
    sys.stderr.flush()

    return {
        'plugins': all_plugins,
        'total_marketplaces': len(marketplaces),
        'loaded_marketplaces': len([m for m in marketplaces if os.path.exists(os.path.join(DATA_DIR, f"{m['name']}.json"))])
    }


def search_plugins(
    plugins: List[Dict[str, Any]],
    query: str = None,
    category: str = None,
    tags: List[str] = None
) -> List[Dict[str, Any]]:
    """
    Search plugins based on query, category, and tags.

    Args:
        plugins: List of plugin dictionaries
        query: Search term to match against name and description
        category: Filter by category
        tags: Filter by tags

    Returns:
        Filtered list of plugins
    """
    results = plugins

    # Filter by category
    if category:
        results = [
            p for p in results
            if p.get('category', '').lower() == category.lower()
        ]

    # Filter by tags
    if tags:
        results = [
            p for p in results
            if any(tag.lower() in [t.lower() for t in p.get('tags', [])] for tag in tags)
        ]

    # Filter by query (search in name and description)
    if query:
        query_lower = query.lower()
        results = [
            p for p in results
            if query_lower in p.get('name', '').lower() or
               query_lower in p.get('description', '').lower()
        ]

    return results


def parse_github_url(url: str) -> Optional[Tuple[str, str, str]]:
    """
    Parse a GitHub URL to extract owner, repo, and branch/path.

    Args:
        url: GitHub URL (e.g., https://github.com/owner/repo/tree/branch/path)

    Returns:
        Tuple of (owner, repo, branch) or None if not a valid GitHub URL
    """
    if not url or 'github.com' not in url:
        return None

    # Pattern for GitHub URLs
    patterns = [
        r'github\.com/([^/]+)/([^/]+)/tree/([^/]+)',  # With branch
        r'github\.com/([^/]+)/([^/]+?)(?:\.git)?(?:/|$)',  # Without branch
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            owner = match.group(1)
            repo = match.group(2).replace('.git', '')
            branch = match.group(3) if len(match.groups()) > 2 else 'main'
            return (owner, repo, branch)

    return None


def fetch_github_repo_info(owner: str, repo: str, branch: str = 'main', plugin_path: str = None) -> Optional[Dict[str, Any]]:
    """
    Fetch repository information from GitHub API.

    Args:
        owner: Repository owner
        repo: Repository name
        branch: Branch name (default: main)
        plugin_path: Path to the plugin within the repo (e.g., 'plugins/code-review')

    Returns:
        Dictionary with repo info or None if fetch fails
    """
    try:
        # Fetch basic repo info
        repo_url = f"https://api.github.com/repos/{owner}/{repo}"
        result = subprocess.run(
            ['curl', '-sL', '-H', 'Accept: application/vnd.github.v3+json', repo_url],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode != 0:
            return None

        repo_data = json.loads(result.stdout)

        info = {
            'stars': repo_data.get('stargazers_count', 0),
            'updated_at': repo_data.get('updated_at'),
            'default_branch': repo_data.get('default_branch', 'main'),
        }

        # Fetch repository tree if plugin_path is provided (including empty string for root)
        if plugin_path is not None:
            tree_url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"
            tree_result = subprocess.run(
                ['curl', '-sL', '-H', 'Accept: application/vnd.github.v3+json', tree_url],
                capture_output=True,
                text=True,
                timeout=30
            )

            if tree_result.returncode == 0:
                try:
                    tree_data = json.loads(tree_result.stdout)
                    tree = tree_data.get('tree', [])

                    # Analyze plugin directory structure
                    commands = []
                    skills = []
                    has_mcp = False

                    # Normalize plugin_path
                    if plugin_path:
                        plugin_prefix = plugin_path.rstrip('/') + '/'
                    else:
                        plugin_prefix = ""  # Root directory

                    for item in tree:
                        path = item.get('path', '')

                        # For root directory, check all paths
                        # For subdirectory, check only paths within that directory
                        if not plugin_prefix or path.startswith(plugin_prefix):
                            relative_path = path[len(plugin_prefix):] if plugin_prefix else path

                            # Check for .mcp.json
                            if relative_path == '.mcp.json' or relative_path.endswith('/.mcp.json'):
                                has_mcp = True

                            # Check for commands
                            if relative_path.startswith('commands/'):
                                remaining = relative_path[9:]
                                # Only get direct files in commands/ directory
                                if remaining and '/' not in remaining:
                                    if item.get('type') == 'blob':
                                        commands.append(remaining)

                            # Check for skills
                            if relative_path.startswith('skills/'):
                                parts = relative_path[7:].split('/')
                                # Look for SKILL.md files to identify actual skills
                                # Skills can be at skills/<name>/SKILL.md or skills/<vendor>/<name>/SKILL.md
                                if 'SKILL.md' in relative_path:
                                    # Extract skill path (everything before /SKILL.md)
                                    skill_path = '/'.join(parts[:-1]) if parts[-1] == 'SKILL.md' else None
                                    if skill_path and skill_path not in skills:
                                        skills.append(skill_path)

                    info['commands'] = sorted(commands)
                    info['skills'] = sorted(skills)
                    info['has_mcp'] = has_mcp

                except (json.JSONDecodeError, KeyError):
                    pass

        return info

    except (subprocess.TimeoutExpired, json.JSONDecodeError, KeyError):
        return None
    except Exception:
        return None


def format_plugin_output(plugin: Dict[str, Any], detailed: bool = False) -> str:
    """Format a plugin for display."""
    name = plugin.get('name', 'Unknown')
    description = plugin.get('description', 'No description')
    category = plugin.get('category', 'uncategorized')
    homepage = plugin.get('homepage', 'N/A')
    tags = plugin.get('tags', [])

    output = f"\n{'='*80}\n"
    output += f"📦 {name}\n"
    output += f"{'='*80}\n"
    output += f"Category: {category}\n"
    output += f"Description: {description}\n"

    if tags:
        output += f"Tags: {', '.join(tags)}\n"

    if detailed:
        author = plugin.get('author', {})
        if author:
            author_name = author.get('name', 'Unknown')
            author_email = author.get('email', 'N/A')
            output += f"Author: {author_name} ({author_email})\n"

        version = plugin.get('version')
        if version:
            output += f"Version: {version}\n"

        source = plugin.get('source', 'N/A')
        output += f"Source: {source}\n"

        # Determine the URL to use for GitHub API and extract plugin path
        github_url = homepage
        plugin_path = None

        # Get marketplace info for this plugin
        marketplace_name = plugin.get('_marketplace', 'claude-plugins-official')
        marketplaces = load_marketplaces_config()
        marketplace_info = next((m for m in marketplaces if m['name'] == marketplace_name), None)

        # If source is a relative path, construct the GitHub URL from the marketplace base
        if isinstance(source, str) and (source.startswith('./') or source.startswith('../')):
            # Get the GitHub URL from marketplace config
            if marketplace_info:
                # Extract owner/repo from base_url
                # e.g., https://raw.githubusercontent.com/anthropics/skills -> anthropics/skills
                base_url = marketplace_info['base_url']
                match = re.search(r'github(?:usercontent)?\.com/([^/]+)/([^/]+)', base_url)
                if match:
                    owner = match.group(1)
                    repo = match.group(2)
                    plugin_path = source.lstrip('./')
                    github_url = f"https://github.com/{owner}/{repo}/tree/main/{plugin_path}"
        elif isinstance(source, dict) and source.get('source') == 'url':
            # Source is a dict with URL - use it directly and analyze repository root
            github_url = source.get('url')
            plugin_path = ""  # Empty string to analyze root directory

        # Fetch GitHub repository information
        github_info = parse_github_url(github_url)
        if github_info:
            owner, repo, branch = github_info
            output += f"\nGitHub Repository: {owner}/{repo}\n"

            repo_data = fetch_github_repo_info(owner, repo, branch, plugin_path)
            if repo_data:
                # Show stars and last updated
                output += f"  ⭐ Stars: {repo_data['stars']}\n"

                if repo_data['updated_at']:
                    # Format date nicely
                    from datetime import datetime
                    try:
                        updated = datetime.fromisoformat(repo_data['updated_at'].replace('Z', '+00:00'))
                        output += f"  🕐 Last Updated: {updated.strftime('%Y-%m-%d')}\n"
                    except:
                        pass

                # Show plugin directory structure
                if plugin_path is not None:
                    if plugin_path:
                        output += f"\nPlugin Directory: {plugin_path}\n"
                    else:
                        output += f"\nPlugin Structure:\n"

                    # MCP support
                    if repo_data.get('has_mcp'):
                        output += f"  🔌 MCP: Yes (.mcp.json found)\n"
                    else:
                        output += f"  🔌 MCP: No\n"

                    # Commands
                    commands = repo_data.get('commands', [])
                    if commands:
                        output += f"  📜 Commands: {len(commands)}\n"
                        for cmd in commands[:5]:  # Show first 5
                            output += f"      - {cmd}\n"
                        if len(commands) > 5:
                            output += f"      ... and {len(commands) - 5} more\n"
                    else:
                        output += f"  📜 Commands: None\n"

                    # Skills
                    skills = repo_data.get('skills', [])
                    if skills:
                        output += f"  🎯 Skills: {len(skills)}\n"
                        for skill in skills[:5]:  # Show first 5
                            output += f"      - {skill}\n"
                        if len(skills) > 5:
                            output += f"      ... and {len(skills) - 5} more\n"
                    else:
                        output += f"  🎯 Skills: None\n"

        # Add installation instructions in detailed mode
        marketplace_name = plugin.get('_marketplace', 'claude-plugins-official')
        output += f"\n{'─'*80}\n"
        output += f"📥 Installation:\n"
        output += f"  # First, add the marketplace (if not already added):\n"
        output += f"  /plugin marketplace add anthropics/{marketplace_name}\n\n"
        output += f"  # Then install the plugin:\n"
        output += f"  /plugin install {name}@{marketplace_name}\n"

    output += f"\nHomepage: {homepage}\n"

    return output


def list_categories(plugins: List[Dict[str, Any]]) -> List[str]:
    """Get unique list of categories."""
    categories = set()
    for plugin in plugins:
        category = plugin.get('category')
        if category:
            categories.add(category)
    return sorted(categories)


def list_tags(plugins: List[Dict[str, Any]]) -> List[str]:
    """Get unique list of tags."""
    tags = set()
    for plugin in plugins:
        plugin_tags = plugin.get('tags', [])
        tags.update(plugin_tags)
    return sorted(tags)


def main():
    parser = argparse.ArgumentParser(
        description='Search Claude Code plugins marketplace',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s -q notion              # Search for plugins matching "notion"
  %(prog)s -c productivity        # List all productivity plugins
  %(prog)s -q "issue tracking"    # Search for issue tracking plugins
  %(prog)s --list-categories      # Show all available categories
  %(prog)s -q api -d              # Detailed search results
        """
    )

    parser.add_argument(
        '-q', '--query',
        help='Search query (searches in name and description)'
    )

    parser.add_argument(
        '-c', '--category',
        help='Filter by category'
    )

    parser.add_argument(
        '-t', '--tags',
        nargs='+',
        help='Filter by tags (space-separated)'
    )

    parser.add_argument(
        '-d', '--detailed',
        action='store_true',
        help='Show detailed information'
    )

    parser.add_argument(
        '--list-categories',
        action='store_true',
        help='List all available categories'
    )

    parser.add_argument(
        '--list-tags',
        action='store_true',
        help='List all available tags'
    )

    parser.add_argument(
        '--json',
        action='store_true',
        help='Output results as JSON'
    )

    args = parser.parse_args()

    # Load all marketplace data
    marketplace = ensure_all_marketplaces()
    plugins = marketplace.get('plugins', [])

    # Handle list commands
    if args.list_categories:
        categories = list_categories(plugins)
        print(f"\nAvailable categories ({len(categories)}):")
        for cat in categories:
            count = len([p for p in plugins if p.get('category') == cat])
            print(f"  • {cat} ({count} plugins)")
        return

    if args.list_tags:
        tags = list_tags(plugins)
        print(f"\nAvailable tags ({len(tags)}):")
        for tag in tags:
            print(f"  • {tag}")
        return

    # Search plugins
    results = search_plugins(
        plugins,
        query=args.query,
        category=args.category,
        tags=args.tags
    )

    # Output results
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print(f"\nFound {len(results)} plugin(s)")

        if len(results) == 0:
            print("\nNo plugins found matching your criteria.")
            print("Try broadening your search or checking available categories.")
        else:
            for plugin in results:
                print(format_plugin_output(plugin, detailed=args.detailed))


if __name__ == '__main__':
    main()
