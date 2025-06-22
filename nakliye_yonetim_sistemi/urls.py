# nakliye_yonetim_sistemi/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings

from ana_uygulama import views # ana_uygulama'daki view'leri doğrudan erişmek için import edildi

urlpatterns = [
    # Admin paneli için URL
    path('admin/', admin.site.urls),

    # Ana sayfayı (kök URL) doğrudan ana_uygulama'daki dashboard_view'e yönlendir.
    # DİKKAT: Bu değişiklikle birlikte, 'ana_uygulama/urls.py' dosyasındaki
    # 'path('dashboard/', views.dashboard_view, name='dashboard'),' satırını
    # SİZİN MANUEL OLARAK SİLMENİZ GEREKMEKTEDİR.
    path('', views.dashboard_view, name='home'),

    # 'ana_uygulama' uygulamasının diğer tüm URL'lerini '/ana_uygulama/' öneki altına dahil et.
    # Örneğin, 'ana_uygulama/teklif-talepleri/' gibi.
    path('', include('ana_uygulama.urls')),
]

# Geliştirme ortamında medya dosyalarını sunmak için (DEBUG = True ise)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)