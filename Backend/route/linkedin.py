import datetime
import secrets
import urllib.parse

from fastapi import APIRouter, Query, Depends
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response
import httpx

from core.engine import get_db
from core.exception import CustomException
from core.setting import settings
from repository.user_reseau import UserReseauRepository
from repository.reseaux import ReseauxRepository
from schema import ReponseAPI
from utils.token import controle_access_token

router = APIRouter(tags=["linkedin"])

STATE_COOKIE_KEY = "state"
USER_COOKIE_KEY = "oauth_user_id"


@router.get("/auth/linkedin/oauth")
async def auth(payload=Depends(controle_access_token)):
    state = secrets.token_urlsafe(32)
    user_id = str(payload.get("sub"))

    data = {
        "response_type": "code",
        "redirect_uri": settings.redirect_url,
        "client_id": settings.client_id,
        "state": state,
        "scope": "w_member_social",
    }
    url = f"https://www.linkedin.com/oauth/v2/authorization?{urllib.parse.urlencode(data)}"

    reponse = RedirectResponse(url=url)
    reponse.set_cookie(
        key=STATE_COOKIE_KEY,
        value=state,
        max_age=300,
        httponly=True,
        samesite="lax",
        secure=True,
    )
    reponse.set_cookie(
        key=USER_COOKIE_KEY,
        value=user_id,
        max_age=300,
        httponly=True,
        samesite="lax",
        secure=True,
    )
    return reponse


@router.get("/auth/linkedin/callback")
async def callback(
    request: Request,
    response: Response,
    code: str = Query(...),
    state: str = Query(...),
    db=Depends(get_db),
):
    cookie_state = request.cookies.get(STATE_COOKIE_KEY)
    cookie_user_id = request.cookies.get(USER_COOKIE_KEY)

    if not cookie_state or state != cookie_state:
        raise CustomException(status_code=401, message="State invalide (CSRF suspecté)")
    if not cookie_user_id:
        raise CustomException(status_code=401, message="Session utilisateur introuvable")

    data = {
        "grant_type": "authorization_code",
        "code": code,
        "client_id": settings.client_id,
        "client_secret": settings.client_secret,
        "redirect_uri": settings.redirect_url,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    token_url = "https://www.linkedin.com/oauth/v2/accessToken"

    async with httpx.AsyncClient() as client:
        token_response = await client.post(token_url, data=data, headers=headers)
        if token_response.status_code != 200:
            raise CustomException(status_code=token_response.status_code, message=f"Erreur Token: {token_response.text}")

        data_auth = token_response.json()
        access_token = data_auth["access_token"]

        user_info_url = "https://www.linkedin.com/v2/userinfo"
        user_headers = {"Authorization": f"Bearer {access_token}"}

        user_response = await client.get(user_info_url, headers=user_headers)
        if user_response.status_code != 200:
            raise CustomException(status_code=user_response.status_code, message=f"Erreur UserInfo: {user_response.text}")

        user_data = user_response.json()
        author_urn = f"urn:li:person:{user_data['sub']}"

    expires_in = data_auth.get("expires_in", 3600)
    expires_at = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=expires_in)

    reseaux_repo = ReseauxRepository(db)
    reseau_linkedin = await reseaux_repo.get_by_name("linkedin")
    if not reseau_linkedin:
        raise CustomException(status_code=500, message="Réseau 'linkedin' non configuré en base")

    repo = UserReseauRepository(db)
    await repo.upsert(
        user_id=cookie_user_id,
        reseaux_id=reseau_linkedin.id,
        external_user_id=user_data["sub"],
        author_urn=author_urn,
        access_token=access_token,
        refresh_token=data_auth.get("refresh_token"),
        expires_at=expires_at,
    )

    response.delete_cookie(key=STATE_COOKIE_KEY)
    response.delete_cookie(key=USER_COOKIE_KEY)

    return ReponseAPI(success=True,message="Authorisation linkedin confirmer",data={"author_urn": author_urn, "user": user_data})