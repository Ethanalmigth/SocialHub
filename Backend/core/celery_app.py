from celery import Celery

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.setting import settings

engine = create_engine(settings.DATABASE_URL_SYNC)

SessionLocal_sync = sessionmaker(
    engine,
    expire_on_commit=False
)

celery_app = Celery('celery_app',broker="redis://redis:6379/0",backend="redis://redis:6379/0", include=['task.publication'])


celery_app.conf.beat_schedule={
    "verify_task": {
        "task": "task.publication.check_post",
        "schedule": 60
    }
}

# redis://redis:6379/0
#   │      │      │   │
#   │      │      │   └── numéro de la base Redis
#   │      │      └────── port
#   │      └───────────── hostname
#   └──────────────────── protocole
