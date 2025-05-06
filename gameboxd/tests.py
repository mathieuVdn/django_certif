from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from gameboxd.models import Game, Review
from unittest.mock import patch
from api.mistral_summary import generate_summary
from rest_framework.test import APIClient
from django.contrib.auth.models import User
from fastapi.testclient import TestClient

class APITests(TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.username = "testuser"
        self.password = "testpass"
        self.user = User.objects.create_user(username=self.username, password=self.password)

    def test_login_success(self):
        response = self.client.post("/login/", data={
            "username": self.username,
            "password": self.password
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn("access_token", response.json())

    def test_login_failure(self):
        response = self.client.post("/login/", data={
            "username": self.username,
            "password": "wrongpass"
        })
        self.assertEqual(response.status_code, 401)

    def test_access_games_authenticated(self):
        # Obtenir un token JWT
        token = self.client.post("/login/", data={
            "username": self.username,
            "password": self.password
        }).json()["access_token"]

        # Utiliser ce token dans le header Authorization
        response = self.client.get("/games/", headers={
            "Authorization": f"Bearer {token}"
        })

        self.assertEqual(response.status_code, 200)
class HomeViewTests(TestCase):
    def setUp(self):
        for i in range(3):
            Game.objects.create(
                id=100 + i,
                title=f"Jeu {i}",
                release_date=timezone.now().date(),
                rating=4.5,
                metacritic=85 + i
            )

    def test_home_status_and_template(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "games/home.html")

    def test_home_context_contains_recent_games(self):
        response = self.client.get(reverse("home"))
        self.assertIn("trending_games", response.context)
        self.assertEqual(len(response.context["trending_games"]), 3)


class GenerateSummaryFakeTests(TestCase):
    def setUp(self):
        self.game = Game.objects.create(
            id=1,
            title="Test Game",
            slug="test-game",
            release_date=timezone.now().date()
        )
        for i in range(5):
            Review.objects.create(
                game=self.game,
                platform="pc",
                author=f"user{i}",
                score="8",
                content=f"This is review number {i}.",
                source="Metacritic"
            )

    @patch("api.mistral_summary.requests.post")
    def test_generate_summary_fake_response(self, mock_post):
        # Simuler la réponse Ollama sans appel réel
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "response": "Ceci est un faux résumé généré pour test."
        }

        reviews = list(Review.objects.filter(game=self.game).values_list("content", flat=True))
        result = generate_summary(reviews, lang="fr")

        self.assertEqual(result["model"], "mistral")
        self.assertEqual(result["used_lang"], "fr")
        self.assertIn("faux résumé", result["summary"])
