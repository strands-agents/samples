"""Adapted from τ-bench https://arxiv.org/abs/2406.12045"""

from mabench.environments.base import Env
from mabench.environments.retail.data import load_data
from typing import Dict, List, Optional, Union, Any, Callable
from mabench.environments.user import UserStrategy


def get_user_profile(user_id: str) -> Dict[str, Any]:
    """Get a user's financial profile information.

    Args:
        user_id: User's account ID

    Returns:
        User profile including account types, investment preferences, risk tolerance, and goals
    """
    pass


def get_account_summary(user_id: str) -> Dict[str, Any]:
    """Get summary of a user's accounts and balances.

    Args:
        user_id: User's account ID

    Returns:
        Summary of all accounts including type, balance, and performance
    """
    pass


def get_account_transactions(
    account_id: str, start_date: str = None, end_date: str = None
) -> List[Dict[str, Any]]:
    """Get transactions for a specific account within a date range.

    Args:
        account_id: Account ID
        start_date: Start date in YYYY-MM-DD format (default: 30 days ago)
        end_date: End date in YYYY-MM-DD format (default: today)

    Returns:
        List of transactions with date, amount, category, and description
    """
    pass


def get_investment_portfolio(user_id: str) -> Dict[str, Any]:
    """Get a user's investment portfolio details.

    Args:
        user_id: User's account ID

    Returns:
        Portfolio details including asset allocation, holdings, and performance
    """
    pass


