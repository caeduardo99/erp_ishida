"""erp_ishida URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path,include
from erp import views
from django.urls import re_path
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('sii_seguridad.urls',)),
    path('empresa/mq2010New', views.mq2010New, name='mq2010New'),
    path('empresa/mq2010New/consgeneraltrans', views.consgeneraltrans, name='consgeneraltrans'),
    path('empresa/mq2010New/contact', views.contact, name='contact'),
    path('empresa/mq2010New/infoempresa', views.infoempresa, name='infoempresa'),
    path('empresa/mq2010New/facturacion', views.facturacion, name='facturacion'),
    path('empresa/mq2010New/listaprecios', views.listaprecios, name='listaprecios'),
    path('empresa/mq2010New/listapreciosjson', views.listapreciojson, name='listapreciosjson'),
    path('empresa/mq2010New/bodegajson', views.obtener_bodegas, name='bodegajson'),
    path('empresa/mq2010New/ivgrupo1_json', views.ivgrupo1_json, name='ivgrupo1_json'),
    path('empresa/mq2010New/ivgrupo2_json', views.ivgrupo2_json, name='ivgrupo2_json'),
    path('empresa/mq2010New/ivgrupo6_json', views.ivgrupo6_json, name='ivgrupo6_json'),
    path('empresa/mq2010New/listaexistencia', views.listaexistencia, name='listaexistencia'),
    path('empresa/mq2010New/listaexistenciajson', views.listaexistenciajson, name='listaexistenciajson'),
    path('empresa/mq2010New/ctacontablejson', views.obtener_ctacontable, name='ctacontablejson'),


]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)