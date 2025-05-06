import logging
import requests
import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

API_KEY = os.getenv('API_KEY')
BASE_URL = os.getenv('BASE_URL')

def save_to_db(games):
    """
    Sauvegarde les jeux dans la base de données.

    Args:
        games (list): Liste de jeux récupérés depuis l'API.

    Returns:
        int: Nombre de jeux ajoutés ou mis à jour.
    """
    from .models import Game, Platform, Genre, Developer, Publisher, Screenshot, Rating
    count = 0
    for game in games:
        try:
            # Sauvegarde du jeu principal
            game_instance, created = Game.objects.update_or_create(
                id=game["id"],
                defaults={
                    "title": game["name"],
                    "slug": game.get("slug", None),
                    "release_date": game.get("released", None),
                    "rating": game.get("rating", None),
                    "ratings_count": game.get("ratings_count", None),
                    "metacritic": game.get("metacritic", None),
                    "playtime": game.get("playtime", None),
                    "website": game.get("website", None),
                    "background_image": game.get("background_image", None),
                    "reddit_url": game.get("reddit_url", None),
                    "added_by_status": game.get("added_by_status", None),
                }
            )

            # Sauvegarde des plateformes
            for platform_data in game.get("platforms", []):
                platform = platform_data["platform"]
                platform_instance, _ = Platform.objects.update_or_create(
                    id=platform["id"],
                    defaults={"name": platform["name"], "slug": platform["slug"]}
                )
                game_instance.platforms.add(platform_instance)

            # Sauvegarde des genres
            for genre in game.get("genres", []):
                genre_instance, _ = Genre.objects.update_or_create(
                    id=genre["id"],
                    defaults={"name": genre["name"], "slug": genre["slug"]}
                )
                game_instance.genres.add(genre_instance)

            # Sauvegarde des développeurs
            for developer in game.get("developers", []):
                dev_instance, _ = Developer.objects.update_or_create(
                    id=developer["id"],
                    defaults={"name": developer["name"]}
                )
                game_instance.developers.add(dev_instance)

            # Sauvegarde des éditeurs
            for publisher in game.get("publishers", []):
                pub_instance, _ = Publisher.objects.update_or_create(
                    id=publisher["id"],
                    defaults={"name": publisher["name"]}
                )
                game_instance.publishers.add(pub_instance)

            # Sauvegarde des captures d’écran
            for screenshot in game.get("short_screenshots", []):
                Screenshot.objects.update_or_create(
                    game=game_instance,
                    image=screenshot["image"]
                )

            # Sauvegarde des évaluations
            for rating in game.get("ratings", []):
                Rating.objects.update_or_create(
                    game=game_instance,
                    title=rating["title"],
                    defaults={
                        "count": rating["count"],
                        "percent": rating["percent"],
                    }
                )

            count += 1
            logging.info(f"✅ Jeu '{game['name']}' {'ajouté' if created else 'mis à jour'} avec succès.")
        except Exception as e:
            logging.error(f"❌ Erreur lors de l'ajout du jeu '{game.get('name', 'Inconnu')}': {e}")

    return count

def run_game_import(params):
    """
    Fonction qui importe des jeux depuis l'API et met à jour la progression dans ImportHistory
    si un identifiant d'import (import_id) est fourni dans params.

    Args:
        params (dict): Paramètres d'import, incluant :
            - max_requests (int)
            - results_per_page (int)
            - metacritic (str)
            - (optionnel) ordering (str)
            - (optionnel) genres (str)
            - (optionnel) import_id (int) : identifiant de l'enregistrement ImportHistory à mettre à jour.
    """
    max_requests = params.get("max_requests", 1)
    results_per_page = params.get("results_per_page", 10)
    metacritic = params.get("metacritic", "60,100")
    ordering = params.get("ordering", "-rating")
    genres = params.get("genres", "")
    import_id = params.get("import_id", None)

    # Si un import_id est fourni, récupérer l'instance ImportHistory pour mettre à jour la progression.
    import_instance = None
    if import_id:
        from .models import ImportHistory
        try:
            import_instance = ImportHistory.objects.get(id=import_id)
        except ImportHistory.DoesNotExist:
            logging.warning(f"ImportHistory avec id {import_id} introuvable.")
    
    page = 1
    while page <= max_requests:
        logging.info(f"📥 Récupération de la page {page}")

        api_params = {
            'key': API_KEY,
            'page': page,
            'page_size': results_per_page,
            'metacritic': metacritic,
            'ordering': ordering,
        }
        if genres:
            api_params['genres'] = genres

        try:
            response = requests.get(BASE_URL, params=api_params, timeout=10)
            print(f"📡 Requête envoyée à : {response.url}")
            print(f"📥 Réponse API : {response.status_code}")
        except requests.exceptions.RequestException as e:
            logging.error(f"Erreur lors de la requête API (page {page}): {e}")
            break

        try:
            data = response.json()
        except Exception as e:
            logging.error(f"Erreur lors de la conversion en JSON (page {page}): {e}")
            break

        print(f"📊 Données reçues : {data}")

        if response.status_code == 200:
            save_to_db(data.get("results", []))
            if import_instance:
                progress_percentage = int((page / max_requests) * 100)
                import_instance.progress = progress_percentage
                import_instance.save()
                logging.info(f"Progression mise à jour à {progress_percentage}% pour ImportHistory id {import_id}")
            page += 1
        else:
            logging.warning(f"⚠ Erreur API : {response.status_code}")
            break
