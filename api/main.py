import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.database import engine, Base
from api.routes import overview, projects, alerts, analytics, similar, review


@asynccontextmanager
async def lifespan(app: FastAPI):
    db_path = os.path.join(os.path.dirname(__file__), "..", "db", "mplad.db")
    if os.path.exists(db_path):
        Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="MPLAD-SHIELD API",
    description="Risk Intelligence Platform for MPLADS Works",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(overview.router, prefix="/api", tags=["Overview"])
app.include_router(projects.router, prefix="/api", tags=["Projects"])
app.include_router(alerts.router, prefix="/api", tags=["Alerts"])
app.include_router(analytics.router, prefix="/api", tags=["Analytics"])
app.include_router(similar.router, prefix="/api", tags=["Similar"])
app.include_router(review.router, prefix="/api", tags=["Review"])


@app.get("/")
def root():
    return {"name": "MPLAD-SHIELD", "version": "1.0.0", "status": "running"}
