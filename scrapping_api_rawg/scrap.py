
import os
import sys
import django
import requests
import logging
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

#  Chemin du projet 
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

# Configuration Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "game_portal.settings")
django.setup()

from gameboxd.models import Game, Platform, Genre, Developer, Publisher, Screenshot, Rating

# Variables d'environnement
API_KEY = os.getenv('API_KEY')
BASE_URL = os.getenv('BASE_URL')
MAX_REQUESTS = int(os.getenv('MAX_REQUESTS'))
RESULTS_PER_PAGE = int(os.getenv('RESULTS_PER_PAGE'))
PROGRESS_FILE = os.getenv('PROGRESS_FILE')

# Configuration du logging
logging.basicConfig(
    filename="game_import.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def fetch_games(page):
    """ Récupère une page de données de l'API RAWG """
    params = {
        'key': API_KEY,
        'page': page,
        'page_size': RESULTS_PER_PAGE,
        'metacritic': "60,80"
    }
    try:
        response = requests.get(BASE_URL, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Erreur lors de la requête API (page {page}): {e}")
        return None

def save_to_db(games):
    """ Enregistre toutes les données des jeux et leurs relations associées. """
    for game in games:
        try:
            # Sauvegarde du jeu principal
            game_instance, created = Game.objects.update_or_create(
                id=game['id'],
                defaults={
                    'title': game['name'],
                    'slug': game.get('slug', None),
                    'release_date': game.get('released', None),
                    'rating': game.get('rating', None),
                    'ratings_count': game.get('ratings_count', None),
                    'metacritic': game.get('metacritic', None),
                    'playtime': game.get('playtime', None),
                    'website': game.get('website', None),
                    'background_image': game.get('background_image', None),
                    'reddit_url': game.get('reddit_url', None),
                    'added_by_status': game.get('added_by_status', None),
                }
            )

            # Sauvegarde des plateformes
            for platform_data in game.get('platforms', []):
                platform, _ = Platform.objects.update_or_create(
                    id=platform_data['platform']['id'],
                    defaults={'name': platform_data['platform']['name'], 'slug': platform_data['platform']['slug']}
                )
                game_instance.platforms.add(platform)

            # Sauvegarde des genres
            for genre in game.get('genres', []):
                genre_obj, _ = Genre.objects.update_or_create(
                    id=genre['id'],
                    defaults={'name': genre['name'], 'slug': genre['slug']}
                )
                game_instance.genres.add(genre_obj)

            # Sauvegarde des développeurs
            for dev in game.get('developers', []):
                developer, _ = Developer.objects.update_or_create(
                    id=dev['id'],
                    defaults={'name': dev['name']}
                )
                game_instance.developers.add(developer)

            # Sauvegarde des éditeurs
            for pub in game.get('publishers', []):
                publisher, _ = Publisher.objects.update_or_create(
                    id=pub['id'],
                    defaults={'name': pub['name']}
                )
                game_instance.publishers.add(publisher)

            # Sauvegarde des captures d’écran
            for screenshot in game.get('short_screenshots', []):
                Screenshot.objects.update_or_create(
                    game=game_instance,
                    image=screenshot['image']
                )

            # Sauvegarde des évaluations
            for rating in game.get('ratings', []):
                Rating.objects.update_or_create(
                    game=game_instance,
                    title=rating['title'],
                    defaults={
                        'count': rating['count'],
                        'percent': rating['percent'],
                    }
                )

            logging.info(f"Jeu '{game['name']}' {'ajouté' if created else 'mis à jour'} avec succès.")

        except Exception as e:
            logging.error(f"Erreur lors de l'ajout du jeu '{game['name']}': {e}")

def save_progress(page, filename):
    """ Enregistre la progression dans un fichier. """
    try:
        with open(filename, 'w') as f:
            f.write(str(page))
    except Exception as e:
        logging.error(f"Erreur lors de l'enregistrement de la progression: {e}")

def load_progress(filename):
    """ Charge la progression depuis un fichier. """
    if os.path.exists(filename):
        try:
            with open(filename, 'r') as f:
                page = f.read().strip()
                return int(page)
        except ValueError:
            logging.warning("Fichier de progression corrompu, redémarrage depuis la page 1.")
            return 1
    return 1

def main():
    page = load_progress(PROGRESS_FILE)
    while page <= MAX_REQUESTS:
        logging.info(f"Récupération de la page {page}")
        data = fetch_games(page)

        if data and 'results' in data:
            save_to_db(data['results'])
            save_progress(page, PROGRESS_FILE)
            page += 1
        else:
            logging.warning(f"Aucune donnée trouvée ou erreur rencontrée à la page {page}.")
            break

if __name__ == "__main__":
    main()
