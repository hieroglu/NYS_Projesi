# ana_uygulama/urls.py
from django.urls import path
from django.contrib.auth import views as auth_views # Django'nun hazır kimlik doğrulama view'leri için
from . import views # views.py dosyasındaki view fonksiyonlarını import et

app_name = 'ana_uygulama' # Uygulama alanı (namespace)

urlpatterns = [
    # Kimlik Doğrulama URL'leri
    path('login/', auth_views.LoginView.as_view(template_name='ana_uygulama/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='ana_uygulama:login'), name='logout'),

    # Ana Sayfa / Kontrol Paneli
    path('dashboard/', views.dashboard_view, name='dashboard'),

    # Nakliyeci Rolüne Özel URL'ler
    # Teklif Talepleri
    path('nakliyeci/teklif-talepleri/', views.quote_request_list_nakliyeci_view, name='quote_request_list_nakliyeci_view'),
    path('nakliyeci/teklif-talebi/<int:quote_id>/fiyatla/', views.create_quote_for_request_view, name='create_quote_for_request_view'),
    path('nakliyeci/teklif-talebi/<int:quote_id>/fiyat-guncelle/', views.update_quote_for_request_view, name='update_quote_for_request_view'),
    path('nakliyeci/teklif-talepleri/<int:pk>/', views.quote_request_detail_nakliyeci_view, name='quote_request_detail_nakliyeci'),
    path('nakliyeci/teklif-talebi/olustur/', views.quote_request_create_nakliyeci_view, name='quote_request_create_nakliyeci_view'), # Nakliyeciler için bu view hata mesajı döner
    path('nakliyeci/teklif-talebi/<int:pk>/guncelle/', views.quote_request_update_nakliyeci_view, name='quote_request_update_nakliyeci_view'), # Nakliyeciler için bu view hata mesajı döner
    path('nakliyeci/teklif-talebi/<int:pk>/sil/', views.quote_request_delete_nakliyeci_view, name='quote_request_delete_nakliyeci_view'), # Nakliyeciler için bu view hata mesajı döner

    # Sevkiyatlar (İşler)
    path('nakliyeci/isler/', views.shipment_list_nakliyeci_view, name='shipment_list_nakliyeci_view'),
    path('nakliyeci/is/<int:pk>/arac-kaldir/', views.shipment_remove_vehicle_nakliyeci_view, name='shipment_remove_vehicle_nakliyeci_view'), # Hata alınan path
    path('nakliyeci/is/yeni/', views.shipment_create_nakliyeci_view, name='shipment_create_nakliyeci_view'),
    path('nakliyeci/is/<int:quote_id>/tekliften-olustur/', views.shipment_create_from_quote_nakliyeci_view, name='shipment_create_from_quote_nakliyeci_view'),
    path('nakliyeci/is/<int:shipment_id>/detay/', views.shipment_detail_nakliyeci_view, name='shipment_detail_nakliyeci_view'),
    path('nakliyeci/is/<int:shipment_id>/guncelle/', views.shipment_update_nakliyeci_view, name='shipment_update_nakliyeci_view'),
    path('nakliyeci/is/<int:shipment_id>/sil/', views.shipment_delete_nakliyeci_view, name='shipment_delete_nakliyeci_view'),
    path('nakliyeci/is/<int:shipment_id>/arac-ata/', views.assign_vehicle_to_shipment_view, name='assign_vehicle_to_shipment_view'),
    path('nakliyeci/is/<int:shipment_id>/durum-guncelle/', views.update_shipment_status_nakliyeci_view, name='update_shipment_status_nakliyeci_view'),

    # Araç Yönetimi
    path('nakliyeci/araclar/', views.vehicle_list_nakliyeci_view, name='vehicle_list_nakliyeci_view'),
    path('nakliyeci/arac/yeni/', views.vehicle_create_nakliyeci_view, name='vehicle_create_nakliyeci_view'),
    path('nakliyeci/arac/yeni/<int:carrier_id>/', views.vehicle_create_nakliyeci_view, name='vehicle_create_nakliyeci_for_carrier_view'), # Taşıyıcıya bağlı araç ekleme
    path('nakliyeci/arac/<int:vehicle_id>/detay/', views.vehicle_detail_nakliyeci_view, name='vehicle_detail_nakliyeci_view'),
    path('nakliyeci/arac/<int:vehicle_id>/guncelle/', views.vehicle_update_nakliyeci_view, name='vehicle_update_nakliyeci_view'),
    path('nakliyeci/arac/<int:vehicle_id>/sil/', views.vehicle_delete_nakliyeci_view, name='vehicle_delete_nakliyeci_view'),


    # Taşıyıcı Yönetimi
    path('nakliyeci/tasiyicilar/', views.carrier_list_nakliyeci_view, name='carrier_list_nakliyeci_view'),
    path('nakliyeci/tasiyici/yeni/', views.carrier_create_nakliyeci_view, name='carrier_create_nakliyeci_view'),
    path('nakliyeci/tasiyici/<int:pk>/detay/', views.carrier_detail_nakliyeci_view, name='carrier_detail_nakliyeci_view'),
    path('nakliyeci/tasiyici/<int:pk>/guncelle/', views.carrier_update_nakliyeci_view, name='carrier_update_nakliyeci_view'),
    path('nakliyeci/tasiyici/<int:pk>/sil/', views.carrier_delete_nakliyeci_view, name='carrier_delete_nakliyeci_view'),
    path('nakliyeci/tasiyici/<int:carrier_id>/banka-hesabi/ekle/', views.carrier_bank_account_add_view, name='carrier_bank_account_add_view'),
    path('nakliyeci/tasiyici/<int:carrier_id>/banka-hesabi/<int:pk>/duzenle/', views.carrier_bank_account_edit_view, name='carrier_bank_account_edit_view'),
    path('nakliyeci/tasiyici/<int:carrier_id>/banka-hesabi/<int:pk>/sil/', views.carrier_bank_account_delete_view, name='carrier_bank_account_delete_view'),

    # Faturalar (Nakliyeci tarafından kesilen)

    path('nakliyeci/faturalar/', views.invoice_list_nakliyeci_view, name='invoice_list_nakliyeci_view'),
    path('nakliyeci/faturalar/sevkiyat/<int:shipment_id>/olustur/', views.invoice_create_view, name='invoice_create_view'),
    path('nakliyeci/faturalar/<int:pk>/detay/', views.invoice_detail_nakliyeci_view, name='invoice_detail_nakliyeci_view'),
    path('nakliyeci/faturalar/<int:pk>/guncelle/', views.invoice_update_view, name='invoice_update_view'),
    path('nakliyeci/faturalar/<int:pk>/odenmis-olarak-isaretle/', views.invoice_mark_as_paid_nakliyeci_view, name='invoice_mark_as_paid_nakliyeci_view'),
    path('nakliyeci/faturalar/<int:pk>/sil/', views.invoice_delete_view, name='invoice_delete_view'),


    # Ödemeler/Tahsilatlar (Nakliyeci)
    path('nakliyeci/odemeler/', views.payment_list_nakliyeci_view, name='payment_list_nakliyeci_view'),
    path('nakliyeci/odeme/yeni/', views.payment_create_nakliyeci_view, name='payment_create_nakliyeci_view'),
    path('nakliyeci/odeme/<int:pk>/detay/', views.payment_detail_nakliyeci_view, name='payment_detail_nakliyeci_view'),
    path('nakliyeci/odeme/<int:pk>/guncelle/', views.payment_update_nakliyeci_view, name='payment_update_nakliyeci_view'),
    # Banka Hesapları (Nakliyeci Şirketi Kendi Hesapları) - ÖNEMLİ: Modelde Carrier'a bağlı olduğu için bu kısım yorumlandı.
    # Eğer BankAccount doğrudan Company'ye bağlanacaksa models.py güncellenmeli.
    # Şu anki yapıya göre, banka hesapları taşıyıcılara aittir.
     path('nakliyeci/banka-hesaplari/', views.bank_account_list_nakliyeci_view, name='bank_account_list_nakliyeci_view'),
    # path('nakliyeci/banka-hesaplari/yeni/', views.bank_account_create_nakliyeci_view, name='bank_account_create_nakliyeci_view'), # Bu, carrier_id olmadan genel bir ekleme olacağı için şu anki modelle uyumsuz.
    # path('nakliyeci/banka-hesaplari/<int:pk>/detay/', views.bank_account_detail_nakliyeci_view, name='bank_account_detail_nakliyeci_view'),
    # path('nakliyeci/banka-hesaplari/<int:pk>/guncelle/', views.bank_account_update_nakliyeci_view, name='bank_account_update_nakliyeci_view'),
    # path('nakliyeci/banka-hesaplari/<int:pk>/sil/', views.bank_account_delete_nakliyeci_view, name='bank_account_delete_nakliyeci_view'),

    # Nakliyeci Firma Kullanıcıları
    path('nakliyeci/kullanicilar/', views.company_user_list_nakliyeci_view, name='company_user_list_nakliyeci_view'),
    path('nakliyeci/kullanici/yeni/', views.company_user_create_nakliyeci_view, name='company_user_create_nakliyeci_view'),
    # path('nakliyeci/kullanici/<int:pk>/guncelle/', views.company_user_update_nakliyeci_view, name='company_user_update_nakliyeci_view'),
    # path('nakliyeci/kullanici/<int:pk>/sil/', views.company_user_delete_nakliyeci_view, name='company_user_delete_nakliyeci_view'),

    # Nakliyeci - Fabrika Firma Listeleme ve Yeni Fabrika Ekleme
    path('nakliyeci/fabrikalar/', views.company_list_for_nakliyeci_view, name='company_list_for_nakliyeci_view'),
    path('nakliyeci/fabrika/yeni/', views.factory_create_by_nakliyeci_view, name='factory_create_by_nakliyeci_view'),

    # Fabrika Rolüne Özel URL'ler
    # Teklif Talepleri (Fabrika tarafından oluşturulan)
    path('fabrika/teklif-talepleri/', views.quote_request_list_fabrika_view, name='quote_request_list_fabrika_view'),
    path('fabrika/teklif-talebi/olustur/', views.quote_request_create_fabrika_view, name='quote_request_create_fabrika_view'),
    path('fabrika/teklif-talebi/<int:pk>/detay/', views.quote_request_detail_fabrika_view, name='quote_request_detail_fabrika_view'),
    path('fabrika/teklif-talebi/<int:pk>/guncelle/', views.request_quote_update_fabrika_view, name='request_quote_update_fabrika_view'),
    path('fabrika/teklif-talebi/<int:pk>/sil/', views.quote_request_delete_fabrika_view, name='quote_request_delete_fabrika_view'),
    path('fabrika/teklif-talebi/<int:quote_id>/kabul-et/', views.accept_quote_fabrika_view, name='accept_quote_fabrika_view'),
    path('fabrika/teklif-talebi/<int:quote_id>/reddet/', views.reject_quote_fabrika_view, name='reject_quote_fabrika_view'),

    # Sevkiyatlar (Fabrika tarafından takip edilen)
    path('fabrika/sevkiyatlar/', views.shipment_list_fabrika_view, name='shipment_list_fabrika_view'),
    path('fabrika/sevkiyatlar/<int:shipment_id>/detay/', views.shipment_detail_fabrika_view, name='shipment_detail_fabrika_view'),

    # Faturalar (Fabrikaya kesilen)
    path('fabrika/faturalar/', views.invoice_list_fabrika_view, name='invoice_list_fabrika_view'),
    path('fabrika/faturalar/<int:invoice_id>/detay/', views.invoice_detail_fabrika_view, name='invoice_detail_fabrika_view'),

    # Ödemeler (Fabrika tarafından yapılan)
    # path('fabrika/odemeler/', views.payment_list_fabrika_view, name='payment_list_fabrika_view'),
    # path('fabrika/odeme/yeni/', views.payment_create_fabrika_view, name='payment_create_fabrika_view'),
    # path('fabrika/odeme/<int:pk>/detay/', views.payment_detail_fabrika_view, name='payment_detail_fabrika_view'),
    # path('fabrika/odeme/<int:pk>/guncelle/', views.payment_update_fabrika_view, name='payment_update_fabrika_view'),
    # path('fabrika/odeme/<int:pk>/sil/', views.payment_delete_fabrika_view, name='payment_delete_fabrika_view'),


    # Fabrika Firma Kullanıcıları
    path('fabrika/kullanicilar/', views.company_user_list_fabrika_view, name='company_user_list_fabrika_view'),
    path('fabrika/kullanici/yeni/', views.company_user_create_fabrika_view, name='company_user_create_fabrika_view'),
    path('fabrika/kullanici/<int:pk>/guncelle/', views.company_user_update_fabrika_view, name='company_user_update_fabrika_view'),
    path('fabrika/kullanici/<int:pk>/sil/', views.company_user_delete_fabrika_view, name='company_user_delete_fabrika_view'),

    # Fabrika - Firma Listeleme ve Yeni Tedarikçi Ekleme
    path('fabrika/firmalar/', views.company_list_for_fabrika_view, name='company_list_for_fabrika_view'),
    path('fabrika/tedarikci/yeni/', views.shipper_create_by_fabrika_view, name='shipper_create_by_fabrika_view'),


    # Firma Yönetimi (Genellikle Süperkullanıcı Erişimi İçin)
    path('firmalar/', views.company_list_view, name='company_list_view'),
    path('firma/olustur/', views.company_create_view, name='company_create_view'),
    path('firma/<int:pk>/detay/', views.company_detail_view, name='company_detail_view'),
    path('firma/<int:pk>/guncelle/', views.company_update_view, name='company_update_view'),
    path('firma/<int:pk>/sil/', views.company_delete_view, name='company_delete_view'),

    # Global Arama
    path('ara/', views.global_search_view, name='global_search_view'),
    path('ajax-ara/', views.ajax_live_search_view, name='ajax_live_search_view'),
]
