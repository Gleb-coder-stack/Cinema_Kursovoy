from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import uuid
import logging
from database import db

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="WebCinema")

# Добавляем CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Настройка шаблонов и статики
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Сессии (простое хранилище в памяти)
sessions = {}

# Вспомогательные функции
def get_current_user(request: Request):
    session_id = request.cookies.get("session_id")
    if session_id and session_id in sessions:
        return sessions[session_id]
    return None

# API endpoints
@app.get("/api/movies")
async def get_movies():
    try:
        movies = db.get_movies()
        logger.info(f"API /api/movies: возвращено {len(movies)} фильмов")
        return movies
    except Exception as e:
        logger.error(f"Ошибка в /api/movies: {e}")
        return []

@app.get("/api/sessions")
async def get_sessions():
    try:
        sessions_data = db.get_sessions()
        logger.info(f"API /api/sessions: возвращено {len(sessions_data)} сеансов")
        return sessions_data
    except Exception as e:
        logger.error(f"Ошибка в /api/sessions: {e}")
        return []

# Страницы
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/schedule", response_class=HTMLResponse)
async def schedule(request: Request):
    return templates.TemplateResponse("schedule.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

# Запуск
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=["templates", "static"]
    )