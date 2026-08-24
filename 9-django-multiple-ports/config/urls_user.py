from django.urls import path
from django.http import HttpResponse

from panel.views import duyuru_listesi

#def home(request):
#    return HttpResponse("Kullanici paneline welcome!")

urlpatterns=[
    path('',duyuru_listesi),
]
#model view controller yapımızdaki view modeli html sayfaasının template gelecek sonradan