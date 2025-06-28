# ana_uygulama/views.py
import calendar
import json
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib import messages
from django.utils import timezone
from datetime import date, timedelta
from django.db.models import Sum, Q, Count # Count eklendi
from django.urls import reverse
from django.db.models.functions import TruncMonth # Ay bazında gruplama için

# Model importları
from .models import (
    BankAccount, Carrier, Company, CustomUser, QuoteRequest, Shipment, Vehicle, Invoice, Payment
)
from decimal import Decimal

# Form importları
from .forms import (
    CompanyUserCreationForm, QuoteRequestForm, VehicleForm, ShipmentFormNakliyeci,
    OfferPriceForm, AssignVehicleForm, ShipmentStatusUpdateForm, InvoiceForm,
    FactoryCreationByShipperForm, CarrierForm, BankAccountForm, CompanyForm,
    PaymentForm
)


# === Yardımcı Fonksiyonlar / Decorator'lar ===
# Kullanıcının şirket tipini kontrol eden decorator
def user_company_type_required(company_type):
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.error(request, "Bu sayfaya erişim için giriş yapmalısınız.")
                return redirect('ana_uygulama:login')
            if not request.user.company or request.user.company.company_type != company_type:
                messages.error(request, "Bu sayfaya erişim yetkiniz yoktur.")
                return redirect('ana_uygulama:dashboard')
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

# Kullanıcının nakliyeci olduğunu kontrol eden decorator
nakliyeci_required = user_company_type_required('NAKLIYECI')
# Kullanıcının fabrika olduğunu kontrol eden decorator
fabrika_required = user_company_type_required('FABRIKA')

# === Logout View ===
def logout_view(request):
    logout(request)
    messages.info(request, "Başarıyla çıkış yaptınız.")
    return redirect(settings.LOGIN_URL)
# === Dashboard View ===
@login_required
def dashboard_view(request):
    """
    Renders the customized dashboard based on the user's role (Shipper or Factory).
    Displays different metrics for each company type.
    """
    user = request.user
    today = timezone.now().date()
    seven_days_later = today + timedelta(days=7)
    thirty_days_ago = today - timedelta(days=30)
    six_months_ago_start = (today - timedelta(days=180)).replace(day=1) # Son 6 ayın ilk günü

    # Kullanıcının bir firmaya atanıp atanmadığını kontrol edin
    if not hasattr(user, 'company') or user.company is None:
        messages.warning(request, "Henüz bir firmaya atanmadınız. Lütfen sistem yöneticisiyle iletişime geçin.")
        context = {
            'firma_adi': "Firma Atanmadı",
            'kullanici_adi': user.first_name or user.username,
            'is_nakliyeci': False,
            'is_fabrika': False,
            'today': today,
            'page_title': 'Kontrol Paneli',
            'aylik_is_etiketleri': json.dumps([]),
            'aylik_is_cirolari': json.dumps([]),
            'bekleyen_teklif_talepleri_sayisi': 0,
            'onay_bekleyen_teklifler_sayisi': 0,
            'toplam_aktif_is_sayisi': 0,
            'toplam_arac_sayisi': 0,
            'son_aktif_isler': [],
            'muayenesi_gecmis_arac_sayisi': 0,
            'sigortasi_gecmis_arac_sayisi': 0,
            'muayenesi_yaklasan_araclar': [],
            'sigortasi_yaklasan_araclar': [],
            'bu_ay_kesilen_faturalar_toplami': Decimal('0.00'),
            'odenmemis_fatura_sayisi': 0,
            'vadesi_gecmis_tahsilat_sayisi': 0,
            'gonderdigim_bekleyen_talepler_sayisi': 0,
            'onayimi_bekleyen_teklifler_sayisi': 0,
            'aktif_sevkiyatlarim_sayisi': 0,
            'yaklasan_odeme_sayisi': 0,
            'tamamlanan_sevkiyat_bu_ay_sayisi': 0,
            'bu_ayki_toplam_fatura_tutari': Decimal('0.00'),
            'vadesi_gecmis_odeme_sayisi': 0,
            'recent_activities': []
        }
        return render(request, 'ana_uygulama/dashboard.html', context)

    current_company = user.company

    # Ortak bağlam verileri için varsayılanları başlatın
    context = {
        'firma_adi': current_company.name,
        'kullanici_adi': user.first_name or user.username,
        'is_nakliyeci': False,
        'is_fabrika': False,
        'today': today,
        'page_title': 'Kontrol Paneli',
        'aylik_is_etiketleri': json.dumps([]),
        'aylik_is_cirolari': json.dumps([]),
        'bekleyen_teklif_talepleri_sayisi': 0,
        'onay_bekleyen_teklifler_sayisi': 0,
        'toplam_aktif_is_sayisi': 0,
        'toplam_arac_sayisi': 0,
        'son_aktif_isler': [],
        'muayenesi_gecmis_arac_sayisi': 0,
        'sigortasi_gecmis_arac_sayisi': 0,
        'muayenesi_yaklasan_araclar': [],
        'sigortasi_yaklasan_araclar': [],
        'bu_ay_kesilen_faturalar_toplami': Decimal('0.00'),
        'odenmemis_fatura_sayisi': 0,
        'vadesi_gecmis_tahsilat_sayisi': 0,
        'gonderdigim_bekleyen_talepler_sayisi': 0,
        'onayimi_bekleyen_teklifler_sayisi': 0,
        'aktif_sevkiyatlarim_sayisi': 0,
        'yaklasan_odeme_sayisi': 0,
        'tamamlanan_sevkiyat_bu_ay_sayisi': 0,
        'bu_ayki_toplam_fatura_tutari': Decimal('0.00'),
        'vadesi_gecmis_odeme_sayisi': 0,
        'last_items': [],
        'recent_activities': [] # Başlangıçta boş
    }

    # Son Hareketler (Recent Activities) - Genel bir örnek
    # Bu kısmı kendi uygulamanızdaki gerçek aktivite loglarına göre doldurmanız gerekecektir.
    # Şimdilik örnek verilerle doldurulmuştur.
    # Örnek: Son 5 sevkiyat veya faturayı activity olarak gösterilebilir.
    if current_company.company_type == 'NAKLIYECI':
        # Nakliyeci için son 5 sevkiyat veya fatura
        recent_shipments = Shipment.objects.filter(shipper_company=current_company).order_by('-created_at')[:3]
        recent_invoices = Invoice.objects.filter(issued_by_shipper=current_company).order_by('-created_at')[:2]
        
        for s in recent_shipments:
            context['recent_activities'].append({
                'icon': 'fas fa-truck',
                'message': f"Sevkiyat #{s.pk} ({s.get_status_display()})",
                'date': s.created_at,
                'url': reverse('ana_uygulama:shipment_detail_nakliyeci_view', args=[s.pk])
            })
        for i in recent_invoices:
            context['recent_activities'].append({
                'icon': 'fas fa-file-invoice-dollar',
                'message': f"Fatura #{i.invoice_number} ({i.get_status_display()})",
                'date': i.created_at,
                'url': reverse('ana_uygulama:invoice_detail_nakliyeci_view', args=[i.pk])
            })
    elif current_company.company_type == 'FABRIKA':
        # Fabrika için son 5 sevkiyat veya fatura
        recent_shipments = Shipment.objects.filter(factory=current_company).order_by('-created_at')[:3]
        recent_invoices = Invoice.objects.filter(billed_to_factory=current_company).order_by('-created_at')[:2]

        for s in recent_shipments:
            context['recent_activities'].append({
                'icon': 'fas fa-truck-loading',
                'message': f"Sevkiyat #{s.pk} ({s.get_status_display()})",
                'date': s.created_at,
                'url': reverse('ana_uygulama:shipment_detail_fabrika_view', args=[s.pk])
            })
        for i in recent_invoices:
            context['recent_activities'].append({
                'icon': 'fas fa-receipt',
                'message': f"Fatura #{i.invoice_number} ({i.get_status_display()})",
                'date': i.created_at,
                'url': reverse('ana_uygulama:invoice_detail_fabrika_view', args=[i.pk])
            })
    
    # Tarihe göre sırala ve ilk 5'i al
    context['recent_activities'] = sorted(context['recent_activities'], key=lambda x: x['date'], reverse=True)[:5]


    if current_company.company_type == 'NAKLIYECI':
        context['is_nakliyeci'] = True

        # Stat Kartları
        # Bekleyen Teklif Talepleri: Nakliyeciye henüz fiyat verilmemiş, durumu 'PENDING' olan talepler
        context['bekleyen_teklif_talepleri_sayisi'] = QuoteRequest.objects.filter(
            status='PENDING'
        ).count()
        # Onay Bekleyen Teklifler: Nakliyecinin fiyat verdiği ama henüz kabul edilmemiş/reddedilmemiş talepler
        context['onay_bekleyen_teklifler_sayisi'] = QuoteRequest.objects.filter(
            priced_by_shipper_company=current_company, status='QUOTED'
        ).count()
        # Toplam Aktif İş Sayısı: Atama bekleyen, atandı, yolda olan sevkiyatlar
        context['toplam_aktif_is_sayisi'] = Shipment.objects.filter(
            shipper_company=current_company,
            status__in=['PENDING_ASSIGNMENT', 'ASSIGNED', 'IN_TRANSIT']
        ).count()
        # Toplam Araç Sayısı: Nakliyecinin yönettiği taşıyıcılara ait araçlar
        context['toplam_arac_sayisi'] = Vehicle.objects.filter(
            carrier__managed_by_shipper=current_company
        ).count()

        # Son Aktif İşler (Nakliyeci)
        # Örnek: Durumu tamamlanmış, faturalanmış veya iptal edilmiş olmayan son 5 sevkiyat
        context['son_aktif_isler'] = Shipment.objects.filter(
            shipper_company=current_company
        ).exclude(status__in=['DELIVERED', 'CANCELLED', 'BILLED', 'COMPLETED']).order_by('-created_at')[:5]

        # Araç Uyarıları
        nakliyeci_araclari = Vehicle.objects.filter(carrier__managed_by_shipper=current_company)
        muayenesi_gecmis_araclar_list = []
        sigortasi_gecmis_araclar_list = []
        muayenesi_yaklasan_araclar_list = []
        sigortasi_yaklasan_araclar_list = []

        for vehicle in nakliyeci_araclari:
            # Muayene kontrolü
            if vehicle.inspection_expiry_date:
                if vehicle.inspection_expiry_date < today:
                    muayenesi_gecmis_araclar_list.append(vehicle)
                elif today <= vehicle.inspection_expiry_date <= seven_days_later:
                    muayenesi_yaklasan_araclar_list.append(vehicle)

            # Sigorta kontrolü
            if vehicle.insurance_expiry_date:
                if vehicle.insurance_expiry_date < today:
                    sigortasi_gecmis_araclar_list.append(vehicle)
                elif today <= vehicle.insurance_expiry_date <= seven_days_later:
                    sigortasi_yaklasan_araclar_list.append(vehicle)

        context['muayenesi_gecmis_arac_sayisi'] = len(muayenesi_gecmis_araclar_list)
        context['sigortasi_gecmis_arac_sayisi'] = len(sigortasi_gecmis_araclar_list)
        context['muayenesi_yaklasan_araclar'] = muayenesi_yaklasan_araclar_list
        context['sigortasi_yaklasan_araclar'] = sigortasi_yaklasan_araclar_list


        # Finans Özeti (Nakliyeci - Kesilen faturalar ve tahsilatlar)
        nakliyeci_faturalari = Invoice.objects.filter(issued_by_shipper=current_company)

        # Bu ay kesilen faturaların toplamı
        context['bu_ay_kesilen_faturalar_toplami'] = nakliyeci_faturalari.filter(
            issue_date__month=today.month, issue_date__year=today.year
        ).aggregate(total_sum=Sum('total_amount'))['total_sum'] or Decimal('0.00')

        # Ödenmemiş fatura sayısı (ödendi veya iptal edildi olmayanlar)
        context['odenmemis_fatura_sayisi'] = nakliyeci_faturalari.exclude(
            status__in=['PAID', 'VOID']
        ).count()
        
        # Vadesi geçmiş tahsilat sayısı (fabrika tarafından ödenmemiş ve vadesi geçmiş faturalar)
        context['vadesi_gecmis_tahsilat_sayisi'] = nakliyeci_faturalari.filter(
            due_date__lt=today
        ).exclude(status__in=['PAID', 'VOID']).count()

        # Aylık İş Hacmi (Son 6 Ay) Chart Data
        monthly_ciro_data = {}
        # Son 6 ayın etiketlerini ve başlangıç değerlerini hazırla
        for i in range(6):
            month_date = today - timedelta(days=(5-i) * 30) # En eski aydan başlayıp en yeniye doğru
            month_key = (month_date.year, month_date.month)
            monthly_ciro_data[month_key] = Decimal('0.00')

        # İlgili faturaları filtrele ve aylık toplamları al
        invoices_for_chart = nakliyeci_faturalari.filter(
            issue_date__gte=six_months_ago_start
        ).annotate(
            month_year=TruncMonth('issue_date')
        ).values('month_year').annotate(
            total=Sum('total_amount')
        ).order_by('month_year')

        for item in invoices_for_chart:
            month_key = (item['month_year'].year, item['month_year'].month)
            if month_key in monthly_ciro_data:
                monthly_ciro_data[month_key] = item['total']

        # Chart.js için verileri hazırla
        chart_labels = []
        chart_data = []
        # Ayları kronolojik sıraya göre sırala
        sorted_month_keys = sorted(monthly_ciro_data.keys())
        month_map_tr = {
            1: 'Oca', 2: 'Şub', 3: 'Mar', 4: 'Nis', 5: 'May', 6: 'Haz',
            7: 'Tem', 8: 'Ağu', 9: 'Eyl', 10: 'Eki', 11: 'Kas', 12: 'Ara'
        }

        for year, month_num in sorted_month_keys:
            month_label = f"{month_map_tr.get(month_num)} {year}"
            chart_labels.append(month_label)
            chart_data.append(float(monthly_ciro_data[(year, month_num)]))

        context['aylik_is_etiketleri'] = json.dumps(chart_labels)
        context['aylik_is_cirolari'] = json.dumps(chart_data)

        # Son Teklif Talepleri (Nakliyeci) - Last Items
        context['last_items'] = QuoteRequest.objects.filter(
            Q(status='PENDING') | Q(priced_by_shipper_company=current_company)
        ).order_by('-created_at')[:5]


    elif current_company.company_type == 'FABRIKA':
        context['is_fabrika'] = True

        # Stat Kartları
        # Gönderdiğim Bekleyen Teklif Talepleri Sayısı: Fabrikanın gönderdiği ve hala 'PENDING' durumunda olan talepler
        context['gonderdigim_bekleyen_talepler_sayisi'] = QuoteRequest.objects.filter(
            factory=current_company, status='PENDING'
        ).count()
        # Onayımı Bekleyen Teklifler Sayısı: Fabrikaya gelen ve durumu 'QUOTED' olan teklifler
        context['onayimi_bekleyen_teklifler_sayisi'] = QuoteRequest.objects.filter(
            factory=current_company, status='QUOTED'
        ).count()
        # Aktif Sevkiyatlarım Sayısı: Durumu teslim edildi, iptal edildi, faturalanmış veya tamamlanmış olmayan sevkiyatlar
        context['aktif_sevkiyatlarim_sayisi'] = Shipment.objects.filter(
            factory=current_company
        ).exclude(status__in=['DELIVERED', 'CANCELLED', 'BILLED', 'COMPLETED']).count()
        # Yaklaşan Ödeme Sayısı: Fabrikanın ödemesi gereken, vadesi bugün ile otuz gün sonrası arasında olan faturalar
        context['yaklasan_odeme_sayisi'] = Invoice.objects.filter(
            billed_to_factory=current_company,
            status__in=['SENT', 'PARTIALLY_PAID'], # Sadece gönderilmiş veya kısmen ödenmiş faturalar
            due_date__gte=today,
            due_date__lte=today + timedelta(days=30)
        ).count()

        # Bu Ay Tamamlanan Sevkiyatlar
        context['tamamlanan_sevkiyat_bu_ay_sayisi'] = Shipment.objects.filter(
            factory=current_company,
            status='DELIVERED',
            delivery_date__month=today.month,
            delivery_date__year=today.year
        ).count()

        # Finans Özeti (Fabrika için Harcama)
        fabrika_faturalari = Invoice.objects.filter(billed_to_factory=current_company)
        
        # Bu ayki toplam fatura tutarı (Fabrikanın ödemesi gereken)
        context['bu_ayki_toplam_fatura_tutari'] = fabrika_faturalari.filter(
            issue_date__month=today.month, issue_date__year=today.year
        ).aggregate(total_sum=Sum('total_amount'))['total_sum'] or Decimal('0.00')

        # Vadesi geçmiş ödeme sayısı (Fabrikanın ödemesi gereken ve vadesi geçmiş faturalar)
        context['vadesi_gecmis_odeme_sayisi'] = fabrika_faturalari.filter(
            due_date__lt=today
        ).exclude(status__in=['PAID', 'VOID']).count()

        # Aylık Harcama Hacmi (Son 6 Ay) Chart Data
        monthly_harcama_data = {}
        for i in range(6):
            month_date = today - timedelta(days=(5-i) * 30)
            month_key = (month_date.year, month_date.month)
            monthly_harcama_data[month_key] = Decimal('0.00')

        invoices_for_chart = fabrika_faturalari.filter(
            issue_date__gte=six_months_ago_start
        ).annotate(
            month_year=TruncMonth('issue_date')
        ).values('month_year').annotate(
            total=Sum('total_amount')
        ).order_by('month_year')

        for item in invoices_for_chart:
            month_key = (item['month_year'].year, item['month_year'].month)
            if month_key in monthly_harcama_data:
                monthly_harcama_data[month_key] = item['total']

        chart_labels = []
        chart_data = []
        sorted_month_keys = sorted(monthly_harcama_data.keys())
        month_map_tr = {
            1: 'Oca', 2: 'Şub', 3: 'Mar', 4: 'Nis', 5: 'May', 6: 'Haz',
            7: 'Tem', 8: 'Ağu', 9: 'Eyl', 10: 'Eki', 11: 'Kas', 12: 'Ara'
        }

        for year, month_num in sorted_month_keys:
            month_label = f"{month_map_tr.get(month_num)} {year}"
            chart_labels.append(month_label)
            chart_data.append(float(monthly_harcama_data[(year, month_num)]))

        context['aylik_is_etiketleri'] = json.dumps(chart_labels)
        context['aylik_is_cirolari'] = json.dumps(chart_data)

        # Son Faturalar (Fabrika) - Last Items
        last_invoices = Invoice.objects.filter(billed_to_factory=current_company).order_by('-issue_date')[:5]
        for invoice in last_invoices:
            invoice.is_overdue = invoice.due_date < today and not invoice.status in ['PAID', 'VOID']
            invoice.is_due_soon = not invoice.status in ['PAID', 'VOID'] and today <= invoice.due_date <= seven_days_later
        context['last_items'] = last_invoices


    return render(request, 'ana_uygulama/dashboard.html', context)


