import unittest
from services.ticket_resolver import extract_ticket_id_from_text, resolve_ticket


class TestTicketResolver(unittest.TestCase):

    # -----------------------------
    # 1️⃣ Description Contains Ticket
    # -----------------------------
    def test_extract_from_description(self):
        description = "This fixes AI-DOC-38 issue"
        result = extract_ticket_id_from_text(description)
        self.assertEqual(result, "AI-DOC-38")

    # -----------------------------
    # 2️⃣ Branch Contains Ticket
    # -----------------------------
    def test_extract_from_branch(self):
        branch = "feature/AI-DOC-45-new-endpoint"
        result = extract_ticket_id_from_text(branch)
        self.assertEqual(result, "AI-DOC-45")

    # -----------------------------
    # 3️⃣ No Ticket In Text
    # -----------------------------
    def test_no_ticket_in_text(self):
        text = "Added new login endpoint"
        result = extract_ticket_id_from_text(text)
        self.assertIsNone(result)

    # -----------------------------
    # 4️⃣ Resolve - Description Priority
    # -----------------------------
    def test_resolve_description_priority(self):
        result = resolve_ticket(
            pr_title="Some change",
            pr_description="Fixing AI-DOC-50",
            branch_name="feature/AI-DOC-60"
        )
        self.assertEqual(result["source"], "PR_DESCRIPTION")

    # -----------------------------
    # 5️⃣ Resolve - Branch Fallback
    # -----------------------------
    def test_resolve_branch_fallback(self):
        result = resolve_ticket(
            pr_title="Some change",
            pr_description="No ticket here",
            branch_name="feature/AI-DOC-70"
        )
        self.assertEqual(result["source"], "BRANCH_NAME")

    # -----------------------------
    # 6️⃣ Resolve - Unlinked Case
    # -----------------------------
    def test_resolve_unlinked(self):
        result = resolve_ticket(
            pr_title="Add login endpoint",
            pr_description="No reference",
            branch_name="feature/new-login"
        )
        self.assertEqual(result["status"], "UNLINKED")


if __name__ == "__main__":
    unittest.main()
