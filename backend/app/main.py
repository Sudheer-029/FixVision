from concurrent.futures import ThreadPoolExecutor

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.jobs import router as jobs_router
from app.jobs.state import IllegalTransition
from app.jobs.steps import Deps


def create_app(deps: Deps | None = None) -> FastAPI:
    app = FastAPI(title="FixVision API", version="0.1.0")
    app.state.deps = deps  # None: built on first request, so importing has no side effects
    # one worker thread: model calls leave the request path and run one at a time
    app.state.worker = ThreadPoolExecutor(max_workers=1, thread_name_prefix="fixvision-worker")
    app.include_router(jobs_router)

    @app.exception_handler(IllegalTransition)
    def illegal_transition(_: Request, exc: IllegalTransition) -> JSONResponse:
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
