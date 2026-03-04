import re
import requests
import os
from dotenv import load_dotenv

load_dotenv()

OPENPROJECT_URL = os.getenv("OPENPROJECT_URL")
OPENPROJECT_TOKEN = os.getenv("OPENPROJECT_TOKEN")
EXPECTED_PROJECT_IDENTIFIER = os.getenv("EXPECTED_PROJECT_IDENTIFIER")

HEADERS = {
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

    response = requests.get(search_url, headers=HEADERS,auth=("apikey", OPENPROJECT_TOKEN), params=params)

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
    Full resolution flow with project validation.
    """

    ticket = None
    source = None

    # Step 1: From PR description
    ticket = extract_ticket_id_from_text(pr_description)
    if ticket:
        source = "PR_DESCRIPTION"

    # Step 2: From branch name
    if not ticket:
        ticket = extract_ticket_id_from_text(branch_name)
        if ticket:
            source = "BRANCH_NAME"

    # Step 3: Search by title keywords
    if not ticket:
        result = search_openproject_by_keywords(pr_title)
        if result:
            ticket = str(result["id"])
            source = "TITLE_SEARCH"

    if not ticket:
        return {"status": "UNLINKED"}

    #  Fetch full ticket details
    ticket_details = fetch_ticket_details(ticket)

    if not ticket_details:
        return {"status": "UNLINKED"}

    #  Project validation
    if EXPECTED_PROJECT_IDENTIFIER and \
       ticket_details["project_identifier"] != EXPECTED_PROJECT_IDENTIFIER:
        print("Ticket belongs to different project. Marking as UNLINKED.")
        return {"status": "UNLINKED"}

    return {
        "status": "FOUND",
        "ticket_id": ticket_details["id"],
        "source": source,
        "ticket_details": ticket_details
    }


def fetch_ticket_details(ticket_id):
    if not OPENPROJECT_URL or not OPENPROJECT_TOKEN:
        print("OpenProject credentials not configured.")
        return None

    # Normalize ticket ID
    import re
    numeric_id = None

    if str(ticket_id).isdigit():
        numeric_id = ticket_id
    else:
        match = re.search(r"(\d+)$", ticket_id)
        if match:
            numeric_id = match.group(1)

    if not numeric_id:
        print(f"Invalid ticket ID format: {ticket_id}")
        return None

    url = f"{OPENPROJECT_URL}/api/v3/work_packages/{numeric_id}"

    response = requests.get(url, headers=HEADERS,auth=("apikey", OPENPROJECT_TOKEN))

    if response.status_code != 200:
        print(f"Failed to fetch ticket {numeric_id}: {response.status_code}")
        return None


    ticket = response.json()

    # Extract structured fields safely
    embedded = ticket.get("_embedded", {})

    return {
        "id": ticket.get("id"),
        "subject": ticket.get("subject"),
        "project_identifier": embedded.get("project", {}).get("identifier"),
        "project_name": embedded.get("project", {}).get("name"),
        "status": embedded.get("status", {}).get("name"),
        "priority": embedded.get("priority", {}).get("name"),
        "description": ticket.get("description", {}).get("raw")
        if ticket.get("description") else None
    }
