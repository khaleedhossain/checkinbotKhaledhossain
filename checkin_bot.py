# INF601 - Advanced Programming in Python
# Khaleed Hossain
# Scheduled Check-In Bot

import os
import json
import requests
from datetime import datetime
from pathlib import Path


# ------------------------------------------------------------
# Environment variables
# ------------------------------------------------------------

API_URL = os.getenv(
    "PRACTICE_API_URL",
    "https://practice.fhsucyber.com"
).rstrip("/")

API_TOKEN = os.getenv("PRACTICE_API_TOKEN")
INSTRUCTOR_ID = int(os.getenv("INSTRUCTOR_ID", "7"))


# ------------------------------------------------------------
# Artifact directories
# ------------------------------------------------------------

ARTIFACT_DIR = Path("artifact")
FILES_DIR = ARTIFACT_DIR / "files"
COLLECTED_JSON = ARTIFACT_DIR / "collected.json"


# ------------------------------------------------------------
# API headers
# ------------------------------------------------------------

HEADERS = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}


# ------------------------------------------------------------
# Create artifact directories
# ------------------------------------------------------------

def ensure_artifact_dir():
    """Create artifact directory structure."""

    ARTIFACT_DIR.mkdir(exist_ok=True)
    FILES_DIR.mkdir(exist_ok=True)

    print("✓ Artifact directories ready")


# ------------------------------------------------------------
# Fetch posts
# ------------------------------------------------------------

def fetch_posts(user_id, page=1):
    """Fetch posts from Practice Hub API."""

    params = {
        "author_id": user_id,
        "page": page,
        "limit": 100
    }

    url = f"{API_URL}/api/v1/posts"

    try:
        response = requests.get(
            url,
            headers=HEADERS,
            params=params,
            timeout=10
        )

        response.raise_for_status()

        return response.json()

    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching posts (page {page}): {e}")
        return []


# ------------------------------------------------------------
# Download attachment
# ------------------------------------------------------------

def download_attachment(file_url, filename):
    """Download attachment from API."""

    try:
        response = requests.get(
            file_url,
            headers=HEADERS,
            timeout=30
        )

        response.raise_for_status()

        # Prevent a filename from creating an unexpected path
        safe_filename = Path(filename).name
        file_path = FILES_DIR / safe_filename

        with open(file_path, "wb") as f:
            f.write(response.content)

        print(f"  ✓ Downloaded: {safe_filename}")

        return str(file_path)

    except requests.exceptions.RequestException as e:
        print(f"  ❌ Error downloading {filename}: {e}")
        return None


# ------------------------------------------------------------
# Collect all instructor posts
# ------------------------------------------------------------