# === Shipper Views ===

# Shipper - Quote Management
@login_required
def quote_request_list_nakliyeci_view(request):
    """
    Lists quote requests for users with the 'NAKLIYECI' (Shipper) role.
    Includes pending, quoted, accepted, and rejected quotes.
    """
    if not request.user.company or request.user.company.company_type != 'NAKLIYECI':
        messages.error(request, "Bu sayfaya erişim izniniz yok.")
        return redirect('ana_uygulama:dashboard')

    current_shipper_company = request.user.company

    # Get filtering parameters
    status_filter = request.GET.get('status', '') # Status filter
    factory_search = request.GET.get('factory_search', '') # Factory search
    date_from_filter = request.GET.get('date_from', '')
    date_to_filter = request.GET.get('date_to', '')

    # Base query: Quotes that the shipper can quote or has already quoted
    quote_requests = QuoteRequest.objects.filter(
        Q(status='PENDING') | # Pending requests (not yet quoted by anyone)
        Q(priced_by_shipper_company=current_shipper_company) # All requests quoted by this shipper
    ).select_related('factory', 'created_by_user', 'priced_by_shipper_company').distinct().order_by('-created_at')

    if status_filter:
        quote_requests = quote_requests.filter(status=status_filter)

    if factory_search:
        quote_requests = quote_requests.filter(factory__name__icontains=factory_search)

    if date_from_filter:
        try:
            date_from = timezone.datetime.strptime(date_from_filter, "%Y-%m-%d").date()
            quote_requests = quote_requests.filter(requested_pickup_date__gte=date_from)
        except ValueError:
            messages.warning(request, "Geçersiz başlangıç tarihi formatı.")

    if date_to_filter:
        try:
            date_to = timezone.datetime.strptime(date_to_filter, "%Y-%m-%d").date()
            quote_requests = quote_requests.filter(requested_pickup_date__lte=date_to)
        except ValueError:
            messages.warning(request, "Geçersiz bitiş tarihi formatı.")

    context = {
        'quote_requests': quote_requests,
        'page_title': "Fiyat Teklifi İstekleri",
        'status_choices': QuoteRequest.STATUS_CHOICES, # For filter in template
        'current_status_filter': status_filter,
        'current_factory_search': factory_search,
        'current_date_from': date_from_filter,
        'current_date_to': date_to_filter,
    }
    return render(request, 'ana_uygulama/nakliyeci/quote_request_list.html', context)


@login_required
def create_quote_for_request_view(request, quote_id):
    """
    View for the shipper to provide a price for a specific quote request.
    """
    quote_request = get_object_or_404(QuoteRequest, pk=quote_id)
    # Check if the quote is pending and either not priced yet or priced by the current shipper
    if quote_request.status != 'PENDING' and \
       not (quote_request.status == 'QUOTED' and quote_request.priced_by_shipper_company == request.user.company):
        messages.error(request, "Bu teklif talebi fiyatlandırılamaz veya zaten işleme alınmıştır.")
        return redirect('ana_uygulama:quote_request_list_nakliyeci')

    if request.method == 'POST':
        form = OfferPriceForm(request.POST, instance=quote_request)
        if form.is_valid():
            quote_request.offered_price = form.cleaned_data['offered_price'] # Use 'offered_price' from OfferPriceForm
            quote_request.shipper_notes = form.cleaned_data['shipper_notes'] # Get shipper notes
            quote_request.priced_by_shipper_company = request.user.company
            quote_request.status = 'QUOTED'
            quote_request.save()
            messages.success(request, f"Teklif Talebi #{quote_request.pk} için fiyat başarıyla gönderildi.")
            return redirect('ana_uygulama:quote_request_list_nakliyeci')
        else:
            messages.error(request, "Lütfen formdaki hataları düzeltin.")
    else:
        form = OfferPriceForm(instance=quote_request)

    context = {
        'form': form,
        'quote_request': quote_request,
        'page_title': f'Teklif: #{quote_request.pk}'
    }
    return render(request, 'ana_uygulama/nakliyeci/create_quote_for_request.html', context)

@login_required
def update_quote_for_request_view(request, quote_id):
    """
    View for the shipper to update a previously submitted quote.
    """
    quote_request = get_object_or_404(QuoteRequest, pk=quote_id)
    if quote_request.priced_by_shipper_company != request.user.company or quote_request.status != 'QUOTED':
        messages.error(request, "Bu teklifi güncelleme izniniz yok veya durumu uygun değil.")
        return redirect('ana_uygulama:quote_request_list_nakliyeci')

    if request.method == 'POST':
        form = OfferPriceForm(request.POST, instance=quote_request)
        if form.is_valid():
            quote_request.offered_price = form.cleaned_data['offered_price']
            quote_request.shipper_notes = form.cleaned_data['shipper_notes']
            quote_request.save()
            messages.success(request, f"Teklif Talebi #{quote_request.pk} için fiyat başarıyla güncellendi.")
            return redirect('ana_uygulama:quote_request_list_nakliyeci')
    else:
        form = OfferPriceForm(instance=quote_request)

    context = {
        'form': form,
        'quote_request': quote_request,
        'page_title': f'Teklifi Güncelle: #{quote_request.pk}'
    }
    return render(request, 'ana_uygulama/nakliyeci/update_quote_for_request.html', context)


@login_required
def quote_request_detail_nakliyeci_view(request, pk):
    """
    Displays the details of a specific quote request for the shipper role.
    """
    if not request.user.company or request.user.company.company_type != 'NAKLIYECI':
        messages.error(request, "Bu sayfaya erişim izniniz yok.")
        return redirect('ana_uygulama:dashboard')

    quote_request = get_object_or_404(
        QuoteRequest.objects.select_related('factory', 'created_by_user', 'priced_by_shipper_company'),
        pk=pk
    )

    # Security: Only the shipper who priced this quote, or all shippers if still pending, can view.
    # Or if the quote has been accepted and the shipper managing the job is this user.
    if quote_request.status != 'PENDING' and \
       quote_request.priced_by_shipper_company != request.user.company:
        messages.error(request, "Bu teklif detaylarını görüntüleme izniniz yok.")
        return redirect('ana_uygulama:quote_request_list_nakliyeci')

    related_shipment = None
    if quote_request.status in ['ACCEPTED', 'COMPLETED']:
        try:
            # Check if there is a related shipment
            related_shipment = getattr(quote_request, 'shipment', None)
        except Shipment.DoesNotExist:
            related_shipment = None

    context = {
        'quote_request': quote_request,
        'related_shipment': related_shipment,
        'page_title': f"Teklif Talebi Detayı #{quote_request.pk}"
    }
    return render(request, 'ana_uygulama/nakliyeci/quote_request_detail.html', context)

@login_required
def quote_request_create_nakliyeci_view(request):
    messages.error(request, "Nakliyeciler teklif talebi oluşturamaz; sadece fabrika kullanıcıları oluşturabilir.")
    return redirect('ana_uygulama:dashboard')

@login_required
def quote_request_update_nakliyeci_view(request, pk):
    messages.error(request, "Nakliyeciler teklif taleplerini güncelleyemez.")
    return redirect('ana_uygulama:dashboard')

@login_required
def quote_request_delete_nakliyeci_view(request, pk):
    messages.error(request, "Nakliyeciler teklif taleplerini silemez.")
    return redirect('ana_uygulama:dashboard')


# Shipper - Shipment (Job) Management
@login_required
def shipment_list_nakliyeci_view(request):
    """
    Lists shipments belonging to the shipper's company.
    Offers status and other filtering options.
    """
    if not request.user.company or request.user.company.company_type != 'NAKLIYECI':
        messages.error(request, "Bu sayfaya erişim izniniz yok.")
        return redirect('ana_uygulama:dashboard')

    base_queryset = Shipment.objects.filter(
        shipper_company=request.user.company
    ).select_related('factory', 'assigned_vehicle', 'quote_request').order_by('-created_at')

    status_filter = request.GET.get('status')
    page_title_suffix = ""
    status_display_name = ""

    if status_filter:
        valid_statuses = [choice[0] for choice in Shipment.STATUS_CHOICES]
        if status_filter in valid_statuses:
            base_queryset = base_queryset.filter(status=status_filter)
            status_display_name = dict(Shipment.STATUS_CHOICES).get(status_filter)
            page_title_suffix = f" ({status_display_name})"
        else:
            messages.warning(request, "Geçersiz durum filtresi.")
            status_display_name = "Bilinmiyor (Geçersiz Filtre)"

    shipments = base_queryset

    context = {
        'shipments': shipments,
        'page_title': f"İşlerim{page_title_suffix}",
        'thirty_days_later': timezone.now().date() + timedelta(days=30),
        'current_status_filter': status_filter,
        'status_display_name_for_filter': status_display_name,
        'status_choices': Shipment.STATUS_CHOICES, # For filter in template
    }
    return render(request, 'ana_uygulama/nakliyeci/shipment_list.html', context)

@login_required
def shipment_create_nakliyeci_view(request):
    """
    View for the shipper to manually create a new shipment.
    """
    if not request.user.company or request.user.company.company_type != 'NAKLIYECI':
        messages.error(request, "Bu sayfaya erişim izniniz yok.")
        return redirect('ana_uygulama:dashboard')

    current_shipper_company = request.user.company
    if request.method == 'POST':
        form = ShipmentFormNakliyeci(request.POST, request.FILES, request_user_company=current_shipper_company)
        if form.is_valid():
            shipment = form.save(commit=False)
            shipment.shipper_company = current_shipper_company
            shipment.created_by_user = request.user
            # Vehicle warnings
            assigned_vehicle = form.cleaned_data.get('assigned_vehicle')
            if assigned_vehicle:
                warning_messages = []
                if assigned_vehicle.is_inspection_expired():
                    warning_messages.append(f"{assigned_vehicle.plate_number} muayenesi SÜRESİ DOLDU.")
                elif assigned_vehicle.inspection_expiry_date and assigned_vehicle.inspection_expiry_date < (timezone.now().date() + timedelta(days=7)):
                    warning_messages.append(f"{assigned_vehicle.plate_number} muayenesi YAKINDA DOLUYOR.")
                if assigned_vehicle.is_insurance_expired():
                    warning_messages.append(f"{assigned_vehicle.plate_number} sigortası SÜRESİ DOLDU.")
                elif assigned_vehicle.insurance_expiry_date and assigned_vehicle.insurance_expiry_date < (timezone.now().date() + timedelta(days=7)):
                    warning_messages.append(f"{assigned_vehicle.plate_number} sigortası YAKINDA DOLUYOR.")

                if warning_messages:
                    for warning in warning_messages: messages.warning(request, warning + " Atama yine de yapıldı.")
            try:
                shipment.save()
                messages.success(request, f"Yeni iş (Sevkiyat ID: {shipment.id}) başarıyla oluşturuldu.")
                return redirect('ana_uygulama:shipment_list_nakliyeci_view')
            except Exception as e:
                messages.error(request, f"İş oluşturulurken bir hata oluştu: {e}")
        else:
            messages.error(request, "Lütfen formdaki hataları düzeltin.")
    else:
        form = ShipmentFormNakliyeci(request_user_company=current_shipper_company)

    context = {'form': form, 'page_title': "Manuel Yeni İş Girişi"}
    return render(request, 'ana_uygulama/nakliyeci/shipment_form.html', context)

