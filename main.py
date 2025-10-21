from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

try:
    # If running from inside test_app directory: uvicorn main:app --reload
    from app.database import Base, engine
    from app.routes import public as public_routes
    from app.routes import admin as admin_routes
    from app.routes import orders as orders_routes
except ImportError:
    # If running from project root: uvicorn test_app.main:app --reload
    from test_app.app.database import Base, engine
    from test_app.app.routes import public as public_routes
    from test_app.app.routes import admin as admin_routes
    from test_app.app.routes import orders as orders_routes

app = FastAPI()

# Mount static using absolute path to ensure uploads are served in any CWD
STATIC_DIR = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory="templates")

# Create DB tables
Base.metadata.create_all(bind=engine)

# CORS for Telegram Mini App and local dev
origins = [
    "https://t.me",
    "https://web.telegram.org",
    "http://localhost",
    "http://127.0.0.1",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(public_routes.router)
app.include_router(admin_routes.router)
app.include_router(orders_routes.router)

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/health")
def health_check():
    return {"status": "ok"}
