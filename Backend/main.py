from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError
from model import *
from core.engine import Base,Engine
from core.exception import CustomException
from core.handler import Custom_exception_handler, Validation_exception_handler, Generic_exception_handler,  Integrity_error_handler
from route.user import router as UserRouter
from route.publication import router as PublicationRouter
from route.post import router as PostRouter

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with Engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield



app = FastAPI(lifespan=lifespan)


app.include_router(UserRouter)
app.include_router(PublicationRouter)
app.include_router(PostRouter)
app.add_exception_handler(CustomException,Custom_exception_handler)
app.add_exception_handler(RequestValidationError,Validation_exception_handler)
app.add_exception_handler(IntegrityError,Integrity_error_handler)
app.add_exception_handler(Exception,Generic_exception_handler)
@app.get("/")
async def read_root():
    print("Connection fait")

    """@app.get("/db-test")
    async def test_db(db: AsyncSession = Depends(get_db)):
        return {"status": "DB connected"}
    """
