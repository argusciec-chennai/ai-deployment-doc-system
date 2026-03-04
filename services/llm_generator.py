import requests
import json

OLLAMA_URL = "http://localhost:11434/api/generate"


def generate_deployment_doc(context, diff):

    prompt = f"""
        You are a DevOps assistant.

        Generate deployment documentation based on the following pull request.

        Ticket:
        Project: {context["ticket"]["project_identifier"]}
        Ticket ID: {context["ticket"]["id"]}
        Subject: {context["ticket"]["subject"]}

        Pull Request:
        Title: {context["pr_title"]}
        Author: {context["pr_author"]}
        Branch: {context["branch"]}

        Code Changes:
        {diff}

        Generate a short deployment summary including:
        1. Summary of Change
        2. Impact
        3. Risk level
        4. Deployment notes
        """

    payload = {
        "model": "phi3",
        "prompt": prompt,
        "stream": False,
        "keep_alive": "10m",
        "options": {
            "temperature": 0.1,
            "num_predict": 150,
	    "num_ctx": 1024
        }
    }

    response = requests.post(OLLAMA_URL, json=payload)

    if response.status_code != 200:
        raise Exception(f"Ollama error: {response.text}")

    data = response.json()

    return data.get("response", "No response generated.")
