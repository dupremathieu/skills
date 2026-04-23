#!/usr/bin/env python3
"""Gerrit REST API helper for Claude Code review skill.

Subcommands:
  store-password   Store Gerrit HTTP password securely in libsecret keyring
  query            Search for changes matching a query
  commit           Get commit info (including message) for a change
  patch            Get unified diff patch for a change
  comments         List published review comments on a change
  draft            Post a draft comment on a change
"""

import argparse
import base64
import getpass
import json
import subprocess
import sys
import urllib.parse

import requests
import secretstorage

DEFAULT_SERVER = "https://g1.sfl.io"
SECRET_SCHEMA = {"service": "gerrit", "server": "", "username": ""}


def get_git_config(key):
    """Get a value from git config, or None if not set."""
    try:
        return subprocess.check_output(
            ["git", "config", key], text=True, stderr=subprocess.DEVNULL
        ).strip()
    except subprocess.CalledProcessError:
        return None


def get_default_username():
    return get_git_config("gitreview.username")


def get_server_host(server_url):
    """Extract hostname from server URL."""
    return urllib.parse.urlparse(server_url).hostname


def store_password(server, username):
    """Store Gerrit HTTP password in libsecret keyring."""
    host = get_server_host(server)
    password = getpass.getpass(f"Gerrit HTTP password for {username}@{host}: ")

    conn = secretstorage.dbus_init()
    collection = secretstorage.get_default_collection(conn)
    if collection.is_locked():
        collection.unlock()

    attrs = {"service": "gerrit", "server": host, "username": username}
    label = f"Gerrit HTTP password ({username}@{host})"

    # Delete existing entry if present
    for item in collection.search_items(attrs):
        item.delete()

    collection.create_item(label, attrs, password.encode())
    print(f"Password stored for {username}@{host}", file=sys.stderr)


def get_password(server, username):
    """Retrieve Gerrit HTTP password from libsecret keyring."""
    host = get_server_host(server)
    conn = secretstorage.dbus_init()
    collection = secretstorage.get_default_collection(conn)
    if collection.is_locked():
        collection.unlock()

    attrs = {"service": "gerrit", "server": host, "username": username}
    items = list(collection.search_items(attrs))
    if not items:
        print(
            f"Error: No password found for {username}@{host}.\n"
            f"Run: python3 ~/.claude/scripts/gerrit-review.py store-password --username {username}",
            file=sys.stderr,
        )
        sys.exit(1)
    return items[0].get_secret().decode()


def gerrit_get(server, username, password, endpoint):
    """Make authenticated GET request to Gerrit REST API."""
    url = f"{server}/a{endpoint}"
    resp = requests.get(url, auth=(username, password))
    resp.raise_for_status()
    # Strip Gerrit's )]}' security prefix
    text = resp.text
    if text.startswith(")]}'"):
        text = text.split("\n", 1)[1]
    return text


def gerrit_put(server, username, password, endpoint, data):
    """Make authenticated PUT request to Gerrit REST API."""
    url = f"{server}/a{endpoint}"
    resp = requests.put(
        url, auth=(username, password), json=data,
        headers={"Content-Type": "application/json"},
    )
    resp.raise_for_status()
    text = resp.text
    if text.startswith(")]}'"):
        text = text.split("\n", 1)[1]
    return text


def cmd_query(args):
    password = get_password(args.server, args.username)
    query_encoded = urllib.parse.quote(args.query, safe="")
    endpoint = f"/changes/?q={query_encoded}&o=CURRENT_REVISION&o=CURRENT_FILES"
    result = gerrit_get(args.server, args.username, password, endpoint)
    # Pretty-print JSON
    data = json.loads(result)
    print(json.dumps(data, indent=2))


def cmd_commit(args):
    password = get_password(args.server, args.username)
    endpoint = f"/changes/{args.change}/revisions/{args.revision}/commit"
    result = gerrit_get(args.server, args.username, password, endpoint)
    data = json.loads(result)
    print(json.dumps(data, indent=2))


def cmd_patch(args):
    password = get_password(args.server, args.username)
    endpoint = f"/changes/{args.change}/revisions/{args.revision}/patch"
    result = gerrit_get(args.server, args.username, password, endpoint)
    # Response is base64-encoded unified diff (raw text, no JSON wrapper)
    patch_bytes = base64.b64decode(result.strip())
    sys.stdout.buffer.write(patch_bytes)


def cmd_comments(args):
    password = get_password(args.server, args.username)
    endpoint = f"/changes/{args.change}/comments"
    result = gerrit_get(args.server, args.username, password, endpoint)
    data = json.loads(result)
    print(json.dumps(data, indent=2))


def cmd_draft(args):
    password = get_password(args.server, args.username)
    endpoint = f"/changes/{args.change}/revisions/{args.revision}/drafts"
    data = json.loads(args.body)
    # Always post drafts as unresolved so they require explicit resolution
    data["unresolved"] = True
    result = gerrit_put(args.server, args.username, password, endpoint, data)
    parsed = json.loads(result)
    print(json.dumps(parsed, indent=2))


def main():
    parser = argparse.ArgumentParser(description="Gerrit REST API helper")
    parser.add_argument(
        "--server", default=DEFAULT_SERVER, help="Gerrit server URL"
    )
    parser.add_argument(
        "--username", default=None, help="Gerrit username (default: gitreview.username)"
    )

    sub = parser.add_subparsers(dest="command", required=True)

    # store-password
    sub.add_parser("store-password", help="Store Gerrit HTTP password in keyring")

    # query
    p_query = sub.add_parser("query", help="Search for changes")
    p_query.add_argument("query", help="Gerrit search query string")

    # commit
    p_commit = sub.add_parser("commit", help="Get commit info for a change")
    p_commit.add_argument("change", help="Change number")
    p_commit.add_argument("revision", help="Revision ID (SHA or 'current')")

    # patch
    p_patch = sub.add_parser("patch", help="Get unified diff patch")
    p_patch.add_argument("change", help="Change number")
    p_patch.add_argument("revision", help="Revision ID (SHA or 'current')")

    # comments
    p_comments = sub.add_parser("comments", help="List published review comments on a change")
    p_comments.add_argument("change", help="Change number")

    # draft
    p_draft = sub.add_parser("draft", help="Post a draft comment")
    p_draft.add_argument("change", help="Change number")
    p_draft.add_argument("revision", help="Revision ID (SHA or 'current')")
    p_draft.add_argument("body", help="JSON body for the draft comment")

    args = parser.parse_args()

    # Resolve username default
    if args.username is None:
        args.username = get_default_username()
        if args.username is None:
            print(
                "Error: No username specified and gitreview.username not set.\n"
                "Use --username or run: git config gitreview.username <user>",
                file=sys.stderr,
            )
            sys.exit(1)

    if args.command == "store-password":
        store_password(args.server, args.username)
    elif args.command == "query":
        cmd_query(args)
    elif args.command == "commit":
        cmd_commit(args)
    elif args.command == "patch":
        cmd_patch(args)
    elif args.command == "comments":
        cmd_comments(args)
    elif args.command == "draft":
        cmd_draft(args)


if __name__ == "__main__":
    main()
