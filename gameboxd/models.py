from django.db import models
from django.utils.timezone import now
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class Game(models.Model):
    id = models.IntegerField(primary_key=True)  # ID unique de l'API
    title = models.CharField(max_length=255) # Tite du jeu
    slug = models.CharField(max_length=255, null=True, blank=True)  # Slug pour metacritics à scrapper
    release_date = models.DateField(null=True, blank=True)
    rating = models.FloatField(null=True, blank=True)  # Note moyenne
    ratings_count = models.IntegerField(null=True, blank=True)  # Nombre total d'évaluations
    metacritic = models.IntegerField(null=True, blank=True)  # Score Metacritic
    playtime = models.IntegerField(null=True, blank=True)  # Temps de jeu moyen (en heures)
    website = models.URLField(null=True, blank=True)  # Site officiel
    background_image = models.URLField(null=True, blank=True)  # Image
    reddit_url = models.URLField(null=True, blank=True)  # URL Reddit
    added_by_status = models.JSONField(null=True, blank=True)  # Stats des utilisateurs ajoutant ce jeu
    updated_at = models.DateTimeField(auto_now=True)

    # Relations
    platforms = models.ManyToManyField("Platform", related_name="games")
    genres = models.ManyToManyField("Genre", related_name="games")

    def __str__(self):
        return self.title

class Platform(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=255)
    slug = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name

class Genre(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=255)
    slug = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name

class Developer(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name

class Publisher(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name

class Screenshot(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='screenshots')
    image = models.URLField()

    class Meta:
        unique_together = ('game', 'image')  # Empêche les doublons

    def __str__(self):
        return f"Screenshot of {self.game.title}"

class Rating(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='ratings')
    title = models.CharField(max_length=50)
    count = models.IntegerField() 
    percent = models.FloatField() 

    class Meta:
        unique_together = ('game', 'title') 

    def __str__(self):
        return f"{self.title} ({self.percent}%) - {self.game.title}"
    
# Modèle pour enregistrer les imports passés
class ImportHistory(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    max_requests = models.IntegerField()
    results_per_page = models.IntegerField()
    metacritic = models.CharField(max_length=20)
    status = models.CharField(max_length=20, default="En cours")
    progress = models.IntegerField(default=0) 

    def __str__(self):
        return f"Import du {self.created_at.strftime('%Y-%m-%d %H:%M:%S')} - {self.status}"
    
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(max_length=500, blank=True)
    favorite_genre = models.ForeignKey('Genre', on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return self.user.username
    
class Review(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    platform = models.CharField(max_length=100)
    author = models.CharField(max_length=255)
    score = models.CharField(max_length=10)
    content = models.TextField()
    source = models.CharField(max_length=100, default="Metacritic")

    class Meta:
        unique_together = ('game', 'platform', 'author')  

class Summary(models.Model):
    game = models.OneToOneField(Game, on_delete=models.CASCADE, related_name="summary")
    content = models.TextField()
    model_used = models.CharField(max_length=100, default="mistral-7b")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Résumé pour {self.game.title}"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()