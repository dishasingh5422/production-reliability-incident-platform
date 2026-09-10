import logging
import time
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from starlette.middleware.base import RequestResponseEndpoint
from starlette.responses import Response

from app.api.routes import router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.base import Base, engine
from app.monitoring.metrics import BUILD_INFO, ERROR_COUNT, REQUEST_COUNT, REQUEST_LATENCY

configure_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    Base.metadata.create_all(bind=engine)
    BUILD_INFO.labels(version=settings.app_version, environment=settings.app_env).set(1)
    logger.info(
        "application started",
        extra={"context": {"service": settings.app_name, "version": settings.app_version}},
    )
    yield
    logger.info("application stopped")


app = FastAPI(
    title="Production Reliability & Incident Automation Platform",
    version=get_settings().app_version,
    lifespan=lifespan,
)


@app.middleware("http")
async def operational_metrics(request: Request, call_next: RequestResponseEndpoint) -> Response:
    started = time.perf_counter()
    request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
    path = request.url.path
    try:
        response = await call_next(request)
    except Exception:
        ERROR_COUNT.labels(path=path).inc()
        logger.exception("unhandled request error", extra={"context": {"request_id": request_id}})
        raise
    elapsed = time.perf_counter() - started
    REQUEST_COUNT.labels(method=request.method, path=path, status=str(response.status_code)).inc()
    REQUEST_LATENCY.labels(method=request.method, path=path).observe(elapsed)
    if response.status_code >= 500:
        ERROR_COUNT.labels(path=path).inc()
    response.headers["x-request-id"] = request_id
    return response


app.include_router(router)
