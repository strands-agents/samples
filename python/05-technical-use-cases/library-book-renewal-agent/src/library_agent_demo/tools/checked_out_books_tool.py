"""Tool for retrieving checked out books."""

from typing import Any


class CheckedOutBooksTool:
    """Tool that returns the list of books currently checked out by the user."""

    def get_checked_out_books(self) -> list[dict[str, Any]]:
        """Return static list of checked out books."""
        return [{"book_id": "BOOK-123", "title": "The Great Gatsby"}]
