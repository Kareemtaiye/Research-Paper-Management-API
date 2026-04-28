from fastapi import FastAPI
from app.core.database import lifespan
from app.routers import auth, user, paper, tag
from app.exceptions.handlers import register_exception_handlers

app = FastAPI(lifespan=lifespan)

# cos gastapi wont call the handlers unless thy're registered or imported in this modile
register_exception_handlers(app)

app.include_router(auth.router)
app.include_router(user.router)
app.include_router(paper.router)
app.include_router(tag.router)


@app.get("/", tags=["index"])
def home():
    return "Welcome to the research management api server"
