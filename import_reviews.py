import csv
import os
import django

# Configure l'environnement Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "game_portal.settings")  # adapte si ton projet s'appelle autrement
django.setup()

from gameboxd.models import Game, Review

CSV_PATH = "starfield_reviews.csv"
GAME_ID =  427490 # Remplace par l'ID de Starfield dans ta base

game = Game.objects.get(id=GAME_ID)
inserted = 0

with open(CSV_PATH, newline='', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        review, created = Review.objects.get_or_create(
            game=game,
            platform=row["platform"],
            author=row["author"],
            defaults={
                "score": row["score"],
                "content": row["content"],
                "source": row.get("source", "Metacritic")
            }
        )
        if created:
            inserted += 1

print(f"{inserted} reviews ajoutées à {game.title}.")
