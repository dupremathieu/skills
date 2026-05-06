#!/usr/bin/env python3
"""Redmine REST API helper for Claude Code skills.

Subcommands:
  configure        Store Redmine base URL and API key (URL in config file, key in libsecret)
  projects         List projects accessible to the API key
  versions         List versions of a project
  issues           Fetch issues of a project as JSON
  export           Fetch every issue of a project and write Markdown files,
                   organized in subdirectories per Target version.
"""

import argparse
import concurrent.futures
import getpass
import json
import os
import re
import sys
import unicodedata
import urllib.parse
from pathlib import Path

import requests
import secretstorage

CONFIG_DIR = Path(os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config"))) / "redmine"
CONFIG_FILE = CONFIG_DIR / "config"

PAGE_SIZE = 100
DEFAULT_OUTPUT = "tasks"
DEFAULT_WORKERS = 8


# ---------- config + auth -------------------------------------------------


def _server_host(url):
    return urllib.parse.urlparse(url).hostname or ""


def _read_config():
    if not CONFIG_FILE.is_file():
        return {}
    out = {}
    for line in CONFIG_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        out[k.strip()] = v.strip()
    return out


def _write_config(data):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    body = "\n".join(f"{k}={v}" for k, v in data.items()) + "\n"
    CONFIG_FILE.write_text(body, encoding="utf-8")
    try:
        os.chmod(CONFIG_FILE, 0o600)
    except OSError:
        pass


def _store_key(host, api_key):
    conn = secretstorage.dbus_init()
    collection = secretstorage.get_default_collection(conn)
    if collection.is_locked():
        collection.unlock()
    attrs = {"service": "redmine", "server": host}
    label = f"Redmine API key ({host})"
    for item in collection.search_items(attrs):
        item.delete()
    collection.create_item(label, attrs, api_key.encode())


def _load_key(host):
    conn = secretstorage.dbus_init()
    collection = secretstorage.get_default_collection(conn)
    if collection.is_locked():
        collection.unlock()
    attrs = {"service": "redmine", "server": host}
    items = list(collection.search_items(attrs))
    if not items:
        sys.exit(
            f"Error: no Redmine API key stored for {host}.\n"
            f"Run: python3 {sys.argv[0]} configure"
        )
    return items[0].get_secret().decode()


def _resolve_auth(args):
    """Return (server_url, api_key) from --server/--api-key flags or config + libsecret."""
    cfg = _read_config()
    server = getattr(args, "server", None) or cfg.get("server")
    if not server:
        sys.exit(
            "Error: no Redmine server configured.\n"
            f"Run: python3 {sys.argv[0]} configure"
        )
    server = server.rstrip("/")
    host = _server_host(server)
    api_key = getattr(args, "api_key", None) or os.environ.get("REDMINE_API_KEY") or _load_key(host)
    return server, api_key


# ---------- HTTP ----------------------------------------------------------


def _get(server, api_key, path, params=None):
    url = f"{server}{path}"
    headers = {"X-Redmine-API-Key": api_key, "Accept": "application/json"}
    resp = requests.get(url, headers=headers, params=params or {}, timeout=60)
    resp.raise_for_status()
    return resp.json()


def _paginated(server, api_key, path, params=None, key=None):
    """Yield items from a paginated Redmine collection endpoint.

    `key` is the JSON field carrying the array (e.g. "issues", "projects").
    """
    params = dict(params or {})
    params.setdefault("limit", PAGE_SIZE)
    offset = 0
    while True:
        params["offset"] = offset
        data = _get(server, api_key, path, params)
        items = data.get(key, [])
        for item in items:
            yield item
        total = data.get("total_count", 0)
        offset += len(items)
        if not items or offset >= total:
            return


# ---------- formatting helpers --------------------------------------------


_SLUG_STRIP_RE = re.compile(r"[^a-z0-9]+")


def slugify(text, max_len=60):
    if not text:
        return "untitled"
    norm = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    norm = norm.lower()
    norm = _SLUG_STRIP_RE.sub("-", norm).strip("-")
    if not norm:
        return "untitled"
    if len(norm) > max_len:
        norm = norm[:max_len].rstrip("-")
    return norm or "untitled"


_FS_BAD_RE = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def safe_dirname(text):
    """Sanitize a Target version name into a directory-safe string."""
    cleaned = _FS_BAD_RE.sub("_", text).strip().strip(".")
    return cleaned or "_unknown_version"


def yaml_quote(value):
    """Render a scalar as a double-quoted YAML string (always safe)."""
    if value is None:
        return '""'
    s = str(value).replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
    return f'"{s}"'


def _name_of(field):
    if isinstance(field, dict):
        return field.get("name") or field.get("login") or field.get("value") or ""
    return field or ""


def render_frontmatter(issue, server):
    fixed = issue.get("fixed_version") or {}
    rows = [
        ("id", issue.get("id")),
        ("subject", yaml_quote(issue.get("subject", ""))),
        ("tracker", yaml_quote(_name_of(issue.get("tracker")))),
        ("status", yaml_quote(_name_of(issue.get("status")))),
        ("priority", yaml_quote(_name_of(issue.get("priority")))),
        ("author", yaml_quote(_name_of(issue.get("author")))),
        ("assignee", yaml_quote(_name_of(issue.get("assigned_to")))),
        ("target_version", yaml_quote(_name_of(fixed))),
        ("category", yaml_quote(_name_of(issue.get("category")))),
        ("created_on", yaml_quote(issue.get("created_on", ""))),
        ("updated_on", yaml_quote(issue.get("updated_on", ""))),
        ("done_ratio", issue.get("done_ratio", 0)),
        ("url", yaml_quote(f"{server}/issues/{issue.get('id')}")),
    ]
    body = ["---"]
    for k, v in rows:
        body.append(f"{k}: {v}")
    body.append("---")
    return "\n".join(body)


def render_checklist(issue):
    items = issue.get("checklists") or []
    if not items:
        return ""
    lines = ["", "## Checklist", ""]
    for it in items:
        subject = (it.get("subject") or "").replace("\n", " ").strip()
        mark = "x" if it.get("is_done") else " "
        lines.append(f"- [{mark}] {subject}")
    return "\n".join(lines)


def render_journal(issue):
    journals = issue.get("journals") or []
    if not journals:
        return ""
    out = ["", "## Journal", ""]
    for j in journals:
        author = _name_of(j.get("user"))
        when = j.get("created_on", "")
        out.append(f"### {when} — {author}")
        details = j.get("details") or []
        if details:
            out.append("")
            for d in details:
                prop = d.get("property", "")
                name = d.get("name", "")
                old_v = d.get("old_value")
                new_v = d.get("new_value")
                old_s = old_v if old_v not in (None, "") else "∅"
                new_s = new_v if new_v not in (None, "") else "∅"
                label = f"{prop}.{name}" if prop and prop != "attr" else name
                out.append(f"- {label}: {old_s} → {new_s}")
        notes = (j.get("notes") or "").strip()
        if notes:
            out.append("")
            out.append(notes.replace("\r\n", "\n"))
        out.append("")
    return "\n".join(out).rstrip() + "\n"


def render_issue(issue, server):
    parts = [render_frontmatter(issue, server), ""]
    parts.append(f"# #{issue.get('id')} — {issue.get('subject', '')}")
    parts.append("")
    parts.append("## Description")
    parts.append("")
    desc = (issue.get("description") or "").replace("\r\n", "\n").strip()
    parts.append(desc if desc else "_(no description)_")
    checklist = render_checklist(issue)
    if checklist:
        parts.append(checklist)
    journal = render_journal(issue)
    if journal:
        parts.append("")
        parts.append(journal.rstrip())
    return "\n".join(parts).rstrip() + "\n"


# ---------- commands ------------------------------------------------------


def cmd_configure(_args):
    del _args
    print("Configuring Redmine helper.", file=sys.stderr)
    default_server = _read_config().get("server", "")
    prompt = f"Redmine base URL [{default_server}]: " if default_server else "Redmine base URL (e.g. https://redmine.example.org): "
    server = input(prompt).strip() or default_server
    if not server:
        sys.exit("Error: a base URL is required.")
    server = server.rstrip("/")
    host = _server_host(server)
    if not host:
        sys.exit(f"Error: could not parse hostname from {server!r}.")
    api_key = getpass.getpass(f"Redmine API key for {host}: ").strip()
    if not api_key:
        sys.exit("Error: an API key is required.")
    _write_config({"server": server})
    _store_key(host, api_key)
    print(f"Saved server URL to {CONFIG_FILE}", file=sys.stderr)
    print(f"Stored API key in libsecret for {host}", file=sys.stderr)


def cmd_projects(args):
    server, api_key = _resolve_auth(args)
    projects = list(_paginated(server, api_key, "/projects.json", key="projects"))
    if args.json:
        print(json.dumps(projects, indent=2, ensure_ascii=False))
        return
    for p in projects:
        print(f"{p.get('id'):>6}  {p.get('identifier','')!s:<30}  {p.get('name','')}")


def cmd_versions(args):
    server, api_key = _resolve_auth(args)
    data = _get(server, api_key, f"/projects/{args.project}/versions.json")
    versions = data.get("versions", [])
    if args.json:
        print(json.dumps(versions, indent=2, ensure_ascii=False))
        return
    for v in versions:
        print(f"{v.get('id'):>6}  {v.get('status',''):<8}  {v.get('name','')}")


def _build_issue_params(args):
    params = {"project_id": args.project}
    if getattr(args, "open_only", False):
        pass  # Redmine default = open
    elif getattr(args, "status", None):
        params["status_id"] = args.status
    else:
        params["status_id"] = "*"
    return params


def cmd_issues(args):
    server, api_key = _resolve_auth(args)
    params = _build_issue_params(args)
    if args.limit:
        params["limit"] = min(args.limit, PAGE_SIZE)
        data = _get(server, api_key, "/issues.json", params)
        print(json.dumps(data.get("issues", []), indent=2, ensure_ascii=False))
        return
    issues = list(_paginated(server, api_key, "/issues.json", params=params, key="issues"))
    print(json.dumps(issues, indent=2, ensure_ascii=False))


def _fetch_issue_detail(server, api_key, issue_id):
    data = _get(
        server,
        api_key,
        f"/issues/{issue_id}.json",
        params={"include": "journals,attachments,relations,checklists"},
    )
    return data.get("issue", {})


def cmd_export(args):
    server, api_key = _resolve_auth(args)
    output_root = Path(args.output)
    output_root.mkdir(parents=True, exist_ok=True)

    params = _build_issue_params(args)
    print(f"Listing issues for project '{args.project}' on {server}...", file=sys.stderr)
    listed = list(_paginated(server, api_key, "/issues.json", params=params, key="issues"))
    total = len(listed)
    if total == 0:
        print("No issues found.", file=sys.stderr)
        return
    print(f"Found {total} issue(s). Fetching details...", file=sys.stderr)

    fetch = (lambda i: i) if args.no_journals else (
        lambda i: _fetch_issue_detail(server, api_key, i["id"])
    )

    detailed = []
    done = 0
    if args.no_journals:
        detailed = listed
        done = total
    else:
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
            for issue in pool.map(fetch, listed):
                detailed.append(issue)
                done += 1
                if done % 20 == 0 or done == total:
                    print(f"  fetched {done}/{total}", file=sys.stderr)

    version_dirs = set()
    unversioned = 0
    for issue in detailed:
        fixed = issue.get("fixed_version") or {}
        version_name = _name_of(fixed)
        if version_name:
            target_dir = output_root / safe_dirname(version_name)
            version_dirs.add(version_name)
        else:
            target_dir = output_root
            unversioned += 1
        target_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{issue.get('id')}-{slugify(issue.get('subject', ''))}.md"
        (target_dir / filename).write_text(render_issue(issue, server), encoding="utf-8")

    print(
        f"Exported {len(detailed)} issue(s) to {output_root} "
        f"({len(version_dirs)} version dir(s), {unversioned} unversioned).",
        file=sys.stderr,
    )


# ---------- main ----------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(description="Redmine REST API helper")
    parser.add_argument("--server", default=None, help="Redmine base URL (overrides config)")
    parser.add_argument("--api-key", default=None, help="Redmine API key (overrides keyring)")

    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("configure", help="Store Redmine base URL + API key")

    p_projects = sub.add_parser("projects", help="List accessible projects")
    p_projects.add_argument("--json", action="store_true", help="Output raw JSON")

    p_versions = sub.add_parser("versions", help="List versions of a project")
    p_versions.add_argument("project", help="Project identifier or numeric id")
    p_versions.add_argument("--json", action="store_true", help="Output raw JSON")

    p_issues = sub.add_parser("issues", help="Fetch issues of a project as JSON")
    p_issues.add_argument("project", help="Project identifier or numeric id")
    p_issues.add_argument("--open-only", action="store_true", help="Only open issues")
    p_issues.add_argument("--status", help="Specific status_id (overrides default of *)")
    p_issues.add_argument("--limit", type=int, default=0, help="Limit to first N (default: all)")

    p_export = sub.add_parser(
        "export",
        help="Export every issue of a project as Markdown files",
    )
    p_export.add_argument("project", help="Project identifier or numeric id")
    p_export.add_argument(
        "--output", "-o", default=DEFAULT_OUTPUT,
        help=f"Output directory (default: {DEFAULT_OUTPUT})",
    )
    p_export.add_argument("--open-only", action="store_true", help="Only open issues")
    p_export.add_argument("--status", help="Specific status_id (overrides default of *)")
    p_export.add_argument(
        "--no-journals", action="store_true",
        help="Skip per-issue detail fetch (no journal/checklist), much faster",
    )
    p_export.add_argument(
        "--workers", type=int, default=DEFAULT_WORKERS,
        help=f"Parallel detail fetchers (default: {DEFAULT_WORKERS})",
    )

    args = parser.parse_args()
    handlers = {
        "configure": cmd_configure,
        "projects": cmd_projects,
        "versions": cmd_versions,
        "issues": cmd_issues,
        "export": cmd_export,
    }
    handlers[args.command](args)


if __name__ == "__main__":
    main()
