#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate release notes from git commits
Usage: python generate_release_notes.py [previous_tag]
"""

import subprocess
import sys
from datetime import datetime


def get_git_commits(from_tag=None):
    """Get commits since the specified tag or from beginning"""
    if from_tag:
        cmd = ['git', 'log', f'{from_tag}..HEAD', '--pretty=format:%h - %s (%an, %ar)']
    else:
        cmd = ['git', 'log', '--pretty=format:%h - %s (%an, %ar)']
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout.strip().split('\n')


def get_current_version():
    """Get current version from libs/__init__.py"""
    try:
        with open('libs/__init__.py', 'r') as f:
            for line in f:
                if '__version__' in line:
                    return line.split('=')[1].strip().strip("'\"")
    except:
        return 'unknown'


def categorize_commits(commits):
    """Categorize commits by type"""
    categories = {
        'Features': [],
        'Bug Fixes': [],
        'Improvements': [],
        'Documentation': [],
        'Build/CI': [],
        'Other': []
    }
    
    for commit in commits:
        if not commit:
            continue
            
        # Categorize based on commit message
        if any(keyword in commit.lower() for keyword in ['add', 'new', 'feat']):
            categories['Features'].append(commit)
        elif any(keyword in commit.lower() for keyword in ['fix', 'bug', 'patch']):
            categories['Bug Fixes'].append(commit)
        elif any(keyword in commit.lower() for keyword in ['improve', 'update', 'enhance', 'refactor']):
            categories['Improvements'].append(commit)
        elif any(keyword in commit.lower() for keyword in ['doc', 'readme']):
            categories['Documentation'].append(commit)
        elif any(keyword in commit.lower() for keyword in ['build', 'ci', 'github', 'workflow']):
            categories['Build/CI'].append(commit)
        else:
            categories['Other'].append(commit)
    
    return categories


def generate_release_notes(from_tag=None):
    """Generate formatted release notes"""
    version = get_current_version()
    commits = get_git_commits(from_tag)
    categories = categorize_commits(commits)
    
    notes = []
    notes.append(f'# Release v{version}\n')
    notes.append(f'**Release Date**: {datetime.now().strftime("%Y-%m-%d")}\n')
    
    # Add summary
    total_commits = sum(len(v) for v in categories.values())
    notes.append(f'**Total Changes**: {total_commits} commits\n')
    
    # Add categorized changes
    for category, items in categories.items():
        if items:
            notes.append(f'## {category}\n')
            for item in items:
                notes.append(f'- {item}')
            notes.append('')
    
    # Add installation instructions
    notes.append('## Installation\n')
    notes.append('### From PyPI\n```bash\npip install LabelCraft\n```\n')
    notes.append('### From Source\n```bash\ngit clone https://github.com/syd168/LabelCraft.git\ncd LabelCraft\npip install -r requirements.txt\npython main.py\n```\n')
    
    # Add download links (will be updated by GitHub Actions)
    notes.append('## Downloads\n')
    notes.append('- **Linux**: `linux_LabelCraft_' + version + '.tar.gz`')
    notes.append('- **Windows**: `windows_LabelCraft_' + version + '.zip`')
    notes.append('- **macOS**: `macOS_LabelCraft_' + version + '.zip` or `.dmg`')
    
    return '\n'.join(notes)


if __name__ == '__main__':
    from_tag = sys.argv[1] if len(sys.argv) > 1 else None
    notes = generate_release_notes(from_tag)
    print(notes)
    
    # Save to file
    with open('RELEASE_NOTES.md', 'w', encoding='utf-8') as f:
        f.write(notes)
    
    print(f'\nRelease notes saved to RELEASE_NOTES.md')
