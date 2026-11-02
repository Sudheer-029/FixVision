from concurrent.futures import ThreadPoolExecutor

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api import jobs
from app.api.jobs import router as jobs_router
from app.jobs.state import IllegalTransition
from app.jobs.steps import Deps

MULTIPART_OVERHEAD = 1024 * 1024


def create_app(deps: Deps | None = None) -> FastAPI:
    app = FastAPI(title="FixVision API", version="0.1.0")
    app.state.deps = deps  # None: built on first request, so importing has no side effects
    # one worker thread: model calls leave the request path and run one at a time
    app.state.worker = ThreadPoolExecutor(max_workers=1, thread_name_prefix="fixvision-worker")
    app.include_router(jobs_router)

    @app.middleware("http")
    async def limit_upload(request: Request, call_next):
        # FastAPI parses multipart before the route runs; the server enforces Content-Length
        if request.url.path.endswith("/media"):
            length = request.headers.get("content-length")
            if length is None or not length.isdigit():
                return JSONResponse(status_code=411, content={"detail": "Content-Length required"})
            if int(length) > jobs.MAX_UPLOAD_BYTES + MULTIPART_OVERHEAD:
                return JSONResponse(status_code=413, content={"detail": "file too large"})
        return await call_next(request)

    @app.exception_handler(IllegalTransition)
    def illegal_transition(_: Request, exc: IllegalTransition) -> JSONResponse:
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
