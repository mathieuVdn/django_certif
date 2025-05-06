from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from gameboxd.models import Game, Review
from unittest.mock import patch
from api.mistral_summary import generate_summary  # adapte si besoin
from fastapi.testclient import TestClient
from api.api import app

client = TestClient(app)

class APITests(TestCase):
    def setUp(self):
        self.username = "testuser"
        self.password = "testpass"
        User.objects.create_user(username=self.username, password=self.password)

    def test_login_success(self):
        response = client.post("/login", data={
            "username": self.username,
            "password": self.password
        })
        assert response.status_code == 200
        assert "access_token" in response.json()

    def test_login_failure(self):
        response = client.post("/login", data={
            "username": self.username,
            "password": "wrongpass"
        })
        assert response.status_code == 401

# --- Tests Django views ---
class HomeViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
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

# --- Simulation du résumé IA ---
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
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "response": "Ceci est un faux résumé généré pour test."
        }

        reviews = list(Review.objects.filter(game=self.game).values_list("content", flat=True))
        result = generate_summary(reviews, lang="fr")

        self.assertEqual(result["model"], "mistral")
        self.assertEqual(result["used_lang"], "fr")
        self.assertIn("faux résumé", result["summary"])
