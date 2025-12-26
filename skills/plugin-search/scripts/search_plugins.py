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


def download_marketplace(github_url: str, file_path: str) -> bool:
    """
    Download the marketplace JSON file from GitHub API.
    Expects a GitHub repository URL (e.g., https://github.com/owner/repo).

    Args:
        github_url: GitHub repository URL
        file_path: Local path to save the file

    Returns:
        True if successful, False otherwise
    """
    try:
        # Extract owner/repo from GitHub URL
        match = re.search(r'github\.com/([^/]+)/([^/]+?)(?:\.git)?(?:/|$)', github_url)
        if not match:
            print(f"Error: Invalid GitHub URL: {github_url}", file=sys.stderr)
            return False

        owner = match.group(1)
        repo = match.group(2)

        # Construct GitHub API URL for the marketplace.json file
        api_url = f"https://api.github.com/repos/{owner}/{repo}/contents/.claude-plugin/marketplace.json"

        # Ensure directory exists
        dir_path = os.path.dirname(file_path)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)

        # Use GitHub API with proper headers
        result = subprocess.run(
            ['curl', '-sL', '-H', 'Accept: application/vnd.github.v3+json', api_url],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            print(f"Error: curl failed with code {result.returncode}", file=sys.stderr)
            if result.stderr:
                print(f"curl error: {result.stderr}", file=sys.stderr)
            return False

        # GitHub API returns the file content in base64
        try:
            import base64
            api_response = json.loads(result.stdout)

            if 'content' not in api_response:
                print(f"Error: GitHub API response missing 'content' field", file=sys.stderr)
                print(f"Response: {result.stdout[:200]}", file=sys.stderr)
                return False

            # Decode base64 content
            content = base64.b64decode(api_response['content']).decode('utf-8')

            # Validate JSON
            json.loads(content)

            # Write to file
            with open(file_path, 'w') as f:
                f.write(content)

            return True

        except (json.JSONDecodeError, KeyError) as e:
            print(f"Error: Invalid GitHub API response: {e}", file=sys.stderr)
            return False

    except subprocess.TimeoutExpired:
        print("Error: Download timeout", file=sys.stderr)
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
        file_path = os.path.join(DATA_DIR, f"{name}.json")

        # Download or use cached data
        if needs_update(file_path):
            if not download_marketplace(base_url, file_path):
                if not os.path.exists(file_path):
                    print(f"Warning: Skipping {name} marketplace (download failed)", file=sys.stderr)
                    continue
                else:
                    print(f"Warning: Using cached {name} data due to download failure.", file=sys.stderr)

        # Load and merge plugins
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                plugins = data.get('plugins', [])
                # Get owner from marketplace data
                owner_data = data.get('owner', {})
                owner_name = owner_data.get('name', 'Unknown') if isinstance(owner_data, dict) else 'Unknown'

                # Add marketplace name and owner to each plugin
                for plugin in plugins:
                    plugin['_marketplace'] = name
                    plugin['_owner'] = owner_name
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
    tags: List[str] = None,
    marketplace: str = None
) -> List[Dict[str, Any]]:
    """
    Search plugins based on query, category, tags, and marketplace.

    Args:
        plugins: List of plugin dictionaries
        query: Search term to match against name and description
        category: Filter by category
        tags: Filter by tags
        marketplace: Filter by marketplace name

    Returns:
        Filtered list of plugins
    """
    results = plugins

    # Filter by marketplace
    if marketplace:
        results = [
            p for p in results
            if p.get('_marketplace', '').lower() == marketplace.lower()
        ]

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

    # Filter by query (search in name, description, tags, category, keywords)
    # Supports multiple terms with OR logic (any term matches)
    if query:
        # Split query into individual terms
        query_terms = query.lower().split()

        filtered_results = []
        for plugin in results:
            # Build searchable text from multiple fields
            searchable_fields = [
                plugin.get('name', ''),
                plugin.get('description', ''),
                plugin.get('category', ''),
                ' '.join(plugin.get('tags', [])),
                ' '.join(plugin.get('keywords', []))
            ]
            searchable_text = ' '.join(searchable_fields).lower()

            # Check if ANY query term matches (OR logic)
            if any(term in searchable_text for term in query_terms):
                filtered_results.append(plugin)

        results = filtered_results

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


