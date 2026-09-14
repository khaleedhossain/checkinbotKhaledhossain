# INF601 - Advanced Programming in Python
# Khaleed Hossain
# Scheduled Check-In Bot

import os
import json
import requests
from datetime import datetime
from pathlib import Path

# Environment variables
API_URL = os.getenv("PRACTICE_API_URL", "https://practice.fhsucyber.com")
API_TOKEN = os.getenv("PRACTICE_API_TOKEN")
INSTRUCTOR_ID = int(os.getenv("INSTRUCTOR_ID", "7"))

# Create artifact directory
ARTIFACT_DIR = Path("artifact")
FILES_DIR = ARTIFACT_DIR / "files"
COLLECTED_JSON = ARTIFACT_DIR / "collected.json"

# API headers
HEADERS = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

def ensure_artifact_dir():
    """Create artifact directory structure."""
    ARTIFACT_DIR.mkdir(exist_ok=True)
    FILES_DIR.mkdir(exist_ok=True)
    print(f"✓ Artifact directories ready")

def fetch_posts(user_id, page=1):
    """Fetch posts from Practice Hub API with pagination."""
    params = {
        "author_id": user_id,
        "page": page,
        "limit": 100
    }

    url = f"{API_URL}/api/v1/datasets/posts"

    try:
        response = requests.get(url, headers=HEADERS, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching posts (page {page}): {e}")
        return {"data": [], "pagination": {}}

def download_attachment(file_url, filename):
    """Download attachment from API."""
    try:
        response = requests.get(file_url, headers=HEADERS)
        response.raise_for_status()

        file_path = FILES_DIR / filename
        with open(file_path, 'wb') as f:
            f.write(response.content)

        print(f"  ✓ Downloaded: {filename}")
        return str(file_path)
    except requests.exceptions.RequestException as e:
        print(f"  ❌ Error downloading {filename}: {e}")
        return None

def collect_all_posts():
    """Collect all instructor posts with full details and attachments."""
    print(f"\n📥 Collecting posts from instructor (ID: {INSTRUCTOR_ID})...")

    all_posts = []
    page = 1
    has_more = True

    while has_more:
        print(f"  Fetching page {page}...")
        response = requests.get(
            f"{API_URL}/api/v1/datasets/posts",
            headers=HEADERS,
            params={"author_id": INSTRUCTOR_ID, "page": page, "limit": 100}
        )

        if response.status_code != 200:
            print(f"  ❌ Error fetching page {page}: {response.status_code}")
            break

        data = response.json()
        posts = data.get("data", [])

        if not posts:
            has_more = False
            break

        # Process each post
        for post in posts:
            post_id = post.get("id")

            # Fetch full post details to get complete body and attachments
            try:
                full_response = requests.get(
                    f"{API_URL}/api/v1/datasets/posts/{post_id}",
                    headers=HEADERS
                )
                full_response.raise_for_status()
                full_post = full_response.json()

                # Extract post details
                post_data = {
                    "id": full_post.get("id"),
                    "title": full_post.get("title"),
                    "body": full_post.get("body"),  # Full body, not truncated
                    "tags": full_post.get("tags", []),
                    "created_at": full_post.get("created_at"),
                    "updated_at": full_post.get("updated_at"),
                    "files": []
                }

                # Download attachments
                attachments = full_post.get("attachments", [])
                if attachments:
                    print(f"  Post {post_id}: Downloading {len(attachments)} attachment(s)...")
                    for attachment in attachments:
                        file_url = attachment.get("url")
                        filename = attachment.get("filename", f"file_{attachment.get('id')}")

                        if file_url:
                            file_path = download_attachment(file_url, filename)
                            if file_path:
                                post_data["files"].append({
                                    "filename": filename,
                                    "path": file_path,
                                    "id": attachment.get("id")
                                })

                all_posts.append(post_data)
                print(f"  ✓ Post {post_id}: {post_data['title']}")

            except requests.exceptions.RequestException as e:
                print(f"  ❌ Error fetching post details {post_id}: {e}")
                continue

        # Check if there are more pages
        pagination = data.get("pagination", {})
        if pagination.get("has_next"):
            page += 1
        else:
            has_more = False

    # Save collected posts to JSON
    with open(COLLECTED_JSON, 'w') as f:
        json.dump({
            "collected_at": datetime.now().isoformat(),
            "instructor_id": INSTRUCTOR_ID,
            "total_posts": len(all_posts),
            "posts": all_posts
        }, f, indent=2)

    print(f"\n✅ Collected {len(all_posts)} posts")
    print(f"   Saved to: {COLLECTED_JSON}")

    return all_posts

def is_checkin_post(title):
    """Check if a post is a check-in (title contains 'check-in')."""
    return "check-in" in title.lower()

def has_user_reply(post_id):
    """Check if we already replied to this post to avoid duplicates.

    Prevents posting multiple replies to the same check-in if the workflow
    is re-run or if the bot is triggered multiple times.
    """
    try:
        response = requests.get(
            f"{API_URL}/api/v1/datasets/posts/{post_id}/comments",
            headers=HEADERS
        )
        response.raise_for_status()
        comments = response.json().get("data", [])

        # Check if any comment is by the bot user (authenticated user)
        # The API will identify comments by the authenticated user
        for comment in comments:
            # Check if comment author matches our authenticated user
            if comment.get("is_own"):  # API marks our own comments with is_own
                return True

        return False
    except requests.exceptions.RequestException as e:
        print(f"  ⚠️  Error checking existing comments: {e}")
        # On error checking comments, assume no reply to be safe
        return False

def reply_to_checkin(post_id, title):
    """Reply to a check-in post.

    Attempts to post a reply to the check-in. Handles several cases:
    - 201: Successfully posted (returns True)
    - 423: Window closed (expected for old check-ins, returns False)
    - Other: API error (returns False)
    """
    reply_text = f"Check-in received and logged. Ready for updates."

    # Check if already replied to avoid duplicates on re-runs
    if has_user_reply(post_id):
        print(f"  ℹ️  Already replied to post {post_id}")
        return True

    try:
        response = requests.post(
            f"{API_URL}/api/v1/datasets/posts/{post_id}/comments",
            headers=HEADERS,
            json={"body": reply_text}
        )

        if response.status_code == 423:
            # Window closed - this is expected for old check-ins
            # Server enforces reply windows; 423 means window already closed
            print(f"  ⏰ Check-in window closed for post {post_id} (423 Locked)")
            return False
        elif response.status_code == 201:
            print(f"  ✅ Replied to check-in post {post_id}")
            return True
        else:
            # Unexpected status code
            print(f"  ❌ Error replying to post {post_id}: {response.status_code}")
            print(f"     Response: {response.text}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"  ❌ Error replying to post {post_id}: {e}")
        return False

def process_checkins(posts):
    """Process check-in posts and reply to open ones."""
    print(f"\n📢 Processing check-in posts...")

    checkin_posts = [p for p in posts if is_checkin_post(p.get("title", ""))]

    if not checkin_posts:
        print("  ℹ️  No check-in posts found")
        return 0

    print(f"  Found {len(checkin_posts)} check-in post(s)")

    replied_count = 0
    for post in checkin_posts:
        post_id = post.get("id")
        title = post.get("title")

        print(f"\n  Processing: {title}")
        if reply_to_checkin(post_id, title):
            replied_count += 1

    return replied_count

def main():
    """Main bot logic."""
    print("=" * 60)
    print("🤖 Scheduled Check-In Bot")
    print(f"📅 Run time: {datetime.now().isoformat()}")
    print("=" * 60)

    # Validate API token
    if not API_TOKEN:
        print("❌ Error: PRACTICE_API_TOKEN not set")
        return False

    # Ensure artifact directory
    ensure_artifact_dir()

    # Task 1: Collect all instructor posts
    posts = collect_all_posts()

    # Task 2: Process check-in posts
    replied_count = process_checkins(posts)

    # Summary
    print("\n" + "=" * 60)
    print("✅ Bot execution complete")
    print(f"   Posts collected: {len(posts)}")
    print(f"   Check-ins replied to: {replied_count}")
    print("=" * 60)

    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
