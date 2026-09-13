from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from core.engine import get_db
from repository.reseaux import ReseauxRepository
from schema.ReponseAPI import ReponseAPI

router= APIRouter(prefix="/reseaux", tags=["reseaux"])
@router.get("/reseaux",status_code=200)
async def get_reseaux(db:AsyncSession=Depends(get_db)):
    reseaux= await ReseauxRepository(db).get_all_reseaux()
    print(reseaux)
    return ReponseAPI(message="reseaux",success=True,data=reseaux)
