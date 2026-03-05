import re


def extract_code_signals(diff: str):
    """
    Extract useful signals from git diff
    """

    added_lines = []
    removed_lines = []

    added_endpoints = []
    removed_endpoints = []

    added_functions = []
    removed_functions = []

    for line in diff.split("\n"):

        # ------------------------
        # Added lines
        # ------------------------
        if line.startswith("+") and not line.startswith("+++"):

            code = line[1:].strip()

            if code:
                added_lines.append(code)

            # detect endpoints
            if "@app." in code:
                added_endpoints.append(code)

            # detect functions
            if code.startswith("def "):
                fn = re.findall(r"def (\w+)", code)
                if fn:
                    added_functions.append(fn[0])

        # ------------------------
        # Removed lines
        # ------------------------
        if line.startswith("-") and not line.startswith("---"):

            code = line[1:].strip()

            if code:
                removed_lines.append(code)

            # detect endpoints
            if "@app." in code:
                removed_endpoints.append(code)

            # detect functions
            if code.startswith("def "):
                fn = re.findall(r"def (\w+)", code)
                if fn:
                    removed_functions.append(fn[0])

    return {
        "added_lines": added_lines,
        "removed_lines": removed_lines,
        "added_endpoints": added_endpoints,
        "removed_endpoints": removed_endpoints,
        "added_functions": added_functions,
        "removed_functions": removed_functions
    }
