import os
import django
from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException, status, Query
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from datetime import datetime, timedelta
from pydantic import BaseModel
from typing import List, Optional
from api.mistral_summary import generate_summary
from pathlib import Path
import sys

# --- Chemins Django ---
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

# --- Initialisation Django ---
load_dotenv()
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "game_portal.settings")
django.setup()

from django.contrib.auth.models import User
from gameboxd.models import Game, Review

SECRET_KEY = "secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

app = FastAPI(title="GameBoxd API", version="1.0")

# --- Schémas ---
class Token(BaseModel):
    access_token: str
    token_type: str

class GameSchema(BaseModel):
    id: int
    title: str
    slug: Optional[str] = None
    class Config:
        orm_mode = True

class ReviewSchema(BaseModel):
    author: str
    score: str
    content: str
    platform: str
    source: str
    class Config:
        orm_mode = True

# --- Authentification ---
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Token invalide")
        return User.objects.get(username=username)
    except (JWTError, User.DoesNotExist):
        raise HTTPException(status_code=401, detail="Token invalide")

# --- Routes API ---
@app.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    try:
        user = User.objects.get(username=form_data.username)
        if not user.check_password(form_data.password):
            raise HTTPException(status_code=401, detail="Mot de passe incorrect")
    except User.DoesNotExist:
        raise HTTPException(status_code=401, detail="Utilisateur introuvable")

    token = create_access_token(data={"sub": user.username})
    return {"access_token": token, "token_type": "bearer"}

@app.get("/me/")
def get_me(current_user: User = Depends(get_current_user)):
    return {"username": current_user.username}

@app.get("/games/", response_model=List[GameSchema])
def get_games(current_user: User = Depends(get_current_user)):
    return list(Game.objects.all())

@app.get("/games/{game_id}/reviews/", response_model=List[ReviewSchema])
def get_reviews(game_id: int, current_user: User = Depends(get_current_user)):
    reviews = Review.objects.filter(game_id=game_id)
    if not reviews.exists():
        raise HTTPException(status_code=404, detail="Aucune review trouvée")
    return list(reviews)

@app.get("/summary/test/")
def summarize_test_reviews(
    current_user: User = Depends(get_current_user),
    lang: str = Query("en", enum=["en", "fr"])
):
    reviews = [
        "Amazing game! I cannot stop playing.",
        "One of the best characters ever created!",
        "A bit repetitive but still enjoyable."
    ]
    summary = generate_summary(reviews, lang=lang)
    return {"lang": lang, "summary": summary}

@app.get("/summary/{game_id}/")
def summarize_reviews_by_game(
    game_id: int,
    lang: str = Query("fr", enum=["en", "fr"]),
    current_user: User = Depends(get_current_user)
):
    reviews_qs = Review.objects.filter(game_id=game_id)[:5]
    if not reviews_qs.exists():
        raise HTTPException(status_code=404, detail="Aucun avis trouvé pour ce jeu")

    contents = [r.content for r in reviews_qs]
    print(f"Contents: {contents}")
    summary = generate_summary(contents, lang=lang)
    return {
        "game_id": game_id,
        "lang": lang,
        "summary": summary,
        "reviews_count": len(contents)
    }

@app.get("/health", tags=["Monitoring"])
def health_check():
    return {"status": "ok"}
