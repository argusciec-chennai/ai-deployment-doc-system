import time
import os
import sys
import requests
from datetime import datetime
from dotenv import load_dotenv
from services.ticket_resolver import resolve_ticket
from services.llm_generator import generate_deployment_doc
from utils.code_parser import extract_code_signals

load_dotenv()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
OWNER = os.getenv("GITHUB_OWNER")
REPO = os.getenv("GITHUB_REPO")
if not GITHUB_TOKEN or not OWNER or not REPO:
    raise Exception("Missing required environment variables in .env file.")
HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}

def get_latest_open_pr():
    url = f"https://api.github.com/repos/{OWNER}/{REPO}/pulls"
    response = requests.get(url, headers=HEADERS)
    if response.status_code != 200:
        raise Exception(f"GitHub API Error: {response.status_code} - {response.text}")
    prs = response.json()
    if not prs:
        print("No open PRs found.")
        return None
    return prs[0]["number"]

def get_pr_details(pr_number):
    url = f"https://api.github.com/repos/{OWNER}/{REPO}/pulls/{pr_number}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch PR details: {response.status_code}")
    return response.json()

def get_pr_diff(pr_number):
    url = f"https://api.github.com/repos/{OWNER}/{REPO}/pulls/{pr_number}"
    headers_diff = HEADERS.copy()
    headers_diff["Accept"] = "application/vnd.github.v3.diff"
    response = requests.get(url, headers=headers_diff)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch PR diff: {response.status_code}")
    return response.text

def main():
    # Optional: Pass PR number as CLI argument
    if len(sys.argv) > 1:
        pr_number = int(sys.argv[1])
    else:
        pr_number = get_latest_open_pr()
        if not pr_number:
            return
    print(f"\nFetching PR #{pr_number}...\n")
    pr_data = get_pr_details(pr_number)
    pr_diff = get_pr_diff(pr_number)

    print("====== PR METADATA ======")
    print("Title:", pr_data["title"])
    print("Author:", pr_data["user"]["login"])
    print("Branch:", pr_data["head"]["ref"])
    print("Base Branch:", pr_data["base"]["ref"])
    print("State:", pr_data["state"])
    print("\n====== PR DESCRIPTION ======")
    print(pr_data["body"] or "No description provided.")
    print("\n====== DIFF SAMPLE (First 1000 chars) ======")
    print(pr_diff[:1000])

    ticket_info = resolve_ticket(
    pr_data["title"],
    pr_data.get("body"),
    pr_data["head"]["ref"]
    )

    print("\n====== TICKET RESOLUTION ======")

    if ticket_info["status"] == "FOUND":
      print("Linked Ticket ID:", ticket_info["ticket_id"])
      print("Resolution Source:", ticket_info["source"])

      ticket_details = ticket_info["ticket_details"]

      print("\n====== OPENPROJECT TICKET DETAILS ======")
      print("Project:", ticket_details["project_identifier"])
      print("Subject:", ticket_details["subject"])
      print("Status:", ticket_details["status"])
      print("Priority:", ticket_details["priority"])
      print("Description:", ticket_details["description"])
    else:
      print("Ticket Status: UNLINKED")

    context = {
      "pr_number": pr_data["number"],
      "pr_title": pr_data["title"],
      "pr_author": pr_data["user"]["login"],
      "branch": pr_data["head"]["ref"],
      "base": pr_data["base"]["ref"],
      "ticket": ticket_info.get("ticket_details")
    }
    signals = extract_code_signals(pr_diff)

    context["code_changes"] = signals


    print("\n====== STRUCTURED CONTEXT READY FOR LLM ======")
    print(context)
    start = time.time()

    clean_diff = "\n".join([
    	line for line in pr_diff.split("\n") if line.startswith("+") or line.startswith("-")])[:500]
    print("Diff size:", len(clean_diff))
    start = time.time() 
    doc = generate_deployment_doc(context, clean_diff)

    end = time.time()
    print("\n====== LLM RESPONSE TIME ======")
    print(f"{round(end - start, 2)} seconds")
    docs_dir = "docs"

    # Create docs directory if it doesn't exist
    os.makedirs(docs_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    file_path = f"{docs_dir}/deployment_pr_{context['pr_number']}_{timestamp}.md"

    with open(file_path, "w") as f:
      f.write(doc)

    print("\n====== DEPLOYMENT DOCUMENT GENERATED ======")
    print(f"Saved to: {file_path}")
    with open(file_path, "r") as f:
      for line in f:
        print(line, end="")



if __name__ == "__main__":
    main()
