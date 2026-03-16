class PrimaryAPIError(Exception):
    """Error returned by the Primary API."""

    def __init__(self, status: str, description: str | None = None, message: str | None = None):
        self.status = status
        self.description = description
        self.api_message = message
        detail = description or message or status
        super().__init__(detail)


class AuthenticationError(PrimaryAPIError):
    """Failed to authenticate against the Primary API."""
