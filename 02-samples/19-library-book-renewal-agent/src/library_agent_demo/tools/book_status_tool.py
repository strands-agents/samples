"""Book status tool for checking library book availability."""

import re
from typing import Literal, cast

from ..models import BookStatus


class BookStatusTool:
    """Tool for checking the status of library books."""

    def __init__(self, default_status: Literal["ACTIVE", "RECALLED"] = "ACTIVE"):
        """Initialize the book status tool.

        Args:
            default_status: The default status to return for all books.
                          Can be overridden for evaluation scenarios.
        """
        self._default_status = default_status
        self._book_overrides: dict[str, Literal["ACTIVE", "RECALLED"]] = {}

    def get_status(self, book_id: str) -> BookStatus:
        """Get the status of a library book.

        Args:
            book_id: The identifier of the book to check.

        Returns:
            BookStatus object containing the book ID and its status.

        Raises:
            ValueError: If the book_id format is invalid.
        """
        # Validate book_id format: ABC-123 (letters-digits)
        if not re.match(r"^[A-Z]+-\d+$", book_id):
            raise ValueError(f"Book with ID '{book_id}' was not found")

        # Check if there's a specific override for this book
        if book_id in self._book_overrides:
            status = self._book_overrides[book_id]
        else:
            status = self._default_status

        return BookStatus(book_id=book_id, status=cast(Literal["ACTIVE", "RECALLED"], status))

    def set_book_status(self, book_id: str, status: Literal["ACTIVE", "RECALLED"]) -> None:
        """Set the status for a specific book (used for evaluation scenarios).

        Args:
            book_id: The identifier of the book.
            status: The status to set for this book.
        """
        self._book_overrides[book_id] = status

    def set_default_status(self, status: Literal["ACTIVE", "RECALLED"]) -> None:
        """Set the default status for all books (used for evaluation scenarios).

        Args:
            status: The default status to return for books without specific overrides.
        """
        self._default_status = status

    def clear_overrides(self) -> None:
        """Clear all book-specific status overrides."""
        self._book_overrides.clear()