def get_investment_recommendations(
    user_id: str, risk_level: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Get personalized investment recommendations.

    Args:
        user_id: User's account ID
        risk_level: Optional risk level override (conservative, moderate, aggressive)

    Returns:
        List of recommended investments with rationale
    """
    pass


def create_investment_plan(
    user_id: str, goal_name: str, target_amount: float, time_horizon: int
) -> Dict[str, Any]:
    """Create a new investment plan for a specific financial goal.

    Args:
        user_id: User's account ID
        goal_name: Name of the financial goal
        target_amount: Target amount to reach
        time_horizon: Time horizon in years

    Returns:
        Created investment plan details
    """
    pass


def check_retirement_readiness(
    user_id: str, retirement_age: Optional[int] = None
) -> Dict[str, Any]:
    """Check retirement readiness based on current savings and contributions.

    Args:
        user_id: User's account ID
        retirement_age: Optional retirement age (default: from user profile)

    Returns:
        Retirement readiness assessment and recommendations
    """
    pass


def analyze_cash_flow(user_id: str, months: int = 3) -> Dict[str, Any]:
    """Analyze income and expenses to provide cash flow insights.

    Args:
        user_id: User's account ID
        months: Number of months to analyze (default: 3)

    Returns:
        Cash flow analysis with income, expenses, and recommendations
    """
    pass


def get_budget_categories(user_id: str) -> List[Dict[str, Any]]:
    """Get a user's budget categories and limits.

    Args:
        user_id: User's account ID

    Returns:
        List of budget categories with spending limits and current usage
    """
    pass


def update_budget_category(
    user_id: str, category_id: str, monthly_limit: float
) -> Dict[str, Any]:
    """Update a budget category's monthly spending limit.

    Args:
        user_id: User's account ID
        category_id: Budget category ID
        monthly_limit: New monthly spending limit

    Returns:
        Updated budget category details
    """
    pass


def get_financial_goals(user_id: str) -> List[Dict[str, Any]]:
    """Get a user's financial goals.

    Args:
        user_id: User's account ID

    Returns:
        List of financial goals with progress and timeline
    """
    pass


def create_financial_goal(
    user_id: str, goal_name: str, target_amount: float, target_date: str
) -> Dict[str, Any]:
    """Create a new financial goal.

    Args:
        user_id: User's account ID
        goal_name: Name of the goal
        target_amount: Target amount to reach
        target_date: Target date in YYYY-MM-DD format

    Returns:
        Created financial goal details
    """
    pass


def calculate_loan_payment(
    loan_amount: float, interest_rate: float, term_years: int
) -> Dict[str, Any]:
    """Calculate loan payment amounts and amortization schedule.

    Args:
        loan_amount: Loan principal amount
        interest_rate: Annual interest rate (percentage)
        term_years: Loan term in years

    Returns:
        Monthly payment amount and amortization details
    """
    pass


def get_debt_payoff_strategy(
    user_id: str, strategy: str = "avalanche"
) -> Dict[str, Any]:
    """Get a debt payoff strategy based on user's current debts.

    Args:
        user_id: User's account ID
        strategy: Payoff strategy, either "avalanche" (highest interest first) or "snowball" (smallest balance first)

    Returns:
        Debt payoff plan with ordered list of debts and timeline
    """
    pass


def get_tax_summary(user_id: str, tax_year: Optional[int] = None) -> Dict[str, Any]:
    """Get a summary of tax information for a specific year.

    Args:
        user_id: User's account ID
        tax_year: Tax year (default: current year)

    Returns:
        Tax summary including income, deductions, and estimated tax liability
    """
    pass


def update_risk_profile(user_id: str, risk_tolerance: str) -> Dict[str, Any]:
    """Update a user's risk tolerance profile.

    Args:
        user_id: User's account ID
        risk_tolerance: Risk tolerance level (conservative, moderate, aggressive)

    Returns:
        Updated risk profile details
    """
    pass


def get_market_outlook() -> Dict[str, Any]:
    """Get current market outlook and economic indicators.

    Returns:
        Market analysis and key economic indicators
    """
    pass


def get_education_resources(topic: str) -> List[Dict[str, Any]]:
    """Get educational resources on financial topics.

    Args:
        topic: Financial topic (e.g., retirement, investing, budgeting)

    Returns:
        List of educational resources with titles and descriptions
    """
    pass


def schedule_advisor_meeting(
    user_id: str, preferred_date: str, preferred_time: str
) -> Dict[str, Any]:
    """Schedule a meeting with a human financial advisor.

    Args:
        user_id: User's account ID
        preferred_date: Preferred date in YYYY-MM-DD format
        preferred_time: Preferred time in HH:MM format

    Returns:
        Scheduled meeting details
    """
    pass


def transfer_to_human_advisor() -> Dict[str, str]:
    """Transfer the conversation to a human financial advisor.

    Returns:
        Status message of the transfer
    """
    pass


ALL_TOOLS = [
    get_user_profile,
    get_account_summary,
    get_account_transactions,
    get_investment_portfolio,
    get_investment_recommendations,
    create_investment_plan,
    check_retirement_readiness,
    analyze_cash_flow,
    get_budget_categories,
    update_budget_category,
    get_financial_goals,
    create_financial_goal,
    calculate_loan_payment,
    get_debt_payoff_strategy,
    get_tax_summary,
    update_risk_profile,
    get_market_outlook,
    get_education_resources,
    schedule_advisor_meeting,
    transfer_to_human_advisor,
]

WIKI = """
# Financial Advisor AI Policy

The current time is 2025-03-24 23:00:00 PST.

As a Financial Advisor AI, you can help users manage their finances, investments, budgets, and financial goals.

- Before taking any actions that modify a user's financial data (creating goals, updating risk profiles, scheduling meetings), you must list the action details and obtain explicit user confirmation (yes) to proceed.

- You should not provide any information, knowledge, or procedures not provided by the user or available tools, or give subjective recommendations or comments about specific investments, stocks, or market timing that could constitute financial advice.

- You should only make one tool call at a time, and if you make a tool call, you should not respond to the user simultaneously. If you respond to the user, you should not make a tool call at the same time.

- You should deny user requests that are against this policy.

- You should transfer the user to a human financial advisor if and only if the request cannot be handled within the scope of your actions or requires personalized financial advice that would exceed your capabilities.

## Domain Basic

- Each user has a profile containing user ID, name, date of birth, contact information, risk tolerance, investment preferences, and financial goals.

- Each user may have multiple accounts (checking, savings, investment, retirement, etc.) with associated balances, transaction histories, and performance metrics.

- Investment portfolios contain asset allocations (stocks, bonds, cash, alternatives), individual holdings, and performance history.

- Financial goals are defined with target amounts, target dates, and associated investment plans.

## Financial Analysis

- The advisor must first confirm the user's ID before providing any account information or analysis.

- Cash flow analysis examines income and expenses over time to identify patterns and opportunities for improvement.

- Retirement readiness assessment considers current savings, contribution rates, expected returns, and retirement age to project retirement income.

- Debt analysis provides strategies for debt reduction (avalanche or snowball method) and consolidation opportunities.

## Investment Management

- Investment recommendations must be aligned with the user's risk tolerance (conservative, moderate, aggressive) and financial goals.

- Portfolio analysis examines current asset allocation, diversification, performance, and fee structure.

- Market outlooks provide general economic context but should not be presented as timing recommendations or specific investment picks.

- Risk profile updates require explicit confirmation from the user and should be accompanied by an explanation of the implications.

## Financial Planning

- Financial goals should be SMART (Specific, Measurable, Achievable, Relevant, Time-bound) and include details on funding strategies.

- Budgeting tools help users track spending by category and set appropriate limits based on income and financial goals.

- Tax planning provides general information about tax-advantaged accounts and strategies but not specific tax advice.

- Education planning helps users save for education expenses through appropriate account types and investment strategies.

## Educational Resources

- The advisor can provide educational resources on various financial topics to help users improve their financial literacy.

- Topics include investing basics, retirement planning, debt management, budgeting, tax strategies, and insurance.

- Resources should be factual and educational, not promotional or biased toward specific products.

## Privacy and Security

- The advisor must protect user financial information and only discuss account details after verifying the user's identity.

- Sensitive information like account numbers should not be fully displayed in messages.

- The advisor should not ask for security credentials, PINs, or passwords under any circumstances.

- For security reasons, certain actions may require additional verification through other channels.
"""

RULES = [
    "You are a Financial Advisor AI assistant. You are chatting with a user, and you can call tools or respond to the user.",
    "The advisor should always first confirm the user ID before proceeding with any personalized task.",
    "The advisor should not proceed with any task if the user ID is not found.",
    "For any changes to the user's financial data, e.g., goal creation, risk profile updates, or budget modifications, the advisor must confirm the details with the user and ask for permission, and get explicit authorization (yes) to proceed.",
    "The advisor should solve the user task given the tools, without transferring to a human financial advisor unless absolutely necessary.",
    "The advisor should not make up any information or knowledge about financial products, market performance, or regulations not provided from the user or the tools.",
    "The advisor should at most make one tool call at a time, and if the advisor makes a tool call, it does not respond to the user at the same time.",
    "The advisor should never make specific investment recommendations for individual securities, funds, or market timing.",
    "The advisor should always clarify that its information is educational and not personalized financial advice.",
    "The advisor should prioritize user privacy and security, never asking for credentials or sensitive account details.",
]


class MockFinancialAdvisorEnv(Env):
    name: str = "financialadvisor"

    def __init__(
        self,
        user_strategy: Union[str, UserStrategy] = UserStrategy.LLM,
        user_model: str = "gpt-4o",
        user_provider: Optional[str] = None,
        task_split: str = "test",
        task_index: Optional[int] = None,
        **kwargs: Any,
    ):
        super().__init__(
            data_load_func=load_data,
            tools=ALL_TOOLS,
            tasks=[],
            wiki=WIKI,
            rules=RULES,
            user_strategy=user_strategy,
            user_model=user_model,
            user_provider=user_provider,
            task_index=task_index,
            **kwargs,
        )
        self.terminate_tools = ["transfer_to_human_advisor"]

    @property
    def tools_info(self) -> Dict[str, Dict[str, Callable]]:
        return {self.name: self.tools_map}
