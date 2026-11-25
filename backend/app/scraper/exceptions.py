"""
Scraper Subsystem Exception Definitions.
"""


class AuthenticationRequiredError(Exception):
    """Raised when extraction is initiated without a valid authenticated browser session."""
    pass