def collect_all_posts():
    """
    Collect instructor posts with full details and attachments.
    """

    print(
        f"\n📥 Collecting posts from instructor "
        f"(ID: {INSTRUCTOR_ID})..."
    )

    all_posts = []
    page = 1
    has_more = True
    total_attempted = 0

    while has_more:

        print(f"  Fetching page {page}...")

        try:
            response = requests.get(
                f"{API_URL}/api/v1/posts",
                headers=HEADERS,
                params={
                    "author_id": INSTRUCTOR_ID,
                    "page": page,
                    "limit": 100
                },
                timeout=10
            )

            response.raise_for_status()
            data = response.json()

        except requests.exceptions.RequestException as e:
            print(f"  ❌ Error fetching page {page}: {e}")
            break

        except ValueError as e:
            print(f"  ❌ Invalid JSON returned on page {page}: {e}")
            break

        # Practice Hub may return a list directly.
        # Also support {"data": [...]} in case the response format changes.
        if isinstance(data, list):
            posts = data

        elif isinstance(data, dict):
            posts = data.get("data", [])

        else:
            print(
                "  ❌ Unexpected API response format: "
                f"{type(data).__name__}"
            )
            break

        if not posts:
            print("  ℹ️  No posts returned")
            break

        # ----------------------------------------------------
        # Process each post
        # ----------------------------------------------------

        for post in posts:

            if not isinstance(post, dict):
                continue

            post_id = post.get("id")

            if not post_id:
                print("  ⚠️  Skipping post without ID")
                continue

            total_attempted += 1

            try:
                # Get full post details
                full_response = requests.get(
                    f"{API_URL}/api/v1/posts/{post_id}",
                    headers=HEADERS,
                    timeout=10
                )

                full_response.raise_for_status()
                full_post = full_response.json()

                if not isinstance(full_post, dict):
                    print(
                        f"  ⚠️  Unexpected response for post "
                        f"{post_id}"
                    )
                    continue

                post_data = {
                    "id": full_post.get("id"),
                    "title": full_post.get("title"),
                    "body": full_post.get("body"),
                    "tags": full_post.get("tags", []),
                    "created_at": full_post.get("created_at"),
                    "updated_at": full_post.get("updated_at"),
                    "files": []
                }

                # --------------------------------------------
                # Download attachments
                # --------------------------------------------

                attachments = full_post.get(
                    "attachments",
                    []
                )

                if attachments:

                    print(
                        f"  Post {post_id}: Downloading "
                        f"{len(attachments)} attachment(s)..."
                    )

                    for attachment in attachments:

                        if not isinstance(attachment, dict):
                            continue

                        file_url = attachment.get("url")

                        filename = attachment.get(
                            "filename",
                            f"file_{attachment.get('id')}"
                        )

                        if file_url:

                            file_path = download_attachment(
                                file_url,
                                filename
                            )

                            if file_path:

                                post_data["files"].append({
                                    "filename": filename,
                                    "path": file_path,
                                    "id": attachment.get("id")
                                })

                all_posts.append(post_data)

                print(
                    f"  ✓ Post {post_id}: "
                    f"{post_data.get('title', 'Untitled')}"
                )

            except requests.exceptions.RequestException as e:

                print(
                    f"  ❌ Error fetching post details "
                    f"{post_id}: {e}"
                )

                continue

            except ValueError as e:

                print(
                    f"  ❌ Invalid JSON for post "
                    f"{post_id}: {e}"
                )

                continue

        # ----------------------------------------------------
        # Pagination
        # ----------------------------------------------------

        # If fewer than 100 posts were returned,
        # there is no additional page.
        if len(posts) < 100:
            has_more = False
        else:
            page += 1


    # --------------------------------------------------------
    # Save collected posts
    # --------------------------------------------------------

    with open(COLLECTED_JSON, "w") as f:

        json.dump(
            {
                "collected_at": datetime.now().isoformat(),
                "instructor_id": INSTRUCTOR_ID,
                "total_posts": len(all_posts),
                "posts": all_posts
            },
            f,
            indent=2
        )


    print(
        f"\n✅ Collected {len(all_posts)} posts "
        f"(attempted {total_attempted})"
    )

    print(f"   Saved to: {COLLECTED_JSON}")

    if all_posts:

        total_files = sum(
            len(post.get("files", []))
            for post in all_posts
        )

        print(f"   Files downloaded: {total_files}")

    return all_posts


# ------------------------------------------------------------
# Determine whether a post is a check-in
# ------------------------------------------------------------

def is_checkin_post(title):
    """Check whether title contains 'check-in'."""

    if not title:
        return False

    return "check-in" in title.lower()


# ------------------------------------------------------------
# Check whether user already replied
# ------------------------------------------------------------

def has_user_reply(post_id):
    """
    Check whether the authenticated user already replied.

    This helps prevent duplicate replies when the GitHub
    workflow runs more than once.
    """

    try:

        response = requests.get(
            f"{API_URL}/api/v1/posts/{post_id}/comments",
            headers=HEADERS,
            timeout=10
        )

        response.raise_for_status()

        data = response.json()

        # API may return comments directly as a list
        if isinstance(data, list):
            comments = data

        elif isinstance(data, dict):
            comments = data.get("data", [])

        else:
            comments = []

        for comment in comments:

            if not isinstance(comment, dict):
                continue

            # API may identify comments created by
            # the authenticated user with is_own.
            if comment.get("is_own"):
                return True

        return False

    except requests.exceptions.RequestException as e:

        print(
            f"  ⚠️  Error checking existing comments "
            f"for post {post_id}: {e}"
        )

        return False

    except ValueError as e:

        print(
            f"  ⚠️  Invalid comments response for "
            f"post {post_id}: {e}"
        )

        return False


# ------------------------------------------------------------
# Reply to check-in
# ------------------------------------------------------------

