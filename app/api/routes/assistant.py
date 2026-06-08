from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.assistant import NextActionsResponse
from app.schemas.job_match import MatchJobRequest, MatchJobResponse
from app.schemas.reply_draft import DraftReplyRequest, DraftReplyResponse
from app.services.job_match_service import JobMatchService
from app.services.next_action_service import NextActionService
from app.services.reply_draft_service import ReplyDraftService

router = APIRouter(prefix="/assistant", tags=["assistant"])


@router.get("/next-actions", response_model=NextActionsResponse)
async def get_next_actions(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NextActionsResponse:
    service = NextActionService()
    return await service.get_next_actions(session, current_user.id)


@router.post("/draft-reply", response_model=DraftReplyResponse)
async def draft_reply(
    payload: DraftReplyRequest,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DraftReplyResponse:
    service = ReplyDraftService()
    return await service.create_draft(session, user_id=current_user.id, request=payload)


@router.post("/match-job", response_model=MatchJobResponse)
async def match_job(
    payload: MatchJobRequest,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MatchJobResponse:
    service = JobMatchService()
    return await service.match_job(session, user_id=current_user.id, request=payload)
