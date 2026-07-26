#!/usr/bin/env python3
"""Publish the directory to GitHub Pages."""

import os, sys, subprocess, json

REPO_DIR = os.path.dirname(os.path.abspath(__file__))

def get_token():
    token_path = os.path.expanduser("~/younggrasshopper-website/.token")
    if os.path.exists(token_path):
        with open(token_path) as f:
            return f.read().strip()
    return os.environ.get("GITHUB_TOKEN", "")

def run(cmd, cwd=REPO_DIR):
    result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"⚠️ {result.stderr.strip()}")
    return result.stdout.strip()

def main():
    token = get_token()
    if not token:
        print("❌ No GitHub token found")
        sys.exit(1)

    repo_url = f"https://creeklava-svg:{token}@github.com/creeklava-svg/directory.grasshopperlocal.com.git"

    # Configure git
    run('git config user.email "hermes@younggrasshopper.io"')
    run('git config user.name "Hermes Agent"')

    # Check if there's anything to commit
    status = run("git status --porcelain")
    if not status:
        print("✅ No changes to publish")
        return

    # Add, commit, push
    run("git add -A")
    run(f'git commit -m "Auto-update: {len(status.splitlines())} files changed [skip ci]"')
    run(f"git push {repo_url} main")

    print(f"✅ Published to https://directory.grasshopperlocal.com")

if __name__ == "__main__":
    main()
