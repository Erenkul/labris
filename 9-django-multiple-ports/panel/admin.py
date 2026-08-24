from django.contrib import admin
#modeli admin panele kaydedeceğimiz yer
# Register your models here.
from .models import Duyuru

admin.site.register(Duyuru)

