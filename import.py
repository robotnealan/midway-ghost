#!/usr/bin/env python3
"""Import Ghost content from MySQL export JSON into new Ghost instance via Admin API."""

import hmac
import hashlib
import json
import time
import base64
import urllib.request
import urllib.error
import sys

GHOST_URL = "https://robertnealan-ghost.fly.dev"
KEY_ID = "bbb00000000000000000001"
KEY_SECRET = "abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
EXPORT_FILE = "/Users/robertnealan/Documents/projects/_archive/ghost-robertnealan/ghost-archive/ghost-export.json"


def make_token():
    secret = bytes.fromhex(KEY_SECRET)
    header = {"alg": "HS256", "typ": "JWT", "kid": KEY_ID}
    now = int(time.time())
    payload = {"iat": now, "exp": now + 300, "aud": "/admin/"}

    def b64url(data):
        return base64.urlsafe_b64encode(json.dumps(data).encode()).rstrip(b"=").decode()

    h = b64url(header)
    p = b64url(payload)
    sig = base64.urlsafe_b64encode(
        hmac.new(secret, f"{h}.{p}".encode(), hashlib.sha256).digest()
    ).rstrip(b"=").decode()
    return f"{h}.{p}.{sig}"


def api_request(method, endpoint, data=None):
    token = make_token()
    url = f"{GHOST_URL}/ghost/api/admin/{endpoint}"
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(
        url,
        data=body,
        method=method,
        headers={
            "Authorization": f"Ghost {token}",
            "Content-Type": "application/json",
        },
    )
    try:
        resp = urllib.request.urlopen(req, timeout=30)
        return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()[:500]
        print(f"  API Error {e.code}: {error_body}")
        return None


def main():
    with open(EXPORT_FILE) as f:
        export = json.load(f)

    posts = export["data"]["posts"]
    tags = export["data"]["tags"]
    posts_tags = export["data"]["posts_tags"]

    # Build tag lookup: old_id -> tag data
    tag_by_id = {t["id"]: t for t in tags}

    # Build post -> tag mapping
    post_tag_map = {}
    for pt in posts_tags:
        post_tag_map.setdefault(pt["post_id"], []).append(pt["tag_id"])

    # Sort posts: published first, then by published_at
    posts.sort(key=lambda p: (0 if p["status"] == "published" else 1, p.get("published_at") or ""))

    # First, create all tags
    print(f"Creating {len(tags)} tags...")
    tag_slug_to_new = {}
    for tag in tags:
        result = api_request("POST", "tags/", {"tags": [{"name": tag["name"], "slug": tag["slug"], "description": tag.get("description")}]})
        if result and "tags" in result:
            new_tag = result["tags"][0]
            tag_slug_to_new[tag["slug"]] = new_tag
            print(f"  + {tag['name']}")
        else:
            # Tag might already exist, try to find it
            print(f"  ? {tag['name']} (may already exist)")

    # Import posts
    print(f"\nImporting {len(posts)} posts...")
    success = 0
    failed = 0

    for post in posts:
        html = post.get("html") or ""
        if not html and post.get("mobiledoc"):
            # Try to extract HTML from mobiledoc
            try:
                md = json.loads(post["mobiledoc"]) if isinstance(post["mobiledoc"], str) else post["mobiledoc"]
                # mobiledoc cards may contain HTML
                for section in md.get("sections", []):
                    if section[0] == 1:  # markup section
                        html += f"<p>{''.join(str(m) for m in section[2:])}</p>"
            except (json.JSONDecodeError, KeyError, TypeError):
                pass

        # Rewrite image URLs to relative paths
        if html:
            html = html.replace("https://robertnealan.com/content/images/", "/content/images/")

        feature_image = post.get("feature_image")
        if feature_image:
            feature_image = feature_image.replace("https://robertnealan.com/content/", "/content/")

        # Build tag list for this post
        post_tags = []
        for tag_id in post_tag_map.get(post["id"], []):
            tag = tag_by_id.get(tag_id)
            if tag:
                post_tags.append({"name": tag["name"], "slug": tag["slug"]})

        post_data = {
            "title": post["title"],
            "slug": post["slug"],
            "html": html,
            "status": post["status"],
            "feature_image": feature_image,
            "custom_excerpt": post.get("custom_excerpt"),
            "published_at": post.get("published_at"),
            "created_at": post.get("created_at"),
            "updated_at": post.get("updated_at"),
            "tags": post_tags,
        }

        # Remove None values
        post_data = {k: v for k, v in post_data.items() if v is not None}

        result = api_request("POST", "posts/?source=html", {"posts": [post_data]})
        if result and "posts" in result:
            status_label = post["status"]
            print(f"  + [{status_label}] {post['title']}")
            success += 1
        else:
            print(f"  x FAILED: {post['title']}")
            failed += 1

        # Small delay to avoid overwhelming the API
        time.sleep(0.3)

    print(f"\nDone: {success} imported, {failed} failed (out of {len(posts)} total)")


if __name__ == "__main__":
    main()
