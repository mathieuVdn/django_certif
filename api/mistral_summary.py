import os
import requests
import logging
from typing import List

# Configuration du logger
logger = logging.getLogger(__name__)

# Variables d’environnement
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11500/api/generate")
MODEL_NAME = "mistral:7b-instruct-q4_0"

def build_prompt(reviews: List[str], lang: str = "en") -> str:
    """
    Construit le prompt à envoyer au modèle Mistral.
    """
    text = "\n".join([f"- {r}" for r in reviews])

    if lang == "fr":
        return f"""Tu es un journaliste spécialisé dans les jeux vidéo, chargé d’analyser des critiques professionnelles et des retours de joueurs.
À partir des avis disponibles sur Metacritic, tu dois traduire en français et résumer fidèlement les critiques fournies.
Ton objectif est de produire une synthèse rédigée, claire, neutre et structurée, qui met en évidence les points positifs, les points négatifs, ainsi que le ressenti général exprimé dans les avis.
N’ajoute aucune information extérieure et ne donne aucune opinion personnelle.
La réponse doit être rédigée uniquement en français, sous forme de texte continu, sans puces, sans numérotation, ni formatage spécial.

Avis :
{text}
"""
    else:
        return f"""Here are player reviews about a video game:
{text}

Write a clear and neutral summary that highlights the main strengths, weaknesses, and general feeling around the game.
Do not add personal opinion or external context.
"""

def generate_summary(reviews: List[str], lang: str = "en") -> dict:
    """
    Génère un résumé des critiques fournies à l'aide du modèle Mistral via Ollama.

    Returns:
        dict: Contenant le résumé généré, le modèle utilisé, la langue.
    """
    if not reviews:
        raise ValueError("La liste des critiques est vide.")

    prompt = build_prompt(reviews, lang)
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=300)
        response.raise_for_status()
        summary = response.json().get("response", "").strip()
        logger.info("Résumé généré avec succès.")
        return {
            "summary": summary,
            "model": MODEL_NAME,
            "used_lang": lang
        }
    except requests.RequestException as e:
        logger.error(f"Erreur lors de la génération du résumé : {e}")
        raise RuntimeError(f"Erreur lors de la génération du résumé : {e}")
