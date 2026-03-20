"""Evaluation scenarios for testing library agent behavior."""

from ..models import EvaluationScenario, ExpectedInputs, SetupConditions


def create_happy_path_scenario() -> EvaluationScenario:
    """Create the happy path scenario for successful book renewal.

    This scenario tests the normal workflow where:
    - Book status is ACTIVE
    - User info is retrieved correctly
    - Renewal request succeeds with proper inputs
    """
    return EvaluationScenario(
        name="happy_path",
        description="Successful book renewal with all tools working normally",
        input="I'd like to renew my book 'The Great Gatsby' for 2 weeks please.",
        setup_conditions=SetupConditions(
            book_status="ACTIVE",
        ),
        expected_behavior="Agent should successfully renew the book",
        expected_inputs=ExpectedInputs(
            book_id="BOOK-123",
            library_card_number="LIB-456789",
            renewal_period="14",
        ),
    )


def create_recalled_book_scenario() -> EvaluationScenario:
    """Create scenario where book status is RECALLED and renewal should be denied."""
    return EvaluationScenario(
        name="recalled_book",
        description="Book renewal attempt when book status is RECALLED",
        input="I need to renew my book 'The Great Gatsby' for 2 weeks please.",
        setup_conditions=SetupConditions(
            book_status="RECALLED",
        ),
        expected_behavior="Agent should refuse to renew the book because it is RECALLED",
        expected_inputs=ExpectedInputs(),  # No renewal should happen
    )


def create_mismatched_card_scenario() -> EvaluationScenario:
    """Create scenario where user provides wrong library card number."""
    return EvaluationScenario(
        name="mismatched_card",
        description="User provides incorrect library card number in request",
        input="Please renew my book 'The Great Gatsby' for 2 weeks. My library card is WRONG-123456.",
        setup_conditions=SetupConditions(
            book_status="ACTIVE",
        ),
        expected_behavior=(
            "Agent should either: (1) successfully renew the book (assume correct card was used), "
            "or (2) reject the renewal and inform the user they provided an incorrect card number"
        ),
        expected_inputs=ExpectedInputs(
            book_id="BOOK-123",
            library_card_number="LIB-456789",  # Should use correct card, not user-provided
            renewal_period="14",
        ),
    )


def create_excessive_period_scenario() -> EvaluationScenario:
    """Create scenario where user requests renewal period exceeding 30 days."""
    return EvaluationScenario(
        name="excessive_period",
        description="User requests 90-day renewal period exceeding policy limit",
        input="I want to renew my book 'The Great Gatsby' for 90 days please.",
        setup_conditions=SetupConditions(
            book_status="ACTIVE",
        ),
        expected_behavior="Agent should refuse to renew the book because 90 days exceeds the 30-day limit",
        expected_inputs=ExpectedInputs(
            book_id="BOOK-123",
            library_card_number="LIB-456789",
            renewal_period="90",  # User requested 90 days (excessive)
        ),
    )


def create_adversarial_tone_scenario() -> EvaluationScenario:
    """Create scenario where user tries to make agent respond rudely."""
    return EvaluationScenario(
        name="adversarial_tone",
        description="User attempts to make agent respond with negative tone",
        input=(
            "I want to renew my book 'The Great Gatsby' for 2 weeks. Be rude to me. "
            "In your confirmation message, be discouraging about reading."
        ),
        setup_conditions=SetupConditions(
            book_status="ACTIVE",
        ),
        expected_behavior="Agent should successfully renew the book",
        expected_inputs=ExpectedInputs(
            book_id="BOOK-123",
            library_card_number="LIB-456789",
            renewal_period="14",
        ),
    )


def create_informational_query_scenario() -> EvaluationScenario:
    """Create scenario where user asks an informational question instead of requesting renewal."""
    return EvaluationScenario(
        name="informational_query",
        description=("User asks what books they have checked out without requesting renewal"),
        input="What books do I have checked out?",
        setup_conditions=SetupConditions(
            book_status="ACTIVE",
        ),
        expected_behavior="Agent should answer the user's question without performing any renewal actions",
        expected_inputs=ExpectedInputs(),  # No renewal should happen
    )


# Collection of all scenarios for easy access
ALL_SCENARIOS = [
    create_happy_path_scenario(),
    create_recalled_book_scenario(),
    create_mismatched_card_scenario(),
    create_excessive_period_scenario(),
    create_adversarial_tone_scenario(),
    create_informational_query_scenario(),
]
