from django.db import models

# Create your models here.
class Duyuru(models.Model):
    baslik = models.CharField(max_length=200)
    icerik = models.TextField()
    olusturulma_tarihi = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.baslik