@login_required
def shipment_create_from_quote_nakliyeci_view(request, quote_id):
    """
    View for the shipper to create a shipment from a factory-accepted quote.
    """
    if not request.user.company or request.user.company.company_type != 'NAKLIYECI':
        messages.error(request, "Bu sayfaya erişim izniniz yok.")
        return redirect('ana_uygulama:dashboard')

    quote_request = get_object_or_404(QuoteRequest, id=quote_id)
    if quote_request.status != 'ACCEPTED':
        messages.error(request, "Bu teklif henüz kabul edilmedi veya zaten bir işe dönüştürüldü.")
        return redirect('ana_uygulama:quote_request_list_nakliyeci')
    if Shipment.objects.filter(quote_request=quote_request).exists():
        messages.warning(request, f"Teklif #{quote_request.id} zaten bir işe dönüştürüldü.")
        return redirect('ana_uygulama:shipment_list_nakliyeci_view')
    if not quote_request.priced_by_shipper_company:
        messages.error(request, "HATA: Teklifi fiyatlandıran nakliyeci bilgisi eksik. İş oluşturulamadı.")
        return redirect('ana_uygulama:quote_request_list_nakliyeci')
    if quote_request.priced_by_shipper_company != request.user.company:
        messages.error(request, "Sadece fiyatı veren nakliyeci bu teklifi bir işe dönüştürebilir.")
        return redirect('ana_uygulama:quote_request_list_nakliyeci')

    try:
        new_shipment = Shipment.objects.create(
            quote_request=quote_request,
            factory=quote_request.factory,
            shipper_company=quote_request.priced_by_shipper_company,
            origin=quote_request.origin,
            destination=quote_request.destination,
            load_description=quote_request.load_description,
            weight=quote_request.weight,
            volume=quote_request.volume,
            pickup_date=quote_request.requested_pickup_date,
            price_for_factory=quote_request.offered_price,
            status='PENDING_ASSIGNMENT',
            created_by_user=request.user
        )
        quote_request.status = 'COMPLETED'
        quote_request.save()
        messages.success(request, f"Teklif #{quote_request.id} yeni işe dönüştürüldü, ID:{new_shipment.id}.")
        return redirect('ana_uygulama:shipment_detail_nakliyeci_view', shipment_id=new_shipment.id)
    except Exception as e:
        messages.error(request, f"Teklif işe dönüştürülürken bir hata oluştu: {e}")
        return redirect('ana_uygulama:quote_request_list_nakliyeci')

@login_required
def shipment_detail_nakliyeci_view(request, shipment_id):
    """
    Displays the details of a shipment belonging to the shipper's company.
    """
    if not request.user.company or request.user.company.company_type != 'NAKLIYECI':
        messages.error(request, "Bu sayfaya erişim izniniz yok.")
        return redirect('ana_uygulama:dashboard')

    shipment = get_object_or_404(
        Shipment.objects.select_related('factory', 'assigned_vehicle', 'quote_request', 'created_by_user'),
        id=shipment_id, shipper_company=request.user.company
    )
    status_update_form = ShipmentStatusUpdateForm(instance=shipment)
    thirty_days_later = timezone.now().date() + timedelta(days=30)
    context = {
        'shipment': shipment,
        'page_title': f"İş Detayı",
        'status_update_form': status_update_form,
        'thirty_days_later': thirty_days_later
    }
    return render(request, 'ana_uygulama/nakliyeci/shipment_detail.html', context)


@login_required
def shipment_update_nakliyeci_view(request, shipment_id):
    """
    View for the shipper to update shipment information.
    """
    if not request.user.company or request.user.company.company_type != 'NAKLIYECI':
        messages.error(request, "Bu sayfaya erişim izniniz yok.")
        return redirect('ana_uygulama:dashboard')

    current_shipper_company = request.user.company
    shipment_to_update = get_object_or_404(Shipment, id=shipment_id, shipper_company=current_shipper_company)

    if shipment_to_update.status in ['DELIVERED', 'BILLED', 'CANCELLED', 'COMPLETED']:
        messages.error(request, f"İş (ID: {shipment_to_update.id}) durumu '{shipment_to_update.get_status_display()}' olduğu için düzenlenemez.")
        return redirect('ana_uygulama:shipment_detail_nakliyeci_view', shipment_id=shipment_id)

    if request.method == 'POST':
        form = ShipmentFormNakliyeci(request.POST, request.FILES, instance=shipment_to_update, request_user_company=current_shipper_company)
        if form.is_valid():
            updated_shipment = form.save(commit=False)
            assigned_vehicle = form.cleaned_data.get('assigned_vehicle')
            if assigned_vehicle:
                warning_messages = []
                if assigned_vehicle.is_inspection_expired():
                    warning_messages.append(f"{assigned_vehicle.plate_number} muayenesi SÜRESİ DOLDU.")
                elif assigned_vehicle.inspection_expiry_date and assigned_vehicle.inspection_expiry_date < (timezone.now().date() + timedelta(days=7)):
                    warning_messages.append(f"{assigned_vehicle.plate_number} muayenesi YAKINDA DOLUYOR.")
                if assigned_vehicle.is_insurance_expired():
                    warning_messages.append(f"{assigned_vehicle.plate_number} sigortası SÜRESİ DOLDU.")
                elif assigned_vehicle.insurance_expiry_date and assigned_vehicle.insurance_expiry_date < (timezone.now().date() + timedelta(days=7)):
                    warning_messages.append(f"{assigned_vehicle.plate_number} sigortası YAKINDA DOLUYOR.")

                if warning_messages:
                    for warning in warning_messages: messages.warning(request, warning + " Araç bilgileri yine de güncellendi.")
            try:
                updated_shipment.save()
                messages.success(request, f"İş (Sevkiyat ID: {updated_shipment.id}) başarıyla güncellendi.")
                return redirect('ana_uygulama:shipment_detail_nakliyeci_view', shipment_id=updated_shipment.id)
            except Exception as e:
                messages.error(request, f"İş güncellenirken bir hata oluştu: {e}")
        else:
            messages.error(request, "Lütfen formdaki hataları düzeltin.")
    else:
        form = ShipmentFormNakliyeci(instance=shipment_to_update, request_user_company=current_shipper_company)

    context = {
        'form': form,
        'shipment': shipment_to_update,
        'page_title': f"İşi Düzenle: Sevkiyat #{shipment_to_update.id}"
    }
    return render(request, 'ana_uygulama/nakliyeci/shipment_form.html', context)


@login_required
def shipment_delete_nakliyeci_view(request, shipment_id):
    """
    View for the shipper to delete a shipment belonging to their company.
    """
    shipment = get_object_or_404(Shipment, pk=shipment_id)
    if shipment.shipper_company != request.user.company and not request.user.is_superuser:
        messages.error(request, "Bu sevkiyatı silme izniniz yok.")
        return redirect('ana_uygulama:shipment_list_nakliyeci_view')

    if request.method == 'POST':
        shipment.delete()
        messages.success(request, "Sevkiyat başarıyla silindi.")
        return redirect('ana_uygulama:shipment_list_nakliyeci_view')

    context = {
        'shipment': shipment,
        'page_title': f'Sevkiyatı Sil #{shipment.pk}'
    }
    return render(request, 'ana_uygulama/nakliyeci/shipment_confirm_delete.html', context)

@login_required
def assign_vehicle_to_shipment_view(request, shipment_id):
    """
    View for the shipper to assign or change a vehicle for a shipment.
    Also handles unassigning a vehicle.
    """
    if not request.user.company or request.user.company.company_type != 'NAKLIYECI':
        messages.error(request, "Bu sayfaya erişim izniniz yok.")
        return redirect('ana_uygulama:dashboard')
    
    shipment = get_object_or_404(Shipment, id=shipment_id, shipper_company=request.user.company)
    
    # Check if the shipment status allows vehicle assignment/unassignment
    if shipment.status not in ['PENDING_ASSIGNMENT', 'ASSIGNED', 'IN_TRANSIT']:
        messages.error(request, f"Bu iş için araç atama/boşa alma yapılamaz. Durum: {shipment.get_status_display()}")
        return redirect('ana_uygulama:shipment_detail_nakliyeci_view', shipment_id=shipment.id)

    current_shipper_company = request.user.company

    if request.method == 'POST':
        action = request.POST.get('action') # Get the action from the submitted form

        if action == 'unassign':
            # Handle unassigning the vehicle
            if shipment.assigned_vehicle:
                shipment.assigned_vehicle = None
                # If the shipment was assigned or in transit, set to PENDING_ASSIGNMENT
                if shipment.status in ['ASSIGNED', 'IN_TRANSIT']:
                    shipment.status = 'PENDING_ASSIGNMENT'
                shipment.save()
                messages.success(request, f"İş #{shipment.id} için araç ataması başarıyla kaldırıldı ve durum 'Atama Bekliyor' olarak güncellendi.")
            else:
                messages.info(request, "Bu iş zaten bir araca atanmamış.")
            return redirect('ana_uygulama:shipment_detail_nakliyeci_view', shipment_id=shipment.id)

        elif action == 'assign':
            # Handle assigning/changing the vehicle
            form = AssignVehicleForm(request.POST, request_user_company=current_shipper_company)
            if form.is_valid():
                selected_vehicle = form.cleaned_data['assigned_vehicle']
                
                # Check for vehicle warnings before assignment
                warning_messages = []
                if selected_vehicle.is_inspection_expired():
                    warning_messages.append(f"{selected_vehicle.plate_number} muayenesi SÜRESİ DOLDU.")
                elif selected_vehicle.inspection_expiry_date and selected_vehicle.inspection_expiry_date < (timezone.now().date() + timedelta(days=7)):
                    warning_messages.append(f"{selected_vehicle.plate_number} muayenesi YAKLAŞIYOR.")
                if selected_vehicle.is_insurance_expired():
                    warning_messages.append(f"{selected_vehicle.plate_number} sigortası SÜRESİ DOLDU.")
                elif selected_vehicle.insurance_expiry_date and selected_vehicle.insurance_expiry_date < (timezone.now().date() + timedelta(days=7)):
                    warning_messages.append(f"{selected_vehicle.plate_number} sigortası YAKLAŞIYOR.")

                if warning_messages:
                    for warning in warning_messages: messages.warning(request, warning + " Araç yine de atandı.")

                shipment.assigned_vehicle = selected_vehicle
                # If shipment is currently pending assignment, change status to ASSIGNED
                if shipment.status == 'PENDING_ASSIGNMENT':
                    shipment.status = 'ASSIGNED'
                shipment.save()
                messages.success(request, f"İş #{shipment.id} araca {selected_vehicle.plate_number} atandı.")
                return redirect('ana_uygulama:shipment_detail_nakliyeci_view', shipment_id=shipment.id)
            else:
                messages.error(request, "Lütfen geçerli bir araç seçin.")
        
        # If action is not 'assign' or 'unassign', or form is not valid for 'assign'
        # re-render the form with errors or current state
        initial_data = {'assigned_vehicle': shipment.assigned_vehicle.id if shipment.assigned_vehicle else None}
        form = AssignVehicleForm(initial=initial_data, request_user_company=current_shipper_company)
        context = {'form': form, 'shipment': shipment, 'page_title': f"İş #{shipment.id} için Araç Ata/Değiştir"}
        return render(request, 'ana_uygulama/nakliyeci/assign_vehicle_form.html', context)


    else: # GET request
        initial_data = {'assigned_vehicle': shipment.assigned_vehicle.id if shipment.assigned_vehicle else None}
        form = AssignVehicleForm(initial=initial_data, request_user_company=current_shipper_company)
    
    context = {'form': form, 'shipment': shipment, 'page_title': f"İş #{shipment.id} için Araç Ata/Değiştir"}
    return render(request, 'ana_uygulama/nakliyeci/assign_vehicle_form.html', context)


@login_required
def update_shipment_status_nakliyeci_view(request, shipment_id):
    """
    View for the shipper to update the status of a shipment.
    """
    if not request.user.company or request.user.company.company_type != 'NAKLIYECI':
        messages.error(request, "Bu sayfaya erişim izniniz yok.")
        return redirect('ana_uygulama:dashboard')
    shipment = get_object_or_404(Shipment, id=shipment_id, shipper_company=request.user.company)
    if shipment.status in ['BILLED', 'CANCELLED', 'COMPLETED']:
        messages.error(request, f"Durumu '{shipment.get_status_display()}' olan bir işin durumu değiştirilemez.")
        return redirect('ana_uygulama:shipment_detail_nakliyeci_view', shipment_id=shipment.id)

    if request.method == 'POST':
        form = ShipmentStatusUpdateForm(request.POST, instance=shipment)
        if form.is_valid():
            new_status = form.cleaned_data['status']
            if new_status == 'DELIVERED' and not shipment.delivery_date:
                shipment.delivery_date = timezone.now().date()
            shipment.status = new_status
            shipment.save()
            messages.success(request, f"İş #{shipment.id} durumu '{shipment.get_status_display()}' olarak güncellendi.")
        else:
            for field, errors in form.errors.items():
                for error in errors: messages.error(request, f"{form.fields[field].label}: {error}")
    return redirect('ana_uygulama:shipment_detail_nakliyeci_view', shipment_id=shipment.id)


# Shipper - Vehicle Management
@login_required
def vehicle_list_nakliyeci_view(request):
    """
    Lists vehicles belonging to carriers managed by the shipper's company.
    """
    if not request.user.company or request.user.company.company_type != 'NAKLIYECI':
        messages.error(request, "Bu sayfaya erişim izniniz yok.")
        return redirect('ana_uygulama:dashboard')

    vehicles = Vehicle.objects.filter(
        carrier__managed_by_shipper=request.user.company
    ).select_related('carrier').order_by('plate_number')

    thirty_days_later = timezone.now().date() + timedelta(days=30)
    context = {
        'vehicles': vehicles,
        'page_title': "Araçlar",
        'thirty_days_later': thirty_days_later,
    }
    return render(request, 'ana_uygulama/nakliyeci/vehicle_list.html', context)

@login_required
def vehicle_create_nakliyeci_view(request):
    """
    View for the shipper to add a new vehicle.
    Can optionally be linked to a specific carrier.
    """
    if not hasattr(request.user, 'company') or request.user.company.company_type != 'NAKLIYECI':
        messages.error(request, "Bu sayfaya erişim izniniz yok.")
        return redirect('ana_uygulama:dashboard')

    current_nakliyeci_company = request.user.company
    initial_data = {}

    carrier_id_to_use = request.resolver_match.kwargs.get('carrier_id') or request.GET.get('carrier_id')

    selected_carrier = None
    if carrier_id_to_use:
        try:
            selected_carrier = Carrier.objects.get(id=carrier_id_to_use, managed_by_shipper=current_nakliyeci_company)
            initial_data['carrier'] = selected_carrier.id
        except (Carrier.DoesNotExist, ValueError):
            messages.warning(request, "Belirtilen taşıyıcı bulunamadı veya izniniz yok.")


    if request.method == 'POST':
        form = VehicleForm(request.POST, request.FILES, request_user_company=current_nakliyeci_company)
        if form.is_valid():
            vehicle = form.save(commit=False)
            try:
                vehicle.save()
                messages.success(request, f"Plaka numarası {vehicle.plate_number} olan araç başarıyla eklendi.")
                if selected_carrier:
                    return redirect('ana_uygulama:carrier_detail_nakliyeci_view', pk=selected_carrier.pk)
                else:
                    return redirect('ana_uygulama:vehicle_list_nakliyeci_view')
            except Exception as e:
                messages.error(request, f"Araç eklenirken bir hata oluştu: {e}.")
        else:
            messages.error(request, "Lütfen formdaki hataları düzeltin.")
    else:
        form = VehicleForm(request_user_company=current_nakliyeci_company, initial=initial_data)

    context = {
        'form': form,
        'page_title': "Yeni Araç Ekle",
        'selected_carrier': selected_carrier,
    }
    return render(request, 'ana_uygulama/nakliyeci/vehicle_form.html', context)