def reply_to_checkin(post_id, title):
    """Reply to an open check-in post."""

    reply_text = (
        "Check-in received and logged. Ready for updates."
    )

    # Avoid duplicate replies
    if has_user_reply(post_id):

        print(
            f"  ℹ️  Already replied to post {post_id}"
        )

        return True


    try:

        response = requests.post(
            f"{API_URL}/api/v1/posts/{post_id}/comments",
            headers=HEADERS,
            json={
                "body": reply_text
            },
            timeout=10
        )


        # --------------------------------------------
        # Successful reply
        # --------------------------------------------

        if response.status_code == 201:

            print(
                f"  ✅ Replied to check-in post "
                f"{post_id}"
            )

            return True


        # --------------------------------------------
        # Check-in window closed
        # --------------------------------------------

        elif response.status_code == 423:

            print(
                f"  ⏰ Check-in window closed for "
                f"post {post_id} (423 Locked)"
            )

            return False


        # --------------------------------------------
        # Authentication error
        # --------------------------------------------

        elif response.status_code == 401:

            print(
                "  ❌ Unauthorized. Check "
                "PRACTICE_API_TOKEN."
            )

            return False


        # --------------------------------------------
        # Permission error
        # --------------------------------------------

        elif response.status_code == 403:

            print(
                f"  ❌ Forbidden from replying to "
                f"post {post_id}"
            )

            return False


        # --------------------------------------------
        # Post not found
        # --------------------------------------------

        elif response.status_code == 404:

            print(
                f"  ❌ Post {post_id} was not found"
            )

            return False


        # --------------------------------------------
        # Validation error
        # --------------------------------------------

        elif response.status_code == 422:

            print(
                f"  ❌ Validation error replying to "
                f"post {post_id}"
            )

            print(
                f"     Response: {response.text}"
            )

            return False


        # --------------------------------------------
        # Other errors
        # --------------------------------------------

        else:

            print(
                f"  ❌ Error replying to post "
                f"{post_id}: {response.status_code}"
            )

            print(
                f"     Response: {response.text}"
            )

            return False


    except requests.exceptions.RequestException as e:

        print(
            f"  ❌ Error replying to post "
            f"{post_id}: {e}"
        )

        return False


# ------------------------------------------------------------
# Process check-ins
# ------------------------------------------------------------

def process_checkins(posts):
    """Find check-in posts and process them."""

    print("\n📢 Processing check-in posts...")

    checkin_posts = [
        post
        for post in posts
        if is_checkin_post(
            post.get("title", "")
        )
    ]


    if not checkin_posts:

        print("  ℹ️  No check-in posts found")

        return 0


    print(
        f"  Found {len(checkin_posts)} "
        f"check-in post(s)"
    )


    replied_count = 0


    for post in checkin_posts:

        post_id = post.get("id")
        title = post.get("title")

        print(f"\n  Processing: {title}")

        if reply_to_checkin(
            post_id,
            title
        ):

            replied_count += 1


    return replied_count


# ------------------------------------------------------------
# Main
# ------------------------------------------------------------

def main():
    """Main bot logic."""

    print("=" * 60)

    print("🤖 Scheduled Check-In Bot")

    print(
        f"📅 Run time: "
        f"{datetime.now().isoformat()}"
    )

    print("=" * 60)


    # --------------------------------------------------------
    # Validate API token
    # --------------------------------------------------------

    if not API_TOKEN:

        print(
            "❌ Error: PRACTICE_API_TOKEN "
            "not set"
        )

        return False


    # --------------------------------------------------------
    # Create artifact directories
    # --------------------------------------------------------

    ensure_artifact_dir()


    # --------------------------------------------------------
    # Collect instructor posts
    # --------------------------------------------------------

    posts = collect_all_posts()


    # --------------------------------------------------------
    # Process check-ins
    # --------------------------------------------------------

    replied_count = process_checkins(
        posts
    )


    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    print("\n" + "=" * 60)

    print("✅ Bot execution complete")

    print(
        f"   Posts collected: "
        f"{len(posts)}"
    )

    print(
        f"   Check-ins replied to: "
        f"{replied_count}"
    )

    print("=" * 60)


    return True


# ------------------------------------------------------------
# Run program
# ------------------------------------------------------------

if __name__ == "__main__":

    success = main()

    exit(
        0 if success else 1
    )
