"""Application-level exceptions mapped to HTTP responses."""


class AppError(Exception):
    status_code: int = 500
    detail: str = "An unexpected error occurred"

    def __init__(self, detail: str | None = None) -> None:
        if detail is not None:
            self.detail = detail
        super().__init__(self.detail)


class NotFoundError(AppError):
    status_code = 404


class UnauthorizedError(AppError):
    status_code = 401
    detail = "Not authenticated"


class ForbiddenError(AppError):
    status_code = 403
    detail = "Forbidden"


class BadRequestError(AppError):
    status_code = 400


class ServiceUnavailableError(AppError):
    status_code = 503


class ExternalServiceError(AppError):
    status_code = 502
    detail = "External service request failed"


class AIGenerationError(AppError):
    status_code = 500
    detail = "AI generation failed"


class InvalidOAuthStateError(BadRequestError):
    def __init__(self, detail: str = "Invalid OAuth state parameter") -> None:
        super().__init__(detail=detail)


class OAuthConfigError(ServiceUnavailableError):
    def __init__(
        self,
        detail: str = (
            "Google OAuth is not configured. Set GMAIL_CLIENT_ID and GMAIL_CLIENT_SECRET."
        ),
    ) -> None:
        super().__init__(detail=detail)


class GmailCredentialsMissingError(BadRequestError):
    def __init__(
        self,
        detail: str = "Gmail is not connected. Visit /api/v1/auth/gmail/connect first.",
    ) -> None:
        super().__init__(detail=detail)


class EmailProcessingError(AppError):
    status_code = 500
    detail = "Failed to process email"


# Backward-compatible alias
GmailOAuthConfigError = OAuthConfigError