@login_required
def vehicle_detail_nakliyeci_view(request, vehicle_id):
    """
    Displays the details of a specific vehicle for the shipper role.
    """
    if not request.user.company or request.user.company.company_type != 'NAKLIYECI':
        messages.error(request, "Bu sayfaya erişim izniniz yok.")
        return redirect('ana_uygulama:dashboard')

    vehicle = get_object_or_404(
        Vehicle.objects.select_related('carrier', 'carrier__managed_by_shipper'),
        id=vehicle_id,
        carrier__managed_by_shipper=request.user.company
    )
    context = {
        'vehicle': vehicle,
        'page_title': f"Araç Detayı: {vehicle.plate_number}"
    }
    return render(request, 'ana_uygulama/nakliyeci/vehicle_detail.html', context)


@login_required
def vehicle_update_nakliyeci_view(request, vehicle_id):
    """
    View for the shipper to update vehicle information.
    """
    if not request.user.company or request.user.company.company_type != 'NAKLIYECI':
        messages.error(request, "Bu sayfaya erişim izniniz yok.")
        return redirect('ana_uygulama:dashboard')

    current_nakliyeci_company = request.user.company
    vehicle_to_update = get_object_or_404(Vehicle, id=vehicle_id, carrier__managed_by_shipper=current_nakliyeci_company)

    if request.method == 'POST':
        form = VehicleForm(request.POST, request.FILES, instance=vehicle_to_update, request_user_company=current_nakliyeci_company)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, f"Araç {vehicle_to_update.plate_number} başarıyla güncellendi.")
                return redirect('ana_uygulama:vehicle_list_nakliyeci_view')
            except Exception as e:
                messages.error(request, f"Araç güncellenirken bir hata oluştu: {e}.")
        else:
            messages.error(request, "Lütfen formdaki hataları düzeltin.")
    else:
        form = VehicleForm(instance=vehicle_to_update, request_user_company=current_nakliyeci_company)

    context = {
        'form': form,
        'vehicle': vehicle_to_update,
        'page_title': f"Aracı Düzenle: {vehicle_to_update.plate_number}"
    }
    return render(request, 'ana_uygulama/nakliyeci/vehicle_form.html', context)


@login_required
def vehicle_delete_nakliyeci_view(request, vehicle_id):
    """
    View for the shipper to delete a vehicle.
    """
    vehicle = get_object_or_404(Vehicle, pk=vehicle_id)
    if vehicle.carrier.managed_by_shipper != request.user.company and not request.user.is_superuser:
        messages.error(request, "Bu aracı silme izniniz yok.")
        return redirect('ana_uygulama:vehicle_list_nakliyeci_view')

    # Before deleting the vehicle, check if it's assigned to any active shipments.
    # If so, prevent deletion and advise to unassign first.
    active_shipments = Shipment.objects.filter(
        assigned_vehicle=vehicle,
        status__in=['PENDING_ASSIGNMENT', 'ASSIGNED', 'IN_TRANSIT']
    ).count()

    if active_shipments > 0:
        messages.error(request, f"Bu araç {active_shipments} adet aktif işe atanmış durumda. Aracı silmeden önce lütfen tüm işlerden boşa alın.")
        return redirect('ana_uygulama:vehicle_detail_nakliyeci_view', vehicle_id=vehicle.pk)


    if request.method == 'POST':
        vehicle.delete()
        messages.success(request, f"Araç {vehicle.plate_number} başarıyla silindi.")
        return redirect('ana_uygulama:vehicle_list_nakliyeci_view')

    context = {
        'vehicle': vehicle,
        'page_title': f'Aracı Sil {vehicle.plate_number}'
    }
    return render(request, 'ana_uygulama/nakliyeci/vehicle_confirm_delete.html', context)


# Shipper - Carrier Management
@login_required
def carrier_list_nakliyeci_view(request):
    """
    Lists carriers managed by the shipper's company.
    """
    if not request.user.company or request.user.company.company_type != 'NAKLIYECI':
        messages.error(request, "Bu sayfaya erişim izniniz yok.")
        return redirect('ana_uygulama:dashboard')

    carriers = Carrier.objects.filter(managed_by_shipper=request.user.company).order_by('full_name')

    context = {
        'carriers': carriers,
        'page_title': "Taşıyıcılar"
    }
    return render(request, 'ana_uygulama/nakliyeci/carrier_list.html', context)

@login_required
def carrier_create_nakliyeci_view(request):
    """
    View for the shipper to add a new carrier.
    """
    if not request.user.company or request.user.company.company_type != 'NAKLIYECI':
        messages.error(request, "Bu sayfaya erişim izniniz yok.")
        return redirect('ana_uygulama:dashboard')

    if request.method == 'POST':
        form = CarrierForm(request.POST, request.FILES) # request.FILES for document uploads
        if form.is_valid():
            carrier = form.save(commit=False)
            carrier.managed_by_shipper = request.user.company
            try:
                carrier.save()
                messages.success(request, f"Taşıyıcı '{carrier.full_name}' başarıyla eklendi.")
                return redirect('ana_uygulama:carrier_list_nakliyeci_view')
            except Exception as e:
                messages.error(request, f"Taşıyıcı eklenirken bir hata oluştu: {e}")
        else:
            messages.error(request, "Lütfen formdaki hataları düzeltin.")
    else:
        form = CarrierForm()

    context = {
        'form': form,
        'page_title': "Yeni Taşıyıcı (Araç Sahibi) Ekle"
    }
    return render(request, 'ana_uygulama/nakliyeci/carrier_form.html', context)


@login_required
def carrier_detail_nakliyeci_view(request, pk):
    """
    View for the shipper to display details of a specific carrier.
    """
    if not request.user.company or request.user.company.company_type != 'NAKLIYECI':
        messages.error(request, "Bu sayfaya erişim izniniz yok.")
        return redirect('ana_uygulama:dashboard')

    carrier = get_object_or_404(Carrier, pk=pk, managed_by_shipper=request.user.company)
    vehicles_of_carrier = Vehicle.objects.filter(carrier=carrier)
    bank_accounts_of_carrier = BankAccount.objects.filter(carrier=carrier)

    # Buraya ekleyin:
    today = timezone.now().date()
    seven_days_later = today + timedelta(days=7) # Şablonda kullanacağınız güncel tarih

    context = {
        'carrier': carrier,
        'vehicles_of_carrier': vehicles_of_carrier,
        'bank_accounts_of_carrier': bank_accounts_of_carrier,
        'page_title': f"Taşıyıcı Detayı: {carrier.full_name}",
        'today': today,                 # Şablonda kullanmak için bugün
        'seven_days_later': seven_days_later, # Şablonda kullanmak için 7 gün sonrası
    }
    return render(request, 'ana_uygulama/nakliyeci/carrier_detail.html', context)


@login_required
def carrier_update_nakliyeci_view(request, pk):
    """
    View for the shipper to update carrier information.
    """
    if not request.user.company or request.user.company.company_type != 'NAKLIYECI':
        messages.error(request, "Bu sayfaya erişim izniniz yok.")
        return redirect('ana_uygulama:dashboard')

    carrier_to_update = get_object_or_404(Carrier, pk=pk, managed_by_shipper=request.user.company)

    if request.method == 'POST':
        form = CarrierForm(request.POST, request.FILES, instance=carrier_to_update)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, f"Taşıyıcı '{carrier_to_update.full_name}' başarıyla güncellendi.")
                return redirect('ana_uygulama:carrier_detail_nakliyeci_view', pk=carrier_to_update.pk)
            except Exception as e:
                messages.error(request, f"Taşıyıcı güncellenirken bir hata oluştu: {e}")
        else:
            messages.error(request, "Lütfen formdaki hataları düzeltin.")
    else:
        form = CarrierForm(instance=carrier_to_update)

    context = {
        'form': form,
        'carrier': carrier_to_update,
        'page_title': f"Taşıyıcıyı Düzenle: {carrier_to_update.full_name}"
    }
    return render(request, 'ana_uygulama/nakliyeci/carrier_form.html', context)


@login_required
def carrier_delete_nakliyeci_view(request, pk):
    """
    View for the shipper to delete a carrier.
    """
    carrier = get_object_or_404(Carrier, pk=pk)
    if carrier.managed_by_shipper != request.user.company and not request.user.is_superuser:
        messages.error(request, "Bu taşıyıcıyı silme izniniz yok.")
        return redirect('ana_uygulama:carrier_list_nakliyeci_view')

    # Check if this carrier has any vehicles assigned to active shipments
    vehicles_with_active_shipments = Vehicle.objects.filter(
        carrier=carrier,
        assigned_shipments__status__in=['PENDING_ASSIGNMENT', 'ASSIGNED', 'IN_TRANSIT']
    ).distinct().count()

    if vehicles_with_active_shipments > 0:
        messages.error(request, f"Bu taşıyıcının {vehicles_with_active_shipments} adet aracı aktif işlere atanmış durumda. Taşıyıcıyı silmeden önce tüm araçlarını aktif işlerden boşa alın.")
        return redirect('ana_uygulama:carrier_detail_nakliyeci_view', pk=carrier.pk)


    if request.method == 'POST':
        carrier.delete()
        messages.success(request, f"Taşıyıcı {carrier.full_name} başarıyla silindi.")
        return redirect('ana_uygulama:carrier_list_nakliyeci_view')

    context = {
        'carrier': carrier,
        'page_title': f'Taşıyıcıyı Sil {carrier.full_name}'
    }
    return render(request, 'ana_uygulama/nakliyeci/carrier_confirm_delete.html', context)


@login_required
def carrier_bank_account_add_view(request, carrier_id):
    """
    View to add a bank account to a specific carrier.
    """
    if not request.user.company or request.user.company.company_type != 'NAKLIYECI':
        messages.error(request, "Yetkisiz erişim.")
        return redirect('ana_uygulama:dashboard')
    carrier = get_object_or_404(Carrier, id=carrier_id, managed_by_shipper=request.user.company)

    if request.method == 'POST':
        form = BankAccountForm(request.POST) # request_user'ı burada geçirmeye gerek yok
        if form.is_valid():
            bank_account = form.save(commit=False)
            bank_account.carrier = carrier
            bank_account.save()
            messages.success(request, "Banka hesabı başarıyla eklendi.")
            return redirect('ana_uygulama:carrier_detail_nakliyeci_view', pk=carrier.pk)
        else:
            messages.error(request, "Lütfen formdaki hataları düzeltin.")
    else:
        form = BankAccountForm() # request_user'ı burada geçirmeye gerek yok

    context = {'form': form, 'carrier': carrier, 'page_title': f"{carrier.full_name} için Yeni Banka Hesabı"}
    return render(request, 'ana_uygulama/nakliyeci/bank_account_form.html', context)

@login_required
def carrier_bank_account_edit_view(request, carrier_id, pk):
    """
    View to edit a bank account for a specific carrier.
    """
    if not request.user.company or request.user.company.company_type != 'NAKLIYECI':
        messages.error(request, "Yetkisiz erişim.")
        return redirect('ana_uygulama:dashboard')
    carrier = get_object_or_404(Carrier, id=carrier_id, managed_by_shipper=request.user.company)
    bank_account = get_object_or_404(BankAccount, pk=pk, carrier=carrier)

    if request.method == 'POST':
        form = BankAccountForm(request.POST, instance=bank_account) # request_user'ı burada geçirmeye gerek yok
        if form.is_valid():
            form.save()
            messages.success(request, "Banka hesabı başarıyla güncellendi.")
            return redirect('ana_uygulama:carrier_detail_nakliyeci_view', pk=carrier.pk)
        else:
            messages.error(request, "Lütfen formdaki hataları düzeltin.")
    else:
        form = BankAccountForm(instance=bank_account) # request_user'ı burada geçirmeye gerek yok

    context = {'form': form, 'carrier': carrier, 'bank_account': bank_account, 'page_title': "Banka Hesabını Düzenle"}
    return render(request, 'ana_uygulama/nakliyeci/bank_account_form.html', context)

@login_required
def carrier_bank_account_delete_view(request, carrier_id, pk):
    """
    View to delete a bank account for a specific carrier.
    """
    if not request.user.company or request.user.company.company_type != 'NAKLIYECI':
        messages.error(request, "Yetkisiz erişim.")
        return redirect('ana_uygulama:dashboard')
    carrier = get_object_or_404(Carrier, id=carrier_id, managed_by_shipper=request.user.company)
    bank_account = get_object_or_404(BankAccount, pk=pk, carrier=carrier)

    if request.method == 'POST':
        bank_account.delete()
        messages.success(request, "Banka hesabı başarıyla silindi.")
        return redirect('ana_uygulama:carrier_detail_nakliyeci_view', pk=carrier.pk)

    messages.warning(request, "Silme işlemi POST isteği gerektirir.")
    return redirect('ana_uygulama:carrier_detail_nakliyeci_view', pk=carrier.pk)


# Shipper - Invoice Management
@login_required
def invoice_list_nakliyeci_view(request):
    """
    Lists invoices issued by the shipper's company.
    Can be filtered by status, date range, and search query.
    """
    if not request.user.is_authenticated or not hasattr(request.user, 'company') or request.user.company.company_type != 'NAKLIYECI':
        messages.error(request, "Bu sayfaya erişim izniniz yok.")
        return redirect('ana_uygulama:dashboard')

    current_nakliyeci_company = request.user.company

    invoices = Invoice.objects.filter(issued_by_shipper=current_nakliyeci_company)

    # Filtering parameters
    status_filter = request.GET.get('status', '')
    date_from_filter = request.GET.get('date_from', '')
    date_to_filter = request.GET.get('date_to', '')
    search_query = request.GET.get('q', '').strip()

    page_title = "Faturalar"
    filter_description = "Tüm Faturalar"

    if status_filter:
        status_filter_upper = status_filter.upper()
        valid_statuses = [choice[0] for choice in Invoice.STATUS_CHOICES]

        if status_filter_upper == 'ODENMIS':
            invoices = invoices.filter(status='PAID')
            filter_description = "Ödenmiş Faturalar"
        elif status_filter_upper == 'ODENMEMIS':
            invoices = invoices.exclude(status__in=['PAID', 'VOID'])
            filter_description = "Ödenmemiş Faturalar"
        elif status_filter_upper in valid_statuses:
            invoices = invoices.filter(status=status_filter_upper)
            filter_description = f"Durum: {dict(Invoice.STATUS_CHOICES).get(status_filter_upper, status_filter_upper)} Faturalar"
        else:
            messages.warning(request, f"'{status_filter}' geçerli bir fatura durumu filtresi değil. Tüm faturalar gösteriliyor.")
            filter_description = "Tüm Faturalar (Geçersiz Filtre)"
        status_filter = status_filter_upper # Context için büyük harfli hali

    if date_from_filter:
        try:
            date_from = timezone.datetime.strptime(date_from_filter, "%Y-%m-%d").date()
            invoices = invoices.filter(issue_date__gte=date_from)
        except ValueError:
            messages.warning(request, "Geçersiz başlangıç tarihi formatı.")

    if date_to_filter:
        try:
            date_to = timezone.datetime.strptime(date_to_filter, "%Y-%m-%d").date()
            invoices = invoices.filter(issue_date__lte=date_to)
        except ValueError:
            messages.warning(request, "Geçersiz bitiş tarihi formatı.")

    if search_query:
        invoices = invoices.filter(
            Q(invoice_number__icontains=search_query) |
            Q(billed_to_factory__name__icontains=search_query) |
            Q(shipment__pk__icontains=search_query) |
            Q(description__icontains=search_query)
        )


    invoices = invoices.order_by('-issue_date', '-created_at')

    context = {
        'invoices': invoices,
        'page_title': page_title,
        'filter_description': filter_description,
        'status_choices': Invoice.STATUS_CHOICES, # For filter dropdown
        'current_filter': status_filter, # The actual value selected from dropdown
        'current_date_from': date_from_filter,
        'current_date_to': date_to_filter,
        'search_query': search_query,
    }
    return render(request, 'ana_uygulama/nakliyeci/invoice_list.html', context)

