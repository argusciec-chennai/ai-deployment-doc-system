import re
import requests
import os
from dotenv import load_dotenv

load_dotenv()

OPENPROJECT_URL = os.getenv("OPENPROJECT_URL")
OPENPROJECT_TOKEN = os.getenv("OPENPROJECT_TOKEN")

HEADERS = {
    "Authorization": f"Bearer {OPENPROJECT_TOKEN}",
    "Content-Type": "application/json"
}


def extract_ticket_id_from_text(text):
    if not text:
        return None
    pattern = r"\b[A-Z]+(?:-[A-Z]+)*-\d+\b|\b\d+\b"
    match = re.search(pattern, text)
    return match.group(0) if match else None


def search_openproject_by_keywords(title):
    """
    Search OpenProject by title keywords.
    """
    if not OPENPROJECT_URL or not OPENPROJECT_TOKEN:
        print("OpenProject credentials not configured.")
        return None

    search_url = f"{OPENPROJECT_URL}/api/v3/work_packages"
    params = {
        "filters": f'[{{"subject": {{"operator": "~", "values": ["{title}"]}}}}]'
    }

    response = requests.get(search_url, headers=HEADERS, params=params)

    if response.status_code != 200:
        print("OpenProject search failed.")
        return None

    data = response.json()
    results = data.get("_embedded", {}).get("elements", [])

    if len(results) == 1:
        return results[0]
    else:
        return None


def resolve_ticket(pr_title, pr_description, branch_name):
    """
    Full resolution flow.
    """

    # Step 1: From PR description
    ticket = extract_ticket_id_from_text(pr_description)
    if ticket:
        return {"status": "FOUND", "ticket_id": ticket, "source": "PR_DESCRIPTION"}

    # Step 2: From branch name
    ticket = extract_ticket_id_from_text(branch_name)
    if ticket:
        return {"status": "FOUND", "ticket_id": ticket, "source": "BRANCH_NAME"}

    # Step 3: Search by title keywords
    result = search_openproject_by_keywords(pr_title)
    if result:
        return {
            "status": "FOUND",
            "ticket_id": result["id"],
            "source": "TITLE_SEARCH"
        }

    return {"status": "UNLINKED"}
