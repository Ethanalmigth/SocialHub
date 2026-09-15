from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from core.engine import get_db
from repository.reseaux import ReseauxRepository
from repository.user_reseau import UserReseauRepository
from schema.ReponseAPI import ReponseAPI
from utils.token import controle_access_token

router = APIRouter(prefix="/reseaux", tags=["reseaux"])


@router.get("/reseaux", status_code=200)
async def get_reseaux(db: AsyncSession = Depends(get_db)):
    reseaux = await ReseauxRepository(db).get_all_reseaux()
    print(reseaux)
    return ReponseAPI(message="reseaux", success=True, data=reseaux)


@router.get("/status", status_code=200)
async def get_reseaux_status(
    payload=Depends(controle_access_token),
    db: AsyncSession = Depends(get_db),
):
    user_id = payload.get("id")

    reseaux_repo = ReseauxRepository(db)
    all_reseaux = await reseaux_repo.get_all_reseaux()  # [{"id":.., "name":..}, ...]

    user_repo = UserReseauRepository(db)
    connected_names = await user_repo.get_connected_reseaux_names(user_id)

    status = {r["name"]: (r["name"] in connected_names) for r in all_reseaux}
    return ReponseAPI(message="statut des connexions", success=True, data=status)