@login_required
def invoice_mark_as_paid_nakliyeci_view(request, invoice_id):
    """
    Marks an invoice as 'PAID' for the shipper.
    This is a simple status update, not a real payment integration.
    """
    invoice = get_object_or_404(Invoice, pk=invoice_id)

    # Permission check
    if invoice.issued_by_shipper != request.user.company and not request.user.is_superuser:
        messages.error(request, "Bu faturayı ödenmiş olarak işaretleme izniniz yok.")
        return redirect('ana_uygulama:invoice_list_nakliyeci_view')

    if request.method == 'POST':
        if invoice.status in ['PAID', 'VOID']:
            messages.info(request, f"Fatura {invoice.invoice_number} zaten '{invoice.get_status_display()}' durumunda.")
        else:
            invoice.status = 'PAID'
            # Assuming full payment, you might want to create a Payment record here if not already done.
            # For simplicity, we just update the status.
            try:
                invoice.save()
                messages.success(request, f"Fatura {invoice.invoice_number} başarıyla ödenmiş olarak işaretlendi.")
            except Exception as e:
                messages.error(request, f"Fatura durumu güncellenirken bir hata oluştu: {e}")
    else:
        messages.error(request, "Bu işlem sadece POST isteği ile yapılabilir.")

    return redirect('ana_uygulama:invoice_list_nakliyeci_view')


@login_required
def invoice_detail_nakliyeci_view(request, pk):  # DOĞRU
    invoice = get_object_or_404(Invoice, pk=pk)

    if invoice.issued_by_shipper != request.user.company and not request.user.is_superuser:
        messages.error(request, "Bu faturayı görüntüleme izniniz yok.")
        return redirect('ana_uygulama:invoice_list_nakliyeci_view')

    context = {
        'invoice': invoice,
        'page_title': f'{invoice.invoice_number} Detay',
        'calculated_vat_amount': invoice.total_vat_amount if invoice.total_vat_amount is not None else Decimal('0.00'),
        'calculated_total_amount': invoice.total_amount if invoice.total_amount is not None else Decimal('0.00'),
    }
    return render(request, 'ana_uygulama/nakliyeci/invoice_detail.html', {'invoice': invoice })

@login_required
def invoice_update_nakliyeci_view(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)

    if invoice.issued_by_shipper != request.user.company and not request.user.is_superuser:
        messages.error(request, "Bu faturayı düzenleme izniniz yok.")
        return redirect('ana_uygulama:invoice_list_nakliyeci_view')

    shipment = invoice.shipment
    net_amount_initial = invoice.amount # Amount alanı artık direkt modelden geliyor

    if request.method == 'POST':
        form = InvoiceForm(request.POST, instance=invoice)
        if form.is_valid():
            invoice = form.save(commit=False)
            invoice.save() # Bu save çağrısı modeldeki save() metodu ile total_amount'ı günceller.
            messages.success(request, f"Fatura {invoice.invoice_number} başarıyla güncellendi.")
            return redirect('ana_uygulama:invoice_detail_nakliyeci_view', invoice_id=invoice.pk) # URL adı düzeltildi
    else:
        form = InvoiceForm(instance=invoice, initial={'amount': net_amount_initial, 'vat_rate': invoice.vat_rate})

    context = {
        'form': form,
        'invoice': invoice,
        'shipment': shipment,
        'net_amount': net_amount_initial, # This is for display, form handles the actual initial
        'page_title': f'Fatura Düzenle {invoice.invoice_number}'
    }
    return render(request, 'ana_uygulama/nakliyeci/invoice_form.html', context)

@login_required
@user_company_type_required('NAKLIYECI') # Sadece Nakliyeci rolü için erişilebilir
def shipment_remove_vehicle_nakliyeci_view(request, pk):
    shipment = get_object_or_404(Shipment, pk=pk, shipper_company=request.user.company)
    if request.method == 'POST':
        # Aracın atamasını kaldır
        shipment.assigned_vehicle = None
        # Sevkiyat durumunu "Atandı"dan başka bir duruma (örn: "Yeni" veya "Onay Bekliyor"a) çevirebilirsiniz.
        # Örneğin: shipment.status = 'NEW'
        shipment.save()
        messages.success(request, f"'{shipment.load_description}' sevkiyatından araç ataması başarıyla kaldırıldı.")
        return redirect('ana_uygulama:shipment_detail_nakliyeci_view', pk=shipment.id)
    # POST dışındaki istekler için (örn: direkt URL'e gidildiğinde) detay sayfasına yönlendir.
    return redirect('ana_uygulama:shipment_detail_nakliyeci_view', pk=shipment.id)

@login_required
def invoice_delete_nakliyeci_view(request, pk):
    """
    View for the shipper to delete an invoice.
    """
    invoice = get_object_or_404(Invoice, pk=pk)

    if invoice.issued_by_shipper != request.user.company and not request.user.is_superuser:
        messages.error(request, "Bu faturayı silme izniniz yok.")
        return redirect('ana_uygulama:invoice_list_nakliyeci_view')

    if request.method == 'POST':
        invoice_number = invoice.invoice_number
        invoice.delete() # Model'deki delete metodu çağrılacak
        messages.success(request, f"Fatura {invoice_number} başarıyla silindi.")
        return redirect('ana_uygulama:invoice_list_nakliyeci_view')

    context = {
        'invoice': invoice,
        'page_title': f'Faturayı Sil {invoice.invoice_number}',
        'shipment': invoice.shipment
    }
    return render(request, 'ana_uygulama/nakliyeci/invoice_confirm_delete.html', context)

@login_required
def invoice_create_view(request, shipment_id):
    """
    View for the shipper to create an invoice for a specific shipment.
    """
    shipment = get_object_or_404(Shipment, id=shipment_id)
    # Permission check: Only the shipper managing the shipment can create an invoice
    if shipment.shipper_company != request.user.company:
        messages.error(request, "Bu sevkiyat için fatura oluşturma izniniz yok.")
        return redirect('ana_uygulama:dashboard')

    # Check if an invoice already exists for this shipment
    if Invoice.objects.filter(shipment=shipment).exists():
        messages.warning(request, f"Sevkiyat #{shipment.id} için zaten bir fatura var.")
        return redirect('ana_uygulama:shipment_detail_nakliyeci_view', shipment_id=shipment.id)


    net_amount = shipment.price_for_factory if shipment.price_for_factory is not None else Decimal('0.00')

    if request.method == 'POST':
        form = InvoiceForm(request.POST)
        if form.is_valid():
            invoice = form.save(commit=False)
            invoice.shipment = shipment
            invoice.created_by = request.user
            invoice.issued_by_shipper = request.user.company
            invoice.billed_to_factory = shipment.factory
            invoice.amount = net_amount # Amount alanı manuel olarak set edildi
            invoice.save()

            shipment.status = 'BILLED' # Update shipment status to billed
            shipment.save()

            messages.success(request, f"Fatura {invoice.invoice_number} başarıyla oluşturuldu ve Sevkiyat #{shipment.pk} faturalandırıldı.")
            return redirect('ana_uygulama:invoice_detail_nakliyeci_view', invoice_id=invoice.pk)
    else:
        # Pass initial data for amount if it's based on shipment price
        # Default invoice type and status, current date for issue date
        form = InvoiceForm(initial={
            'amount': net_amount,
            'vat_rate': Decimal('18.00'), # Example default VAT rate
            'issue_date': timezone.now().date(),
            'invoice_type': 'E_FATURA', # Default type
            'status': 'SENT' # Default status
        })

    context = {
        'form': form,
        'shipment': shipment,
        'net_amount': net_amount, # Used for display
        'page_title': "Yeni Fatura Oluştur"
    }
    return render(request, 'ana_uygulama/nakliyeci/invoice_form.html', context)


# Shipper - Payment Management
@login_required
def payment_list_nakliyeci_view(request):
    """
    Lists payment/collection records for the shipper company.
    """
    if not request.user.company or request.user.company.company_type != 'NAKLIYECI':
        messages.error(request, "Bu sayfaya erişim izniniz yok.")
        return redirect('ana_uygulama:dashboard')

    payments = Payment.objects.filter(shipper_company=request.user.company).order_by('-payment_date', '-created_at')

    context = {
        'payments': payments,
        'page_title': 'Ödemeler/ Tahsilatlar'
    }
    return render(request, 'ana_uygulama/nakliyeci/payment_list.html', context)

@login_required
def payment_create_nakliyeci_view(request):
    """
    View for the shipper to create a new payment/collection record.
    """
    if not request.user.company or request.user.company.company_type != 'NAKLIYECI':
        messages.error(request, "Bu sayfaya erişim izniniz yok.")
        return redirect('ana_uygulama:dashboard')

    if request.method == 'POST':
        form = PaymentForm(request.POST, request_user=request.user)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.shipper_company = request.user.company
            payment.recorded_by_user = request.user
            try:
                payment.save()
                messages.success(request, f"Ödeme/Tahsilat kaydı başarıyla eklendi (Tutar: {payment.amount} TL).")
                return redirect('ana_uygulama:payment_list_nakliyeci_view')
            except Exception as e:
                messages.error(request, f"Kayıt eklenirken bir hata oluştu: {e}")
        else:
            messages.error(request, "Lütfen formdaki hataları düzeltin.")
    else:
        form = PaymentForm(request_user=request.user)

    context = {
        'form': form,
        'page_title': 'Yeni Ödeme/Tahsilat Kaydı Ekle'
    }
    return render(request, 'ana_uygulama/nakliyeci/payment_form.html', context)

@login_required
def payment_detail_nakliyeci_view(request, pk):
    """
    Displays details of a specific payment/collection record for the shipper.
    """
    payment = get_object_or_404(Payment, pk=pk)
    if payment.shipper_company != request.user.company and not request.user.is_superuser:
        messages.error(request, "Bu kaydı görüntüleme izniniz yok.")
        return redirect('ana_uygulama:payment_list_nakliyeci_view')

    context = {
        'payment': payment,
        'page_title': f'Ödeme/Tahsilat Detayı #{payment.pk}'
    }
    return render(request, 'ana_uygulama/nakliyeci/payment_detail.html', context)

@login_required
def payment_update_nakliyeci_view(request, pk):
    """
    View for the shipper to update a payment/collection record.
    """
    payment = get_object_or_404(Payment, pk=pk)
    if payment.shipper_company != request.user.company and not request.user.is_superuser:
        messages.error(request, "Bu kaydı güncelleme izniniz yok.")
        return redirect('ana_uygulama:payment_list_nakliyeci_view')

    if request.method == 'POST':
        form = PaymentForm(request.POST, instance=payment, request_user=request.user)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, f"Ödeme/Tahsilat kaydı #{payment.pk} başarıyla güncellendi.")
                return redirect('ana_uygulama:payment_detail_nakliyeci_view', pk=payment.pk)
            except Exception as e:
                messages.error(request, f"Kayıt güncellenirken bir hata oluştu: {e}")
        else:
            messages.error(request, "Lütfen formdaki hataları düzeltin.")
    else:
        form = PaymentForm(instance=payment, request_user=request.user)

    context = {
        'form': form,
        'payment': payment,
        'page_title': f'Ödeme/Tahsilat Kaydı Düzenle #{payment.pk}'
    }
    return render(request, 'ana_uygulama/nakliyeci/payment_form.html', context)

@login_required
def payment_delete_nakliyeci_view(request, pk):
    """
    View for the shipper to delete a payment/collection record.
    """
    payment = get_object_or_404(Payment, pk=pk)
    if payment.shipper_company != request.user.company and not request.user.is_superuser:
        messages.error(request, "Bu kaydı silme izniniz yok.")
        return redirect('ana_uygulama:payment_list_nakliyeci_view')

    if request.method == 'POST':
        payment.delete()
        messages.success(request, f"Ödeme/Tahsilat kaydı #{pk} başarıyla silindi.")
        return redirect('ana_uygulama:payment_list_nakliyeci_view')

    context = {
        'payment': payment,
        'page_title': f'Ödeme/Tahsilat Kaydı Sil #{payment.pk}'
    }
    return render(request, 'ana_uygulama/nakliyeci/payment_confirm_delete.html', context)


# Shipper - User Management (Company Users)
@login_required
def company_user_list_nakliyeci_view(request):
    """
    Lists company users for the shipper company manager.
    """
    if not request.user.company or request.user.company.company_type != 'NAKLIYECI':
        messages.error(request, "Bu sayfaya erişim izniniz yok.")
        return redirect('ana_uygulama:dashboard')
    users = CustomUser.objects.filter(company=request.user.company)
    context = {'users': users, 'company_type_display': 'Nakliyeci', 'page_title': "Firma Kullanıcıları"}
    return render(request, 'ana_uygulama/company_user_list.html', context)

@login_required
def company_user_create_nakliyeci_view(request):
    """
    View for the shipper company manager to add new users to their company.
    """
    if not request.user.company or request.user.company.company_type != 'NAKLIYECI':
        messages.error(request, "Bu sayfaya erişim izniniz yok.")
        return redirect('ana_uygulama:dashboard')
    if request.method == 'POST':
        form = CompanyUserCreationForm(request.POST)
        if form.is_valid():
            new_user = form.save(commit=False)
            new_user.company = request.user.company
           
            new_user.is_staff = False
            new_user.save()
            messages.success(request, f"Kullanıcı {new_user.username} başarıyla eklendi.")
            return redirect('ana_uygulama:company_user_list_nakliyeci_view')
        else:
            messages.error(request, "Lütfen formdaki hataları düzeltin.")
    else:
        form = CompanyUserCreationForm()
    context = {'form': form, 'company_type_display': 'Nakliyeci', 'page_title': "Yeni Nakliyeci Kullanıcısı Ekle"}
    return render(request, 'ana_uygulama/company_user_form.html', context)

# Shipper - User Update
@login_required
def company_user_update_nakliyeci_view(request, pk):
    """
    Nakliyeci firma yöneticisinin şirketlerindeki mevcut kullanıcıları güncellemesi için görünüm.
    """
    if not request.user.company or request.user.company.company_type != 'NAKLIYECI':
        messages.error(request, "Bu sayfaya erişim izniniz yok.")
        return redirect('ana_uygulama:dashboard')
    user_to_update = get_object_or_404(CustomUser, pk=pk, company=request.user.company)
    if request.method == 'POST':
        form = CompanyUserCreationForm(request.POST, instance=user_to_update)
        if form.is_valid():
            form.save()
            messages.success(request, f"Kullanıcı {user_to_update.username} bilgileri başarıyla güncellendi.")
            return redirect('ana_uygulama:company_user_list_nakliyeci_view')
        else:
            messages.error(request, "Lütfen formdaki hataları düzeltin.")
    else:
        form = CompanyUserCreationForm(instance=user_to_update)
    context = {'form': form, 'page_title': "Şirket Kullanıcısını Güncelle"}
    return render(request, 'ana_uygulama/company_user_form.html', context)


