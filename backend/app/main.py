from fastapi import APIRouter, Depends, FastAPI
from sqlmodel import Session

from app.auth import require_login
from app.db import get_session
from app.routers import auth, metrics, runs, shoes, summary, sync
from app.services.records import compute_records

app = FastAPI(title="Running Tracker", docs_url="/api/docs", openapi_url="/api/openapi.json")

public = APIRouter(prefix="/api")
public.include_router(auth.router)
public.include_router(sync.cron_router())


@public.get("/health")
def health():
    return {"ok": True}


private = APIRouter(prefix="/api", dependencies=[Depends(require_login)])
for module in (runs, shoes, summary, metrics, sync):
    private.include_router(module.router)


@private.get("/records")
def records(session: Session = Depends(get_session)):
    return compute_records(session)


app.include_router(public)
app.include_router(private)
