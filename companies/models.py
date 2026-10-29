from django.db import models


class Company(models.Model):
    """
    Persistent model representing an Indian listed company resolved via MarketPing.
    """
    name = models.CharField(max_length=255)
    ticker = models.CharField(max_length=50, unique=True, db_index=True)
    slug = models.SlugField(max_length=100, unique=True, db_index=True)
    bse_code = models.CharField(max_length=50, blank=True, null=True)
    source_url = models.URLField(max_length=500, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["ticker"]
        verbose_name_plural = "Companies"

    def __str__(self):
        return f"{self.ticker} - {self.name}"
