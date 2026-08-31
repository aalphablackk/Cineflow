from django.db import models

# Create your models here.



class Movie(models.Model):

    class Status(models.TextChoices):
        COMING_SOON = "coming_soon", "Coming Soon"
        NOW_SHOWING = "now_showing", "Now Showing"
        ENDED = "ended", "Ended"

    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    poster = models.ImageField(upload_to="movies/posters/",blank=True,null=True,)
    poster_url = models.URLField(blank=True,)
    trailer_url = models.URLField(blank=True)
    duration = models.PositiveIntegerField()
    release_date = models.DateField()
    age_rating = models.CharField(max_length=20)

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.COMING_SOON,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    @property
    def poster_source(self):
        if self.poster:
            return self.poster.url

        if self.poster_url:
            return self.poster_url

        return ""

    def __str__(self):
        return self.title