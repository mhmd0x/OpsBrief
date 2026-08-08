from pathlib import Path

from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from fastapi import FastAPI

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
def health_check() -> dict[str, str]:
    return {"status": "healthy"}