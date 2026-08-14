from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db
from app.routers.assets import router as assets_router
from app.routers.briefs import router as briefs_router
from app.routers.insights import router as insights_router
from app.routers.work_orders import router as work_orders_router

STATIC_DIRECTORY = Path(__file__).parent / "static"

app = FastAPI(
    title="OpsBrief API",
    description="Decision-support API for maintenance operations.",
    version="0.1.0",
)

app.mount(
    "/static",
    StaticFiles(directory=STATIC_DIRECTORY),
    name="static",
)

app.include_router(assets_router)
app.include_router(work_orders_router)
app.include_router(insights_router)
app.include_router(briefs_router)


@app.get("/", include_in_schema=False)
def dashboard() -> FileResponse:
    return FileResponse(STATIC_DIRECTORY / "index.html")


@app.get("/health", tags=["Health"])
def health_check(
    database: Session = Depends(get_db),
) -> dict[str, str]:
    try:
        database.execute(text("SELECT 1"))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable",
        )

    return {"status": "healthy"}