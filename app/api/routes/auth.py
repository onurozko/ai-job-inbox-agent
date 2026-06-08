from fastapi import APIRouter, Depends, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.auth import GmailConnectResponse, LogoutResponse, TokenResponse, UserRead
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/google/login")
async def google_login() -> RedirectResponse:
    service = AuthService()
    authorization_url = await service.get_google_login_url()
    return RedirectResponse(url=authorization_url)


@router.get("/google/callback", response_model=None)
async def google_callback(
    code: str = Query(...),
    state: str = Query(...),
    response_format: str = Query(default="redirect"),
    session: AsyncSession = Depends(get_db),
) -> RedirectResponse | TokenResponse:
    service = AuthService()
    access_token, user = await service.complete_google_login(session, code=code, state=state)

    if response_format == "json":
        return TokenResponse(access_token=access_token, user=user)

    redirect_url = service.build_login_redirect_url(access_token)
    return RedirectResponse(url=redirect_url)


@router.post("/logout", response_model=LogoutResponse)
async def logout(_current_user: User = Depends(get_current_user)) -> LogoutResponse:
    return LogoutResponse(message="Logged out successfully")


@router.get("/me", response_model=UserRead)
async def get_me(current_user: User = Depends(get_current_user)) -> UserRead:
    return UserRead.model_validate(current_user)


@router.get("/gmail/connect")
async def gmail_connect(current_user: User = Depends(get_current_user)) -> RedirectResponse:
    service = AuthService()
    authorization_url = await service.get_gmail_connect_url(user_id=current_user.id)
    return RedirectResponse(url=authorization_url)


@router.get("/gmail/callback", response_model=GmailConnectResponse)
async def gmail_callback(
    code: str = Query(...),
    state: str = Query(...),
    session: AsyncSession = Depends(get_db),
) -> GmailConnectResponse:
    service = AuthService()
    return await service.complete_gmail_connect(session, code=code, state=state)