# Shipper - User Delete
@login_required
def company_user_delete_nakliyeci_view(request, pk):
    """
    Nakliyeci firma yöneticisinin şirketlerinden kullanıcıları silmesi için görünüm.
    """
    if not request.user.company or request.user.company.company_type != 'NAKLIYECI':
        messages.error(request, "Bu sayfaya erişim izniniz yok.")
        return redirect('ana_uygulama:dashboard')
    user_to_delete = get_object_or_404(CustomUser, pk=pk, company=request.user.company)
    if request.method == 'POST':
        user_to_delete.delete()
        messages.success(request, f"Kullanıcı {user_to_delete.username} başarıyla silindi.")
        return redirect('ana_uygulama:company_user_list_nakliyeci_view')
    context = {'user_to_delete': user_to_delete, 'page_title': "Şirket Kullanıcısını Sil"}
    return render(request, 'ana_uygulama/company_user_confirm_delete.html', context)


# Shipper - Company Listing (Viewing Other Companies)
@login_required
def company_list_for_nakliyeci_view(request):
    """
    View for the shipper role to list other companies in the system.
    Displays Factories and other Shippers separately.
    """
    if not request.user.company or request.user.company.company_type != 'NAKLIYECI':
        messages.error(request, "Bu sayfaya erişim izniniz yok.")
        return redirect('ana_uygulama:dashboard')

    fabrika_firmasi_filter = request.GET.get('fabrika_firmasi', '').strip()
    nakliyeci_firmasi_filter = request.GET.get('nakliyeci_firmasi', '').strip()

    fabrikalar = Company.objects.filter(company_type='FABRIKA').order_by('name')
    if fabrika_firmasi_filter:
        fabrikalar = fabrikalar.filter(name__icontains=fabrika_firmasi_filter)

    nakliyeciler = Company.objects.filter(company_type='NAKLIYECI').order_by('name')
    if nakliyeci_firmasi_filter:
        nakliyeciler = nakliyeciler.filter(name__icontains=nakliyeci_firmasi_filter)

    # Exclude the user's own company from the shipper list
    if request.user.company and request.user.company.company_type == 'NAKLIYECI':
        nakliyeciler = nakliyeciler.exclude(pk=request.user.company.pk)

    context = {
        'fabrikalar': fabrikalar,
        'nakliyeciler': nakliyeciler,
        'page_title': "Sistemdeki Firmalar",
        'fabrika_firmasi_filter_value': fabrika_firmasi_filter,
        'nakliyeci_firmasi_filter_value': nakliyeci_firmasi_filter,
    }
    return render(request, 'ana_uygulama/nakliyeci/company_list.html', context)


# Create Factory (for Shipper to add their own client factories)
@login_required
def factory_create_by_nakliyeci_view(request):
    """
    View for the shipper role to add a new client factory.
    """
    if not request.user.company or request.user.company.company_type != 'NAKLIYECI':
        messages.error(request, "Sadece nakliyeci firmaları yeni fabrika ekleyebilir.")
        return redirect('ana_uygulama:dashboard')

    if request.method == 'POST':
        form = FactoryCreationByShipperForm(request.POST)
        if form.is_valid():
            factory_company = form.save(commit=False)
            factory_company.company_type = 'FABRIKA'
            try:
                factory_company.save()
                messages.success(request, f"Fabrika '{factory_company.name}' başarıyla eklendi.")
                return redirect('ana_uygulama:company_list_for_nakliyeci_view') # Redirect to company list
            except Exception as e:
                messages.error(request, f"Fabrika eklenirken bir hata oluştu: {e}")
        else:
            messages.error(request, "Lütfen formdaki hataları düzeltin.")
    else:
        form = FactoryCreationByShipperForm()

    context = {
        'form': form,
        'page_title': "Yeni Müşteri Fabrikası Ekle"
    }
    return render(request, 'ana_uygulama/nakliyeci/factory_create_form.html', context)


# === Factory Views ===

# Factory - Quote Management
@login_required
def quote_request_list_fabrika_view(request):
    """
    Lists quote requests for the user with the 'FABRIKA' (Factory) role.
    """
    if not request.user.company or request.user.company.company_type != 'FABRIKA':
        messages.error(request, "Bu sayfaya erişim izniniz yok.")
        return redirect('ana_uygulama:dashboard')
    quote_requests = QuoteRequest.objects.filter(factory=request.user.company).order_by('-created_at')
    context = {'quote_requests': quote_requests, 'page_title': "Teklif Talepleri"}
    return render(request, 'ana_uygulama/fabrika/quote_request_list.html', context)

@login_required
def quote_request_create_fabrika_view(request):
    """
    View for the factory role user to create a new quote request.
    """
    if not request.user.company or request.user.company.company_type != 'FABRIKA':
        messages.error(request, "Bu sayfaya erişim izniniz yok.")
        return redirect('ana_uygulama:dashboard')
    if request.method == 'POST':
        form = QuoteRequestForm(request.POST)
        if form.is_valid():
            quote_request = form.save(commit=False)
            quote_request.factory = request.user.company
            quote_request.created_by_user = request.user
            quote_request.status = 'PENDING'
            quote_request.save()
            messages.success(request, "Fiyat teklifi talebiniz başarıyla oluşturuldu.")
            return redirect('ana_uygulama:quote_request_list_fabrika_view')
        else:
            messages.error(request, "Lütfen formdaki hataları düzeltin.")
    else:
        form = QuoteRequestForm()
    context = {'form': form, 'page_title': "Yeni Fiyat Teklifi Talebi Oluştur"}
    return render(request, 'ana_uygulama/fabrika/quote_request_form.html', context)

@login_required
def quote_request_detail_fabrika_view(request, pk):
    """
    Displays the details of a specific quote request for the factory role.
    """
    if not request.user.company or request.user.company.company_type != 'FABRIKA':
        messages.error(request, "Bu sayfaya erişim izniniz yok.")
        return redirect('ana_uygulama:dashboard')
    quote_request = get_object_or_404(QuoteRequest.objects.select_related('factory','priced_by_shipper_company'), pk=pk, factory=request.user.company)
    context = {'quote_request': quote_request, 'page_title': f"Teklif Talebi Detayı #{quote_request.pk}"}
    return render(request, 'ana_uygulama/fabrika/quote_request_detail.html', context)

@login_required
def request_quote_update_fabrika_view(request, pk):
    """
    View for the factory role user to update their own quote request.
    """
    quote_request = get_object_or_404(QuoteRequest, pk=pk)
    if quote_request.factory != request.user.company or quote_request.status != 'PENDING':
        messages.error(request, "Bu teklif talebini güncelleme izniniz yok veya durumu uygun değil.")
        return redirect('ana_uygulama:quote_request_list_fabrika_view')

    if request.method == 'POST':
        form = QuoteRequestForm(request.POST, instance=quote_request)
        if form.is_valid():
            form.save()
            messages.success(request, f"Teklif Talebi #{quote_request.pk} başarıyla güncellendi.")
            return redirect('ana_uygulama:quote_request_detail_fabrika_view', pk=quote_request.pk)
    else:
        form = QuoteRequestForm(instance=quote_request)

    context = {
        'form': form,
        'quote_request': quote_request,
        'page_title': f'Teklif Talebini Güncelle #{quote_request.pk}'
    }
    return render(request, 'ana_uygulama/fabrika/quote_request_form.html', context)

@login_required
def quote_request_delete_fabrika_view(request, pk):
    """
    View for the factory role user to delete their own quote request.
    """
    quote_request = get_object_or_404(QuoteRequest, pk=pk)
    if quote_request.factory != request.user.company and not request.user.is_superuser:
        messages.error(request, "Bu teklif talebini silme izniniz yok.")
        return redirect('ana_uygulama:quote_request_list_fabrika_view')

    if request.method == 'POST':
        quote_request.delete()
        messages.success(request, "Teklif talebi başarıyla silindi.")
        return redirect('ana_uygulama:quote_request_list_fabrika_view')

    context = {
        'quote_request': quote_request,
        'page_title': f'Teklif Talebini Sil #{quote_request.pk}'
    }
    return render(request, 'ana_uygulama/fabrika/quote_request_confirm_delete.html', context)

@login_required
def accept_quote_fabrika_view(request, quote_id):
    """
    View for the factory role user to accept a shipper's quote.
    Automatically creates a new shipment upon acceptance.
    """
    quote_request = get_object_or_404(QuoteRequest, pk=quote_id)
    if quote_request.factory != request.user.company or quote_request.status != 'QUOTED':
        messages.error(request, "Bu teklifi kabul etme izniniz yok veya durumu uygun değil.")
        return redirect('ana_uygulama:quote_request_list_fabrika_view')

    if not hasattr(quote_request, 'priced_by_shipper_company') or not quote_request.priced_by_shipper_company:
         messages.error(request, "HATA: Teklifi fiyatlandıran nakliyeci bilgisi eksik. İş oluşturulamadı.")
         return redirect('ana_uygulama:quote_request_list_fabrika_view')

    try:
        Shipment.objects.create(
            quote_request=quote_request,
            factory=quote_request.factory,
            shipper_company=quote_request.priced_by_shipper_company,
            origin=quote_request.origin,
            destination=quote_request.destination,
            load_description=quote_request.load_description,
            weight=quote_request.weight,
            volume=quote_request.volume,
            pickup_date=quote_request.requested_pickup_date,
            price_for_factory=quote_request.offered_price,
            status='PENDING_ASSIGNMENT', # Initial shipment status
            created_by_user=request.user
        )
        quote_request.status = 'COMPLETED'
        quote_request.save()
        messages.success(request, f"Teklif talebi #{quote_request.pk} başarıyla kabul edildi ve yeni sevkiyat oluşturuldu.")
    except Exception as e:
        messages.error(request, f"Teklif kabul edildi, ancak iş oluşturulurken bir hata oluştu: {e}")
        # If error occurs, keep quote status as QUOTED or define a separate 'ACCEPT_FAILED' status
        quote_request.status = 'QUOTED'
        quote_request.save()
    return redirect('ana_uygulama:quote_request_list_fabrika_view')


@login_required
def reject_quote_fabrika_view(request, quote_id):
    """
    View for the factory role user to reject a shipper's quote.
    """
    quote_request = get_object_or_404(QuoteRequest, pk=quote_id)
    if quote_request.factory != request.user.company or quote_request.status != 'QUOTED':
        messages.error(request, "Bu teklifi reddetme izniniz yok veya durumu uygun değil.")
        return redirect('ana_uygulama:quote_request_list_fabrika_view')

    quote_request.status = 'REJECTED'
    quote_request.save()
    messages.success(request, f"Teklif talebi #{quote_request.pk} reddedildi.")
    return redirect('ana_uygulama:quote_request_list_fabrika_view')


# Factory - Shipments Management
@login_required
def shipment_list_fabrika_view(request):
    """
    Lists shipments belonging to the factory's company.
    """
    if not request.user.is_authenticated or not hasattr(request.user, 'company') or request.user.company.company_type != 'FABRIKA':
        messages.error(request, "Bu sayfaya erişim izniniz yok.")
        return redirect('ana_uygulama:dashboard')

    shipments = Shipment.objects.filter(factory=request.user.company).order_by('-created_at')

    context = {
        'shipments': shipments,
        'page_title': 'Gönderilerim'
    }
    return render(request, 'ana_uygulama/fabrika/shipment_list.html', context)

@login_required
def shipment_detail_fabrika_view(request, shipment_id):
    """
    Displays the details of a specific shipment for the factory role.
    """
    shipment = get_object_or_404(Shipment, pk=shipment_id)
    if shipment.factory != request.user.company and not request.user.is_superuser:
        messages.error(request, "Bu sevkiyatı görüntüleme izniniz yok.")
        return redirect('ana_uygulama:shipment_list_fabrika_view')

    context = {
        'shipment': shipment,
        'page_title': f'Sevkiyat #{shipment.pk} Detay'
    }
    return render(request, 'ana_uygulama/fabrika/shipment_detail.html', context)


# Factory - Invoices Management
@login_required
def invoice_list_fabrika_view(request):
    """
    Lists invoices billed to the factory's company.
    """
    if not request.user.is_authenticated or not hasattr(request.user, 'company') or request.user.company.company_type != 'FABRIKA':
        messages.error(request, "Bu sayfaya erişim izniniz yok.")
        return redirect('ana_uygulama:dashboard')

    invoices = Invoice.objects.filter(billed_to_factory=request.user.company).order_by('-issue_date', '-created_at')

    context = {
        'invoices': invoices,
        'page_title': 'Faturalar',
    }
    return render(request, 'ana_uygulama/fabrika/invoice_list.html', context)

@login_required
def invoice_detail_fabrika_view(request, invoice_id):
    """
    Displays the details of a specific invoice for the factory role.
    """
    invoice = get_object_or_404(Invoice, pk=invoice_id)
    if invoice.billed_to_factory != request.user.company and not request.user.is_superuser:
        messages.error(request, "Bu faturayı görüntüleme izniniz yok.")
        return redirect('ana_uygulama:invoice_list_fabrika_view')

    context = {
        'invoice': invoice,
        'page_title': f'{invoice.invoice_number} Detay',
        'calculated_vat_amount': invoice.total_vat_amount if invoice.total_vat_amount is not None else Decimal('0.00'),
        'calculated_total_amount': invoice.total_amount if invoice.total_amount is not None else Decimal('0.00'),
    }
    return render(request, 'ana_uygulama/fabrika/invoice_detail.html', context)


# === Company Management Views (Generally for Superuser or Admin Access) ===
@login_required
def company_list_view(request):
    """
    Lists all companies in the system (typically requires superuser privileges).
    """
    if not request.user.is_superuser:
        messages.error(request, "Bu sayfaya erişim izniniz yok.")
        return redirect('ana_uygulama:dashboard')

    companies = Company.objects.all().order_by('name')
    context = {
        'companies': companies,
        'page_title': 'Firmalar'
    }
    return render(request, 'ana_uygulama/company_list.html', context)

@login_required
def company_create_view(request):
    """
    View to create a new company (typically requires superuser privileges).
    """
    if not request.user.is_superuser:
        messages.error(request, "Bu sayfaya erişim izniniz yok.")
        return redirect('ana_uygulama:dashboard')

    if request.method == 'POST':
        form = CompanyForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Firma başarıyla oluşturuldu.")
            return redirect('ana_uygulama:company_list_view')
    else:
        form = CompanyForm()

    context = {
        'form': form,
        'page_title': 'Yeni Firma Oluştur'
    }
    return render(request, 'ana_uygulama/company_form.html', context)

@login_required
def company_detail_view(request, pk):
    """
    Displays the details of a specific company (typically requires superuser privileges).
    """
    company = get_object_or_404(Company, pk=pk)
    if not request.user.is_superuser:
        messages.error(request, "Bu firmayı görüntüleme izniniz yok.")
        return redirect('ana_uygulama:dashboard')

    context = {
        'company': company,
        'page_title': f'{company.name} Detay'
    }
    return render(request, 'ana_uygulama/company_detail.html', context)

@login_required
def company_update_view(request, pk):
    """
    View to update information for a specific company (typically requires superuser privileges).
    """
    company = get_object_or_404(Company, pk=pk)
    if not request.user.is_superuser:
        messages.error(request, "Bu firmayı düzenleme izniniz yok.")
        return redirect('ana_uygulama:dashboard')

    if request.method == 'POST':
        form = CompanyForm(request.POST, instance=company)
        if form.is_valid():
            form.save()
            messages.success(request, f"Firma {company.name} başarıyla güncellendi.")
            return redirect('ana_uygulama:company_detail_view', pk=company.pk)
    else:
        form = CompanyForm(instance=company)

    context = {
        'form': form,
        'company': company,
        'page_title': f'Firma Güncelle {company.name}'
    }
    return render(request, 'ana_uygulama/company_form.html', context)

