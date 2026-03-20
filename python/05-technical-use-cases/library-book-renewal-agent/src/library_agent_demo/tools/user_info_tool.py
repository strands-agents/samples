"""User information tool for retrieving library user data."""

from ..models import UserInfo


class UserInfoTool:
    """Tool for retrieving user information from the library system."""

    def __init__(self):
        """Initialize the user info tool with static user data."""
        # Static user information that remains consistent across all calls
        self._user_info = UserInfo(
            name="Alice Johnson",
            account_number="ACC-2024-001",
            library_card_number="LIB-456789",
        )

    def get_user_info(self) -> UserInfo:
        """Get the current user's information.

        Returns:
            UserInfo object containing the user's name, account number,
            and library card number.
        """
        return self._user_info
