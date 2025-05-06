import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

# --- Chemins Django ---
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

# --- Setup Django ---
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "game_portal.settings")
import django
django.setup()

# --- Imports Django Models ---
from gameboxd.models import Game, Platform, Review

# --- Logging ---
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# --- Config ---
load_dotenv()
METACRITIC_URL_TEMPLATE = os.getenv("METACRITIC_URL_TEMPLATE")

# --- Génération des URLs à partir des jeux et de leurs plateformes ---
def generate_urls():
    urls = []
    games = Game.objects.prefetch_related('platforms').all()
    logger.info(f"{games.count()} jeux chargés depuis la base.")
    
    for game in games:
        for platform in game.platforms.all():
            url = METACRITIC_URL_TEMPLATE.format(game=game.slug, platform=platform.slug)
            urls.append({
                "game_id": game.id,
                "platform": platform.name,
                "url": url
            })
    logger.info(f"{len(urls)} URLs générées à partir des jeux et plateformes.")
    return urls

# --- Scraping d'une page d'avis utilisateurs ---
def scrape_reviews(url):
    reviews = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        logger.info(f"Fetching: {url}")
        page.goto(url, wait_until="networkidle")

        html = page.content()
        soup = BeautifulSoup(html, "html.parser")

        review_blocks = soup.select("div.c-review")
        logger.info(f"Nombre de blocs d'avis trouvés sur la page : {len(review_blocks)}")

        for i, block in enumerate(review_blocks, start=1):
            try:
                author = block.select_one(".c-author__name").text.strip()
                content = block.select_one(".c-review__body").text.strip()
                score = block.select_one(".c-review__score").text.strip()
                date = block.select_one(".c-author__date").text.strip()
                reviews.append({
                    "author": author,
                    "content": content,
                    "score": score,
                    "date": date
                })
            except Exception as e:
                logger.warning(f"Review #{i} skipped: {e}")
                continue
        browser.close()
    logger.info(f"Total d'avis extraits pour cette page : {len(reviews)}")
    return reviews

# --- Enregistrement des avis en base ---
def save_reviews(game_id, platform, reviews):
    for review in reviews:
        _, created = Review.objects.update_or_create(
            game_id=game_id,
            platform=platform,
            author=review["author"],
            defaults={
                "score": review["score"],
                "content": review["content"],
                "source": "Metacritic"
            }
        )
        if created:
            logger.info(f"✅ Review créée pour {review['author']} ({platform})")
        else:
            logger.info(f"↻ Review mise à jour pour {review['author']} ({platform})")

# --- Main ---
def main():
    urls = generate_urls()
    for entry in urls:
        try:
            reviews = scrape_reviews(entry["url"])
            save_reviews(entry["game_id"], entry["platform"], reviews)
            logger.info(f"{len(reviews)} reviews enregistrées pour {entry['url']}")
        except Exception as e:
            logger.error(f"Erreur avec {entry['url']} : {e}")

if __name__ == "__main__":
    main()