@login_required
def company_delete_view(request, pk):
    """
    View to delete a specific company (typically requires superuser privileges).
    """
    company = get_object_or_404(Company, pk=pk)
    if not request.user.is_superuser:
        messages.error(request, "Bu firmayı silme izniniz yok.")
        return redirect('ana_uygulama:dashboard')

    if request.method == 'POST':
        company.delete()
        messages.success(request, f"Firma {company.name} başarıyla silindi.")
        return redirect('ana_uygulama:company_list_view')

    context = {
        'company': company,
        'page_title': f'Firmayı Sil {company.name}'
    }
    return render(request, 'ana_uygulama/company_confirm_delete.html', context)


# === Global Search and AJAX Search Views ===
@login_required
def global_search_view(request):
    """
    Performs a global search across different models in the system.
    Includes access restrictions based on user role.
    """
    query = request.GET.get('q', '').strip()
    context = {
        'query': query,
        'page_title': f"'{query}' için Arama Sonuçları" if query else "Arama",
        'results_shipments': [],
        'results_vehicles': [],
        'results_carriers': [],
        'results_companies_factory': [],
        'results_companies_shipper': [],
        'results_invoices': [],
        'results_quote_requests': [],
        'results_payments': [], # Add payments to search results
    }

    if query and len(query) >= 2:
        user_company = None
        is_shipper = False
        if request.user.is_authenticated and hasattr(request.user, 'company') and request.user.company:
            user_company = request.user.company
            if user_company.company_type == 'NAKLIYECI':
                is_shipper = True

        # Shipment search
        shipment_q = (
            Q(pk__icontains=query) |
            Q(origin__icontains=query) |
            Q(destination__icontains=query) |
            Q(load_description__icontains=query) |
            Q(factory__name__icontains=query) |
            Q(assigned_vehicle__plate_number__icontains=query)
        )
        temp_shipments = Shipment.objects.filter(shipment_q)
        if is_shipper and user_company:
            temp_shipments = temp_shipments.filter(shipper_company=user_company)
        elif request.user.is_authenticated and user_company and user_company.company_type == 'FABRIKA':
            temp_shipments = temp_shipments.filter(factory=user_company)
        context['results_shipments'] = temp_shipments.distinct()[:10]

        # Vehicle search (for shippers only)
        if is_shipper and user_company:
            vehicles = Vehicle.objects.filter(
                Q(plate_number__icontains=query) | Q(driver_name__icontains=query)
            ).filter(carrier__managed_by_shipper=user_company)
            for v in vehicles.distinct()[:5]:
                # Correct the URL name to match urls.py (e.g., 'vehicle_detail_nakliyeci' without '_view')
                context['results_vehicles'].append({
                    'type': 'Araç',
                    'text': f'{v.plate_number} ({v.driver_name})',
                    'url': reverse('ana_uygulama:vehicle_detail_nakliyeci_view', args=[v.pk]) # Corrected URL name
                })

        # Carrier search
        carrier_q = (
            Q(full_name__icontains=query) |
            Q(phone__icontains=query) |
            Q(email__icontains=query) |
            Q(tax_id_number__icontains=query)
        )
        temp_carriers = Carrier.objects.filter(carrier_q)
        if is_shipper and user_company:
            temp_carriers = temp_carriers.filter(managed_by_shipper=user_company)
        context['results_carriers'] = temp_carriers.distinct()[:10]

        # Company (Factory) search
        context['results_companies_factory'] = Company.objects.filter(
            Q(company_type='FABRIKA') &
            (Q(name__icontains=query) | Q(email__icontains=query) | Q(phone__icontains=query))
        ).distinct()[:10]

        # Company (Shipper) search
        context['results_companies_shipper'] = Company.objects.filter(
            Q(company_type='NAKLIYECI') &
            (Q(name__icontains=query) | Q(email__icontains=query) | Q(phone__icontains=query)) &
            ~Q(pk=user_company.pk if user_company else -1) # Exclude own company
        ).distinct()[:10]

        # Invoice search
        invoice_q = (
            Q(invoice_number__icontains=query) |
            Q(billed_to_factory__name__icontains=query) |
            Q(shipment__pk__icontains=query)
        )
        temp_invoices = Invoice.objects.filter(invoice_q)
        if is_shipper and user_company:
            temp_invoices = temp_invoices.filter(issued_by_shipper=user_company)
        elif request.user.is_authenticated and user_company and user_company.company_type == 'FABRIKA':
            temp_invoices = temp_invoices.filter(billed_to_factory=user_company)
        context['results_invoices'] = temp_invoices.distinct()[:10]

        # QuoteRequest search
        quote_q = (
            Q(pk__icontains=query) |
            Q(origin__icontains=query) |
            Q(destination__icontains=query) |
            Q(factory__name__icontains=query)
        )
        temp_quotes = QuoteRequest.objects.filter(quote_q)
        if is_shipper and user_company:
            temp_quotes = temp_quotes.filter(Q(status='PENDING') | Q(priced_by_shipper_company=user_company))
        elif request.user.is_authenticated and user_company and user_company.company_type == 'FABRIKA':
            temp_quotes = temp_quotes.filter(factory=user_company)
        context['results_quote_requests'] = temp_quotes.distinct()[:10]

        # Payment search
        payment_q = (
            Q(description__icontains=query) |
            Q(amount__icontains=query) |
            Q(invoice__invoice_number__icontains=query) |
            Q(shipment__pk__icontains=query) |
            Q(counterparty_company__name__icontains=query) |
            Q(counterparty_name__icontains=query)
        )
        temp_payments = Payment.objects.filter(payment_q)
        if is_shipper and user_company:
            temp_payments = temp_payments.filter(shipper_company=user_company)
        elif request.user.is_authenticated and user_company and user_company.company_type == 'FABRIKA':
            temp_payments = temp_payments.filter(recorded_by_user__company=user_company, direction='OUTGOING') # Fabrika için sadece giden ödemeler
        context['results_payments'] = temp_payments.distinct()[:10]

    return render(request, 'ana_uygulama/search_results.html', context)


@login_required
def ajax_live_search_view(request):
    """
    AJAX view that returns live search results.
    Performs a lighter search and returns JsonResponse.
    """
    query = request.GET.get('term', '').strip()
    results = []
    if query and len(query) >= 2:
        user_company = None
        is_shipper = False
        if request.user.is_authenticated and hasattr(request.user, 'company') and request.user.company:
            user_company = request.user.company
            if user_company.company_type == 'NAKLIYECI':
                is_shipper = True

        # Example: Shipment search
        shipments = Shipment.objects.filter(
            Q(origin__icontains=query) | Q(destination__icontains=query) | Q(pk__icontains=query)
        )
        if is_shipper and user_company:
            shipments = shipments.filter(shipper_company=user_company)
        elif request.user.is_authenticated and user_company and user_company.company_type == 'FABRIKA':
            shipments = shipments.filter(factory=user_company)

        for s in shipments.distinct()[:5]: # Max 5 results
            results.append({
                'type': 'İş',
                'text': f'#{s.pk}: {s.origin} -> {s.destination}',
                'url': reverse('ana_uygulama:shipment_detail_nakliyeci_view', args=[s.pk]) if is_shipper else reverse('ana_uygulama:shipment_detail_fabrika_view', args=[s.pk])
            })

        # Example: Vehicle search (for shippers only)
        if is_shipper and user_company:
            vehicles = Vehicle.objects.filter(
                Q(plate_number__icontains=query) | Q(driver_name__icontains=query)
            ).filter(carrier__managed_by_shipper=user_company)
            for v in vehicles.distinct()[:5]:
                results.append({ # Append to results, not context['results_vehicles']
                    'type': 'Araç',
                    'text': f'{v.plate_number} ({v.driver_name})',
                    'url': reverse('ana_uygulama:vehicle_detail_nakliyeci_view', args=[v.pk]) # Corrected URL name
                })

        # Carrier search
        carrier_q = (
            Q(full_name__icontains=query) |
            Q(phone__icontains=query) |
            Q(email__icontains=query) |
            Q(tax_id_number__icontains=query)
        )
        temp_carriers = Carrier.objects.filter(carrier_q)
        if is_shipper and user_company:
            temp_carriers = temp_carriers.filter(managed_by_shipper=user_company)
        for c in temp_carriers.distinct()[:5]: # Max 5 results
            results.append({
                'type': 'Taşıyıcı',
                'text': f'Taşıyıcı: {c.full_name}',
                'url': reverse('ana_uygulama:carrier_detail_nakliyeci_view', args=[c.pk])
            })

        # Company (Factory) search
        temp_factories = Company.objects.filter(
            Q(company_type='FABRIKA') &
            (Q(name__icontains=query) | Q(email__icontains=query) | Q(phone__icontains=query))
        )
        for f in temp_factories.distinct()[:5]: # Max 5 results
            results.append({
                'type': 'Fabrika Firma',
                'text': f'Fabrika: {f.name}',
                'url': reverse('ana_uygulama:company_detail_view', args=[f.pk]) # Generic company detail for now
            })

        # Company (Shipper) search
        temp_shippers = Company.objects.filter(
            Q(company_type='NAKLIYECI') &
            (Q(name__icontains=query) | Q(email__icontains=query) | Q(phone__icontains=query)) &
            ~Q(pk=user_company.pk if user_company else -1) # Exclude own company
        )
        for s in temp_shippers.distinct()[:5]: # Max 5 results
            results.append({
                'type': 'Nakliyeci Firma',
                'text': f'Nakliyeci: {s.name}',
                'url': reverse('ana_uygulama:company_detail_view', args=[s.pk]) # Generic company detail for now
            })

        # Invoice search
        invoice_q = (
            Q(invoice_number__icontains=query) |
            Q(billed_to_factory__name__icontains=query) |
            Q(shipment__pk__icontains=query)
        )
        temp_invoices = Invoice.objects.filter(invoice_q)
        if is_shipper and user_company:
            temp_invoices = temp_invoices.filter(issued_by_shipper=user_company)
        elif request.user.is_authenticated and user_company and user_company.company_type == 'FABRIKA':
            temp_invoices = temp_invoices.filter(billed_to_factory=user_company)
        for i in temp_invoices.distinct()[:5]: # Max 5 results
            results.append({
                'type': 'Fatura',
                'text': f'Fatura: #{i.invoice_number} ({i.total_amount} TL)',
                'url': reverse('ana_uygulama:invoice_detail_nakliyeci_view' if is_shipper else 'ana_uygulama:invoice_detail_fabrika_view', args=[i.pk])
            })

        # QuoteRequest search
        quote_q = (
            Q(pk__icontains=query) |
            Q(origin__icontains=query) |
            Q(destination__icontains=query) |
            Q(factory__name__icontains=query)
        )
        temp_quotes = QuoteRequest.objects.filter(quote_q)
        if is_shipper and user_company:
            temp_quotes = temp_quotes.filter(Q(status='PENDING') | Q(priced_by_shipper_company=user_company))
        elif request.user.is_authenticated and user_company and user_company.company_type == 'FABRIKA':
            temp_quotes = temp_quotes.filter(factory=user_company)
        for qr in temp_quotes.distinct()[:5]: # Max 5 results
            results.append({
                'type': 'Teklif Talebi',
                'text': f'Teklif Talebi: #{qr.pk} ({qr.get_status_display()})',
                'url': reverse('ana_uygulama:quote_request_detail_nakliyeci_view' if is_shipper else 'ana_uygulama:quote_request_detail_fabrika_view', args=[qr.pk])
            })

        # Payment search
        payment_q = (
            Q(description__icontains=query) |
            Q(amount__icontains=query) |
            Q(invoice__invoice_number__icontains=query) |
            Q(shipment__pk__icontains=query) |
            Q(counterparty_company__name__icontains=query) |
            Q(counterparty_name__icontains=query)
        )
        temp_payments = Payment.objects.filter(payment_q)
        if is_shipper and user_company:
            temp_payments = temp_payments.filter(shipper_company=user_company)
        elif request.user.is_authenticated and user_company and user_company.company_type == 'FABRIKA':
            temp_payments = temp_payments.filter(recorded_by_user__company=user_company, direction='OUTGOING') # Fabrika için sadece giden ödemeler
        for p in temp_payments.distinct()[:5]: # Max 5 results
            results.append({
                'type': 'Ödeme/Tahsilat',
                'text': f'Ödeme/Tahsilat: {p.get_direction_display()} {p.amount} TL', # get_direction_display eklendi
                'url': reverse('ana_uygulama:payment_detail_nakliyeci_view' if is_shipper else 'ana_uygulama:payment_detail_fabrika_view', args=[p.pk])
            })

        # Bank Account search (for own company accounts only)
        bank_accounts = BankAccount.objects.filter(
            Q(bank_name__icontains=query) | Q(iban__icontains=query)
        )
        if user_company:
            # BankAccount modelinde 'company' alanı yok, doğrudan 'carrier' üzerinden şirkete bağlanıyor.
            # Dolayısıyla, banka hesabını kendi şirketine ait carrier'lar üzerinden filtrelemeliyiz.
            if is_shipper and user_company:
                bank_accounts = bank_accounts.filter(carrier__managed_by_shipper=user_company)
            # Fabrika için banka hesabı listeleme views'ı olmadığı varsayımıyla şimdilik boş bırakılabilir.
            else:
                bank_accounts = BankAccount.objects.none() # Fabrikaların direkt banka hesapları yönetimi yoksa

        for ba in bank_accounts.distinct()[:5]:
            results.append({
                'type': 'Banka Hesabı',
                'text': f'Banka Hesabı: {ba.bank_name} - {ba.iban}',
                'url': reverse('ana_uygulama:bank_account_detail_nakliyeci_view', args=[ba.pk]) # Nakliyeci banka hesabı detayına yönlendir
            })


    return JsonResponse({'results': results})


# === Factory - User Management ===
@login_required
def company_user_list_fabrika_view(request):
    """
    Lists company users for the factory company manager.
    """
    if not request.user.company or request.user.company.company_type != 'FABRIKA':
        messages.error(request, "Bu sayfaya erişim izniniz yok.")
        return redirect('ana_uygulama:dashboard')
    users = CustomUser.objects.filter(company=request.user.company)
    context = {'users': users, 'company_type_display': 'Fabrika', 'page_title': "Firma Kullanıcıları"}
    return render(request, 'ana_uygulama/company_user_list.html', context)

@login_required
def company_user_create_fabrika_view(request):
    """
    View for the factory company manager to add new users to their company.
    """
    if not request.user.company or request.user.company.company_type != 'FABRIKA':
        messages.error(request, "Bu sayfaya erişim izniniz yok.")
        return redirect('ana_uygulama:dashboard')
    if request.method == 'POST':
        form = CompanyUserCreationForm(request.POST)
        if form.is_valid():
            new_user = form.save(commit=False)
            new_user.company = request.user.company
            new_user.is_staff = False
            new_user.save()
            messages.success(request, f"Kullanıcı {new_user.username} başarıyla eklendi.")
            return redirect('ana_uygulama:company_user_list_fabrika_view')
        else:
            messages.error(request, "Lütfen formdaki hataları düzeltin.")
    else:
        form = CompanyUserCreationForm()
    context = {'form': form, 'company_type_display': 'Fabrika', 'page_title': "Yeni Fabrika Kullanıcısı Ekle"}
    return render(request, 'ana_uygulama/company_user_form.html', context)

