import requests
import json
import os

OLLAMA_URL = os.getenv(
    "OLLAMA_URL",
    "http://localhost:11434/api/generate"
)

def generate_deployment_doc(context, diff):

    changes = context.get("code_changes", {})
    prompt = f"""
        You are a DevOps assistant.

        Write a concise deployment note.

        TICKET DETAILS:
        Project: {context["ticket"]["project_identifier"]}
        Ticket ID: {context["ticket"]["id"]}
        Subject: {context["ticket"]["subject"]}

        PR DETAILS:
        Title: {context["pr_title"]}
        Author: {context["pr_author"]}
        Branch: {context["branch"]}

	CODE CHANGES:

  	Added Endpoints:
	{changes.get("added_endpoints")}

	Removed Endpoints:
	{changes.get("removed_endpoints")}

	Added Functions:
	{changes.get("added_functions")}

	Removed Functions:
	{changes.get("removed_functions")}
        CODE DIFF:
        {diff}

        GENERATE:
        1. PR Summary
        2. Ticket Information
        3. Code Changes Summary
        4. Impact
        5. Risk level: Low/Medium/High
        6. Deployment notes
	"""
    print("PROMPT LENGTH:", len(prompt))

    payload = {
        "model": "phi3",
        "prompt": prompt,
        "stream": False,
        "keep_alive": "10m",
        "options": {
            "temperature": 0.1,
            "num_predict": 400,
	    "num_ctx": 1024
        }
    }

    response = requests.post(OLLAMA_URL, json=payload)

    if response.status_code != 200:
        raise Exception(f"Ollama error: {response.text}")

    data = response.json()
    print(response.json())

    return data.get("response", "No response generated.")