def format_plugin_compact(plugin: Dict[str, Any]) -> str:
    """Format a plugin in compact mode (optimized for token usage)."""
    name = plugin.get('name', 'Unknown')
    category = plugin.get('category', 'uncategorized')
    description = plugin.get('description', 'No description')
    owner = plugin.get('_owner', 'Unknown')

    return f"{name} ({category}) [{owner}] - {description}"


def format_plugin_output(plugin: Dict[str, Any], detailed: bool = False) -> str:
    """Format a plugin for display."""
    name = plugin.get('name', 'Unknown')
    description = plugin.get('description', 'No description')
    category = plugin.get('category', 'uncategorized')
    homepage = plugin.get('homepage', 'N/A')
    tags = plugin.get('tags', [])
    owner = plugin.get('_owner', 'Unknown')

    output = f"\n{'='*80}\n"
    output += f"📦 {name} [{owner}]\n"
    output += f"{'='*80}\n"
    output += f"Category: {category}\n"
    output += f"Description: {description}\n"

    if tags:
        output += f"Tags: {', '.join(tags)}\n"

    if detailed:
        # Determine the URL to use for GitHub API and extract plugin path
        source = plugin.get('source', 'N/A')
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
            repo_data = fetch_github_repo_info(owner, repo, branch, plugin_path)

            if repo_data:
                # Build stats line
                stats_parts = []

                # Stars
                stats_parts.append(f"⭐ Stars: {repo_data['stars']}")

                # MCP support
                mcp_status = "Yes" if repo_data.get('has_mcp') else "No"
                stats_parts.append(f"🔌 MCP: {mcp_status}")

                # Commands count
                commands = repo_data.get('commands', [])
                stats_parts.append(f"📜 Commands: {len(commands)}")

                # Skills count
                skills = repo_data.get('skills', [])
                stats_parts.append(f"🎯 Skills: {len(skills)}")

                # Last updated
                if repo_data['updated_at']:
                    from datetime import datetime
                    try:
                        updated = datetime.fromisoformat(repo_data['updated_at'].replace('Z', '+00:00'))
                        stats_parts.append(f"🕐 Last Updated: {updated.strftime('%Y-%m-%d')}")
                    except:
                        pass

                # Output stats line
                output += f"\n{' | '.join(stats_parts)}\n"

                # Show detailed lists if there are commands or skills
                if commands or skills:
                    output += f"\n"

                    if commands:
                        output += f"Commands:\n"
                        for cmd in commands[:5]:  # Show first 5
                            output += f"  - {cmd}\n"
                        if len(commands) > 5:
                            output += f"  ... and {len(commands) - 5} more\n"

                    if skills:
                        if commands:
                            output += f"\n"
                        output += f"Skills:\n"
                        for skill in skills[:5]:  # Show first 5
                            output += f"  - {skill}\n"
                        if len(skills) > 5:
                            output += f"  ... and {len(skills) - 5} more\n"

        # Add installation instructions in detailed mode
        marketplace_name = plugin.get('_marketplace', 'claude-plugins-official')

        # Get the marketplace repo path (owner/repo) from config
        marketplaces = load_marketplaces_config()
        marketplace_info = next((m for m in marketplaces if m['name'] == marketplace_name), None)
        marketplace_repo = None

        if marketplace_info:
            # Extract owner/repo from base_url
            base_url = marketplace_info['base_url']
            match = re.search(r'github\.com/([^/]+/[^/]+?)(?:\.git)?(?:/|$)', base_url)
            if match:
                marketplace_repo = match.group(1)

        # Fallback to marketplace name if we can't extract owner/repo
        if not marketplace_repo:
            marketplace_repo = f"anthropics/{marketplace_name}"

        output += f"\n{'─'*80}\n"
        output += f"📥 Installation:\n"
        output += f"  # First, add the marketplace (if not already added):\n"
        output += f"  /plugin marketplace add {marketplace_repo}\n\n"
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
  %(prog)s -q notion                    # Search for plugins matching "notion"
  %(prog)s --all                        # List all plugins (compact)
  %(prog)s --list                       # Show marketplaces and categories
  %(prog)s -d notion linear github      # Detailed info for specific plugins
  %(prog)s -q "issue tracking" -d       # Search with detailed results
  %(prog)s --all -m anthropics-skills   # List plugins from specific marketplace
  %(prog)s -c productivity              # List all productivity plugins
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
        nargs='*',
        metavar='PLUGIN',
        help='Show detailed information (optionally specify plugin names: -d notion linear)'
    )

    parser.add_argument(
        '--list',
        action='store_true',
        help='List all marketplaces and categories'
    )

    parser.add_argument(
        '--all',
        action='store_true',
        help='List all plugins (no search query required)'
    )

    parser.add_argument(
        '-m', '--marketplace',
        help='Filter by marketplace (e.g., claude-plugins-official, anthropics-skills, claude-code-templates)'
    )

    args = parser.parse_args()

    # Load all marketplace data
    marketplace = ensure_all_marketplaces()
    plugins = marketplace.get('plugins', [])

    # Handle list commands
    if args.list:
        # List marketplaces
        marketplaces = load_marketplaces_config()
        print(f"\nMarketplaces ({len(marketplaces)}):")
        for m in marketplaces:
            name = m['name']
            base_url = m['base_url']
            count = len([p for p in plugins if p.get('_marketplace') == name])
            print(f"  • {name} ({count} plugins)")
            print(f"    {base_url}")

        # List categories
        categories = list_categories(plugins)
        print(f"\nCategories ({len(categories)}):")
        for cat in categories:
            count = len([p for p in plugins if p.get('category') == cat])
            print(f"  • {cat} ({count} plugins)")
        return

    # Handle -d with specific plugin names
    if args.detailed is not None and len(args.detailed) > 0:
        # Specific plugin names provided with -d
        plugin_names = [name.lower() for name in args.detailed]
        results = [p for p in plugins if p.get('name', '').lower() in plugin_names]

        print(f"\nFound {len(results)} plugin(s)")

        if len(results) == 0:
            print("\nNo plugins found with the specified names.")
            print(f"Searched for: {', '.join(args.detailed)}")
        else:
            for plugin in results:
                print(format_plugin_output(plugin, detailed=True))

            # Show tip if more than 3 results
            if len(results) > 3:
                print("\n" + "="*80)
                print("**TIP**: Use the AskUserQuestion tool to narrow down the users requirements")
                print("="*80)
    else:
        # Normal search flow
        if args.all:
            # When --all is used, don't filter by query (show all plugins)
            results = search_plugins(
                plugins,
                query=None,
                category=args.category,
                tags=args.tags,
                marketplace=args.marketplace
            )
        else:
            # Search plugins with query
            results = search_plugins(
                plugins,
                query=args.query,
                category=args.category,
                tags=args.tags,
                marketplace=args.marketplace
            )

        # Output results
        print(f"\nFound {len(results)} plugin(s)")

        if len(results) == 0:
            print("\nNo plugins found matching your criteria.")
            print("Try broadening your search or checking available categories.")
        else:
            # Use detailed format when -d is specified (without args), otherwise use compact format
            if args.detailed is not None:
                for plugin in results:
                    print(format_plugin_output(plugin, detailed=True))

                # Show tip if more than 3 results
                if len(results) > 3:
                    print("\n" + "="*80)
                    print("**TIP**: Use the AskUserQuestion tool to narrow down the users requirements")
                    print("="*80)
            else:
                print()  # Empty line before list
                for i, plugin in enumerate(results, 1):
                    print(f"{i}. {format_plugin_compact(plugin)}")


if __name__ == '__main__':
    main()