# Fabrika - Kullanıcı Güncelleme
@login_required
def company_user_update_fabrika_view(request, pk):
    """
    Fabrika firma yöneticisinin şirketlerindeki mevcut kullanıcıları güncellemesi için görünüm.
    """
    if not request.user.company or request.user.company.company_type != 'FABRIKA':
        messages.error(request, "Bu sayfaya erişim izniniz yok.")
        return redirect('ana_uygulama:dashboard')
    user_to_update = get_object_or_404(CustomUser, pk=pk, company=request.user.company)
    if request.method == 'POST':
        form = CompanyUserCreationForm(request.POST, instance=user_to_update)
        if form.is_valid():
            form.save()
            messages.success(request, f"Kullanıcı {user_to_update.username} bilgileri başarıyla güncellendi.")
            return redirect('ana_uygulama:company_user_list_fabrika_view')
        else:
            messages.error(request, "Lütfen formdaki hataları düzeltin.")
    else:
        form = CompanyUserCreationForm(instance=user_to_update)
    context = {'form': form, 'page_title': "Şirket Kullanıcısını Güncelle"}
    return render(request, 'ana_uygulama/company_user_form.html', context)


# Fabrika - Kullanıcı Silme
@login_required
def company_user_delete_fabrika_view(request, pk):
    """
    Fabrika firma yöneticisinin şirketlerinden kullanıcıları silmesi için görünüm.
    """
    if not request.user.company or request.user.company.company_type != 'FABRIKA':
        messages.error(request, "Bu sayfaya erişim izniniz yok.")
        return redirect('ana_uygulama:dashboard')
    user_to_delete = get_object_or_404(CustomUser, pk=pk, company=request.user.company)
    if request.method == 'POST':
        user_to_delete.delete()
        messages.success(request, f"Kullanıcı {user_to_delete.username} başarıyla silindi.")
        return redirect('ana_uygulama:company_user_list_fabrika_view')
    context = {'user_to_delete': user_to_delete, 'page_title': "Şirket Kullanıcısını Sil"}
    return render(request, 'ana_uygulama/company_user_confirm_delete.html', context)

# Fabrika - Şirket Listeleme (Diğer Firmaları Görüntüleme)
@login_required
def company_list_for_fabrika_view(request):
    """
    Fabrika rolü için sistemdeki diğer firmaları listeleme görünümü.
    Tedarikçileri ve diğer Fabrikaları ayrı ayrı gösterir.
    """
    if not request.user.company or request.user.company.company_type != 'FABRIKA':
        messages.error(request, "Bu sayfaya erişim izniniz yok.")
        return redirect('ana_uygulama:dashboard')

    shipper_company_filter = request.GET.get('shipper_company', '').strip()
    factory_company_filter = request.GET.get('factory_company', '').strip()

    shippers = Company.objects.filter(company_type='NAKLIYECI').order_by('name')
    if shipper_company_filter:
        shippers = shippers.filter(name__icontains=shipper_company_filter)

    factories = Company.objects.filter(company_type='FABRIKA').order_by('name')
    if factory_company_filter:
        factories = factories.filter(name__icontains=factory_company_filter)

    # Exclude the user's own company from the factory list
    if request.user.company and request.user.company.company_type == 'FABRIKA':
        factories = factories.exclude(pk=request.user.company.pk)

    context = {
        'shippers': shippers,
        'factories': factories,
        'page_title': "Sistemdeki Firmalar",
        'shipper_company_filter_value': shipper_company_filter,
        'factory_company_filter_value': factory_company_filter,
    }
    return render(request, 'ana_uygulama/fabrika/company_list.html', context)

# Fabrika - Yeni Tedarikçi Oluştur
@login_required
def shipper_create_by_fabrika_view(request):
    """
    Fabrika rolü kullanıcısının yeni bir tedarikçi (nakliyeci) firması ekleme görünümü.
    """
    if not request.user.company or request.user.company.company_type != 'FABRIKA':
        messages.error(request, "Sadece fabrika firmaları yeni tedarikçi ekleyebilir.")
        return redirect('ana_uygulama:dashboard')

    if request.method == 'POST':
        form = CarrierForm(request.POST) # Using CarrierForm, but setting company_type to 'NAKLIYECI'
        if form.is_valid():
            shipper_company = form.save(commit=False)
            shipper_company.company_type = 'NAKLIYECI'
            try:
                shipper_company.save()
                messages.success(request, f"Nakliyeci '{shipper_company.full_name}' başarıyla eklendi.")
                return redirect('ana_uygulama:company_list_for_fabrika_view')
            except Exception as e:
                messages.error(request, f"Nakliyeci eklenirken bir hata oluştu: {e}")
        else:
            messages.error(request, "Lütfen formdaki hataları düzeltin.")
    else:
        form = CarrierForm() # Using CarrierForm

    context = {
        'form': form,
        'page_title': "Yeni Nakliyeci Ekle"
    }
    return render(request, 'ana_uygulama/fabrika/shipper_create_form.html', context)


# --- Fabrika - Ödemeler ---
@login_required
def payment_list_fabrika_view(request):
    """
    Fabrika için tüm ödeme kayıtlarını listeler.
    Fabrika sadece OUTGOING (giden) ödemelerini görmeli.
    """
    if not request.user.company or request.user.company.company_type != 'FABRIKA':
        messages.error(request, "Bu sayfaya erişim izniniz yok.")
        return redirect('ana_uygulama:dashboard')

    payments = Payment.objects.filter(
        recorded_by_user__company=request.user.company,
        direction='OUTGOING' # Fabrika sadece giden ödemelerini görmeli
    ).order_by('-payment_date')
    context = {'payments': payments, 'page_title': "Ödemelerim"}
    return render(request, 'ana_uygulama/fabrika/payment_list.html', context)

@login_required
def payment_create_fabrika_view(request):
    """
    Fabrikanın yeni bir ödeme kaydı oluşturmasını sağlar (outgoing).
    """
    if not request.user.company or request.user.company.company_type != 'FABRIKA':
        messages.error(request, "Bu sayfaya erişim izniniz yok.")
        return redirect('ana_uygulama:dashboard')

    if request.method == 'POST':
        form = PaymentForm(request.POST, request_user=request.user) # user'ı forma ilettik
        if form.is_valid():
            payment = form.save(commit=False)
            payment.recorded_by_user = request.user # Kaydı oluşturan kullanıcı
            payment.direction = 'OUTGOING' # Fabrika için varsayılan olarak 'Giden'
            payment.save()
            messages.success(request, "Ödeme kaydı başarıyla oluşturuldu.")
            return redirect('ana_uygulama:payment_list_fabrika_view')
        else:
            messages.error(request, "Lütfen formdaki hataları düzeltin.")
    else:
        form = PaymentForm(request_user=request.user) # user'ı forma ilettik
    context = {'form': form, 'page_title': "Yeni Ödeme Kaydı Oluştur"}
    return render(request, 'ana_uygulama/fabrika/payment_form.html', context)

@login_required
def payment_detail_fabrika_view(request, pk):
    """
    Fabrika için belirli bir ödeme kaydının detaylarını görüntüler.
    """
    payment = get_object_or_404(Payment, pk=pk, recorded_by_user__company=request.user.company, direction='OUTGOING')
    context = {'payment': payment, 'page_title': f"Ödeme Detayı - {payment.pk}"}
    return render(request, 'ana_uygulama/fabrika/payment_detail.html', context)


@login_required
def payment_update_fabrika_view(request, pk):
    """
    Fabrikanın mevcut bir ödeme kaydını güncellemesini sağlar.
    """
    payment = get_object_or_404(Payment, pk=pk, recorded_by_user__company=request.user.company, direction='OUTGOING')
    if request.method == 'POST':
        form = PaymentForm(request.POST, instance=payment, request_user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Ödeme kaydı başarıyla güncellendi.")
            return redirect('ana_uygulama:payment_list_fabrika_view')
        else:
            messages.error(request, "Lütfen formdaki hataları düzeltin.")
    else:
        form = PaymentForm(instance=payment, request_user=request.user)
    context = {'form': form, 'page_title': "Ödeme Kaydını Güncelle"}
    return render(request, 'ana_uygulama/fabrika/payment_form.html', context)

@login_required
@user_company_type_required('NAKLIYECI')
def bank_account_list_nakliyeci_view(request):
    """
    Nakliyeci rolündeki kullanıcının kendi şirketine ait banka hesaplarını listeler.
    """
    # Sadece oturum açmış kullanıcının şirketine ait banka hesaplarını filtrele
    bank_accounts = BankAccount.objects.filter(carrier__managed_by_shipper=request.user.company).order_by('-created_at')
    context = {
        'bank_accounts': bank_accounts,
        'page_title': "Banka Hesaplarım"
    }
    # Not: Bu şablon yolu sizin projenizdeki gerçek şablon yoluna göre ayarlanmalıdır.
    # Örneğin, ana_uygulama/templates/ana_uygulama/nakliyeci/bank_account_list.html
    return render(request, 'ana_uygulama/nakliyeci/bank_account_list.html', context)

@login_required
def payment_delete_fabrika_view(request, pk):
    """
    Fabrikanın bir ödeme kaydını silmesini sağlar.
    """
    payment = get_object_or_404(Payment, pk=pk, recorded_by_user__company=request.user.company, direction='OUTGOING')
    if request.method == 'POST':
        payment.delete()
        messages.success(request, "Ödeme kaydı başarıyla silindi.")
        return redirect('ana_uygulama:payment_list_fabrika_view')
    context = {'payment': payment, 'page_title': "Ödeme Kaydını Sil"}
    return render(request, 'ana_uygulama/confirm_delete.html', context)

@login_required
@user_company_type_required('NAKLIYECI')
def bank_account_create_nakliyeci_view(request):
    """
    Nakliyeci rolündeki kullanıcının kendi şirketi için yeni bir banka hesabı oluşturmasını sağlar.
    """
    if request.method == 'POST':
        form = BankAccountForm(request.POST) # request_user'ı burada geçirmeye gerek yok
        if form.is_valid():
            bank_account = form.save(commit=False)
            # BankAccount modelinde 'company' alanı yok, bu yüzden carrier üzerinden atamalıyız
            # Formdan carrier seçildiğini varsayıyorum, aksi takdirde burası değişmeli
            # Eğer BankAccount doğrudan Company'ye bağlı olacaksa models.py'yi düzeltmeliyiz.
            # Şu anki models.py'ye göre BankAccount, Carrier'a bağlı.
            # Dolayısıyla, banka hesabı oluşturulurken hangi taşıyıcıya ait olduğu belirtilmelidir.
            # Bu fonksiyon 'nakliyeci/banka-hesaplari/yeni/' URL'si ile çalışıyor ve bir carrier_id almadığı için
            # doğrudan Nakliyeci şirketinin banka hesabı olarak değil, onun yönettiği taşıyıcının banka hesabı olarak düşünülmeli.
            # Eğer Nakliyeci'nin kendi şirketinin banka hesabı olacaksa models.py'ye Company'ye ForeignKey eklenmeli.
            # Varsayım: Bu form, Nakliyeci'nin kendi şirketi için genel bir banka hesabı eklemesidir.
            # Eğer bu BankAccount, doğrudan Nakliyeci firmasına ait olacaksa, Model.py'de `company = models.ForeignKey(Company...)` eklenmeli.
            # Şu anki models.py'ye göre bu mümkün değil.
            messages.error(request, "Banka hesabı doğrudan nakliyeci firmaya atanamaz. Lütfen bir taşıyıcıya atayın.")
            return redirect('ana_uygulama:bank_account_list_nakliyeci_view') # Hata ile geri yönlendir

        else:
            messages.error(request, "Lütfen formdaki hataları düzeltin.")
    else:
        form = BankAccountForm() # GET isteği için formu hazırla
    context = {'form': form, 'page_title': "Yeni Banka Hesabı Oluştur"}
    # Şablon yolu: ana_uygulama/templates/ana_uygulama/nakliyeci/bank_account_form.html
    return render(request, 'ana_uygulama/nakliyeci/bank_account_form.html', context)


@login_required
@user_company_type_required('NAKLIYECI')
def bank_account_detail_nakliyeci_view(request, pk):
    """
    Nakliyeci rolündeki kullanıcının kendi şirketine ait belirli bir banka hesabının detaylarını görüntüler.
    """
    # Sadece kullanıcının şirketi tarafından yönetilen taşıyıcılara ait banka hesaplarını getir
    bank_account = get_object_or_404(BankAccount, pk=pk, carrier__managed_by_shipper=request.user.company)
    context = {
        'bank_account': bank_account,
        'page_title': "Banka Hesabı Detayları"
    }
    # Şablon yolu: ana_uygulama/templates/ana_uygulama/nakliyeci/bank_account_detail.html
    return render(request, 'ana_uygulama/nakliyeci/bank_account_detail.html', context)


@login_required
@user_company_type_required('NAKLIYECI')
def bank_account_update_nakliyeci_view(request, pk):
    """
    Nakliyeci rolündeki kullanıcının kendi şirketine ait mevcut bir banka hesabını günceller.
    """
    bank_account = get_object_or_404(BankAccount, pk=pk, carrier__managed_by_shipper=request.user.company)
    if request.method == 'POST':
        form = BankAccountForm(request.POST, instance=bank_account) # request_user'ı burada geçirmeye gerek yok
        if form.is_valid():
            form.save()
            messages.success(request, "Banka hesabı başarıyla güncellendi.")
            return redirect('ana_uygulama:bank_account_list_nakliyeci_view') # Liste sayfasına yönlendir
        else:
            messages.error(request, "Lütfen formdaki hataları düzeltin.")
    else:
        form = BankAccountForm(instance=bank_account)
    context = {'form': form, 'page_title': "Banka Hesabını Güncelle"}
    # Şablon yolu: ana_uygulama/templates/ana_uygulama/nakliyeci/bank_account_form.html (oluşturma formu ile aynı olabilir)
    return render(request, 'ana_uygulama/nakliyeci/bank_account_form.html', context)


@login_required
@user_company_type_required('NAKLIYECI')
def bank_account_delete_nakliyeci_view(request, pk):
    """
    Nakliyeci rolündeki kullanıcının kendi şirketine ait bir banka hesabını silmesini sağlar.
    """
    bank_account = get_object_or_404(BankAccount, pk=pk, carrier__managed_by_shipper=request.user.company)
    if request.method == 'POST':
        bank_account.delete()
        messages.success(request, "Banka hesabı başarıyla silindi.")
        return redirect('ana_uygulama:bank_account_list_nakliyeci_view') # Liste sayfasına yönlendir
    context = {
        'bank_account': bank_account,
        'page_title': "Banka Hesabını Sil",
        'object_name': bank_account.bank_name # Silinecek objenin adını şablonda kullanmak için
    }
    # Şablon yolu: ana_uygulama/templates/ana_uygulama/nakliyeci/bank_account_confirm_delete.html
    return render(request, 'ana_uygulama/nakliyeci/bank_account_confirm_delete.html', context)

@login_required
@user_company_type_required('NAKLIYECI')
def company_list_for_nakliyeci_view(request):
    """
    Nakliyeci rolündeki kullanıcının çalışabileceği aktif Fabrika firmalarını listeler.
    """
    # Sadece aktif ve 'FABRIKA' tipindeki firmaları listele
    factories = Company.objects.filter(company_type='FABRIKA', is_active=True).order_by('name')
    context = {
        'companies': factories,
        'page_title': "Çalıştığım/Potansiyel Fabrikalar"
    }
    # Not: Bu şablon yolu sizin projenizdeki gerçek şablon yoluna göre ayarlanmalıdır.
    # Örneğin, ana_uygulama/templates/ana_uygulama/nakliyeci/company_list.html
    return render(request, 'ana_uygulama/nakliyeci/company_list.html', context)
