from django.shortcuts import render
#controller home fonksiyonu buraya
# Create your views here.
from .models import Duyuru


def duyuru_listesi(request):
    duyurular= Duyuru.objects.all().order_by('-olusturulma_tarihi')
    return render(request,'panel/duyuru_listesi.html',{'duyurular':duyurular})