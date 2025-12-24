from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.middleware.error_handler import add_exception_handlers
from app.routes import tools, agents, execution, history

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="A multi-tenant backend platform for managing and executing AI Agents.",
    lifespan=lifespan,
)

add_exception_handlers(app)

app.include_router(tools.router, prefix="/api/v1", tags=["Tools"])
app.include_router(agents.router, prefix="/api/v1", tags=["Agents"])
app.include_router(execution.router, prefix="/api/v1", tags=["Execution"])
app.include_router(history.router, prefix="/api/v1", tags=["History"])


@app.get("/health", tags=["Health"])
async def health_check() -> JSONResponse:
    return JSONResponse(
        content={
            "status": "healthy",
            "service": settings.app_name,
            "version": settings.app_version,
        }
    )
