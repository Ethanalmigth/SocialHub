# routes/linkedin.py
from fastapi import APIRouter, Depends, Query, logger
from starlette.requests import Request
from starlette.responses import Response

from core.engine import get_db
from repository.reseaux import ReseauxRepository
from repository.user_reseau import UserReseauRepository
from service.linkedin_publisher import LinkedInPublisher
from utils.token import controle_access_token

router = APIRouter(prefix="/linkedin", tags=["linkedin"])


@router.get("/auth")
async def linkedin_auth(payload=Depends(controle_access_token)):
    publisher = LinkedInPublisher(user_reseau=None, db=None)
    return await publisher.auth(payload=payload)


@router.get("/callback")
async def linkedin_callback(
    request: Request,
    code: str | None = Query(None),
    state: str | None = Query(None),
    error: str | None = Query(None),
    error_description: str | None = Query(None),
    db=Depends(get_db),
):
    if error:
        logger.error("LinkedIn callback error: %s - %s", error, error_description)
        return LinkedInPublisher._redirect_with_error("linkedin")

    if not code or not state:
        logger.error("LinkedIn callback: code ou state manquant")
        return LinkedInPublisher._redirect_with_error("linkedin")

    publisher = LinkedInPublisher(user_reseau=None, db=db)
    return await publisher.callback(request=request, code=code, state=state, db=db)

@router.get("/reseaux/status")
async def get_reseaux_status(
    payload=Depends(controle_access_token),
    db=Depends(get_db),
):
    user_id = payload.get("id")

    reseaux_repo = ReseauxRepository(db)
    all_reseaux = await reseaux_repo.get_all_reseaux()

    user_repo = UserReseauRepository(db)
    connected_names = await user_repo.get_connected_reseaux_names(user_id)

    return {r["name"]: (r["name"] in connected_names) for r in all_reseaux}

