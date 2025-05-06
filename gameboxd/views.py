from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
import datetime
import logging
from .models import ImportHistory, Game, Genre, Review
import requests
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, authenticate, logout
from django.views.decorators.http import require_GET
from django.http import JsonResponse
from datetime import timedelta
from django.utils import timezone
from prometheus_client import generate_latest, Counter



logger = logging.getLogger(__name__)


def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Inscription réussie !")
            return redirect('home')
        elif form.errors:
            messages.error(request, "Erreur lors de l'inscription.")
            context = {
                'form': form,  # avec les erreurs
                'open_modal': True  # ← clé pour forcer l’ouverture de la modal
            }
            return render(request, "games/home.html", context)

        else:
            trending_games = Game.objects.order_by('-release_date', '-metacritic')[:60]
            recent_games = Game.objects.order_by('-release_date')[:30]
            games_by_genre = {}
            for genre in Genre.objects.all():
                games = Game.objects.filter(genres=genre)[:30]
                if games.exists():
                    games_by_genre[genre] = games

            context = {
                'trending_games': trending_games,
                'recent_games': recent_games,
                'games_by_genre': games_by_genre,
                'form': form,  # avec les erreurs
                'open_modal': True  # ← clé pour forcer l’ouverture de la modal
            }
            return render(request, "games/home.html", context)

    return redirect('home')

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, "Connexion réussie !")
            return redirect('home')
        else:
            messages.error(request, "Nom d'utilisateur ou mot de passe incorrect.")

            # Recharger la page d'accueil avec la modal ouverte
            from .models import Game, Genre
            trending_games = Game.objects.filter(metacritic__gte=80).order_by('-release_date', '-metacritic')[:30]
            recent_games = Game.objects.order_by('-release_date')[:30]
            games_by_genre = {}
            for genre in Genre.objects.all():
                games = Game.objects.filter(genres=genre)[:30]
                if games.exists():
                    games_by_genre[genre] = games

            context = {
                'trending_games': trending_games,
                'recent_games': recent_games,
                'games_by_genre': games_by_genre,
                'form': UserCreationForm(),  # Pour inscription
                'login_form': form,          # Pour connexion avec erreurs
                'open_login_modal': True
            }
            return render(request, "games/home.html", context)
    else:
        return redirect('home')


def logout_view(request):
    logout(request)
    messages.info(request, "Vous êtes déconnecté.")
    return redirect('home')

@login_required
def profile(request):
    return render(request, 'auth/profile.html')

def admin_import_games(request):
    if request.method == "POST":
        import_today = request.POST.get("import_today") == "on"
        try:
            # Création d'un enregistrement d'import dans la base
            import_instance = ImportHistory.objects.create(
                max_requests=int(request.POST.get("max_requests", 1)),
                results_per_page=int(request.POST.get("results_per_page", 10)),
                metacritic=request.POST.get("metacritic", "60,100"),
                status="En cours",
                progress=0
            )
        except Exception as e:
            logger.error(f"Erreur lors de la création de l'import : {e}")
            messages.error(request, "Erreur lors de la création de l'import.")
            return redirect("/admin/gameboxd/importhistory/")

        # Construction des paramètres d'import
        params = {
            "max_requests": import_instance.max_requests,
            "results_per_page": import_instance.results_per_page,
            "metacritic": import_instance.metacritic,
            "import_id": import_instance.id
        }

        # Si la case "import_today" est cochée, on ajoute le filtre sur la date du jour
        if import_today:
            today = datetime.now().strftime("%Y-%m-%d")
            params["dates"] = today  # Tu devras gérer ce paramètre côté FastAPI dans `run_game_import`

        try:
            response = requests.post(
                "http://localhost:8001/import",
                json=params,
                headers={"Authorization": "Bearer " + "votretokensecret"},
                timeout=5
            )
            if response.status_code == 200:
                messages.success(request, f"L'importation a été lancée en arrière-plan. ID: {import_instance.id}")
            else:
                messages.error(request, f"Erreur lors du déclenchement de l'importation (code {response.status_code}).")
        except Exception as e:
            logger.error(f"Erreur de communication avec le service d'import : {e}")
            messages.error(request, f"Erreur de communication avec le service d'import : {e}")
        return redirect("/admin/gameboxd/importhistory/")
    return render(request, "admin/import_games.html")


def home(request):
    today = timezone.now().date()

    release = request.GET.get('release')
    sort = request.GET.get('sort')
    genre_filter = request.GET.get('genre')
    platform_filter = request.GET.get('platform')

    filtered_games = Game.objects.all()

    if release == '30':
        filtered_games = filtered_games.filter(release_date__gte=today - timedelta(days=30))
    elif release == '7':
        filtered_games = filtered_games.filter(release_date__gte=today - timedelta(days=7))
    elif release == 'next':
        filtered_games = filtered_games.filter(release_date__gt=today)

    if sort == 'best':
        filtered_games = filtered_games.filter(release_date__year=2024).order_by('-metacritic')
    elif sort == 'popular':
        filtered_games = filtered_games.filter(release_date__year=2024).order_by('-metacritic')
    elif sort == 'top250':
        filtered_games = filtered_games.order_by('-metacritic')[:40]

    if genre_filter:
        filtered_games = filtered_games.filter(genres__name__iexact=genre_filter)

    if platform_filter:
        filtered_games = filtered_games.filter(platform__iexact=platform_filter)

    # Si aucun filtre, affichage standard
    if not (release or sort or genre_filter or platform_filter):
        filtered_games = Game.objects.filter(metacritic__gte=80).order_by('-release_date', '-metacritic')[:40]

    # Déterminer le titre de la section selon le filtre
    if genre_filter:
        section_title = f"Jeux {genre_filter}"
    elif platform_filter:
        section_title = f"Jeux sur {platform_filter}"
    elif release == 'next':
        section_title = "Sorties à venir"
    elif release == '7':
        section_title = "Nouveautés de la semaine"
    elif release == '30':
        section_title = "Nouveautés du mois"
    elif sort == 'top250':
        section_title = "Top 250 jeux"
    elif sort == 'popular':
        section_title = "Populaires en 2024"
    elif sort == 'best':
        section_title = "Meilleurs de l'année"
    else:
        section_title = "Jeux tendances"

    context = {
        'trending_games': filtered_games,
        'section_title': section_title,
        'form': UserCreationForm(),
        'login_form': AuthenticationForm(),
    }
    return render(request, "games/home.html", context)


@require_GET
def search_games(request):
    query = request.GET.get('q', '')
    if query:
        games = Game.objects.filter(title__icontains=query)[:8]
        results = [{'id': game.id, 'title': game.title} for game in games]
    else:
        results = []
    return JsonResponse(results, safe=False)


def game_detail(request, game_id):
    game = get_object_or_404(
        Game.objects.prefetch_related("genres", "platforms", "screenshots", "ratings"),
        id=game_id
    )
    reviews = Review.objects.filter(game=game)
    summary = getattr(game, "summary", None)  # récupère le résumé s'il existe

    context = {
        "game": game,
        "reviews": reviews,
        "summary": summary,
    }
    return render(request, "games/game_detail.html", context)



# Exemple de métrique simple
REQUEST_COUNT = Counter("gameboxd_http_requests_total", "Total des requêtes HTTP")

def metrics_view(request):
    REQUEST_COUNT.inc()
    return HttpResponse(generate_latest(), content_type="text/plain")