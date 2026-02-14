"""Rescue Command Center - FastAPI Backend."""

import logging
import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Log to console and file (backend/logs/app.log)
LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "app.log"
LOG_FMT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
logging.basicConfig(
    level=logging.INFO,
    format=LOG_FMT,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
    ],
)

from app.routers import mavic, tiago, supervisor, mission, trigger

app = FastAPI(
    title="Rescue Command Center API",
    description="API for controlling Mavic drone and Tiago robot in rescue operations",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(mavic.router)
app.include_router(tiago.router)
app.include_router(supervisor.router)
app.include_router(mission.router)
app.include_router(trigger.router)


@app.get("/")
def root():
    return {"message": "Rescue Command Center API", "docs": "/docs"}


@app.get("/health")
def health():
    return {"status": "ok"}
