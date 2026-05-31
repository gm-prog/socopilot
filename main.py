"""SOCoPilot FastAPI application entrypoint."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="SOCoPilot",
        version="0.2.0",
        description="SOC Pipeline Backend",
    )

    # CORS (frontend support)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # API routes
    app.include_router(api_router, prefix="/api/v1")

    @app.get("/")
    def root():
        return {"status": "running"}

    return app


app = create_app()