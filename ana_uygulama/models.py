# ana_uygulama/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.core.validators import FileExtensionValidator
from decimal import Decimal
from django.conf import settings # AUTH_USER_MODEL için gerekli
from django.db.models import Sum # Sum için eklendi

# 1. Company (Firma) Modeli
class Company(models.Model):
    COMPANY_TYPE_CHOICES = [
        ('FABRIKA', 'Fabrika'),
        ('NAKLIYECI', 'Nakliyeci'),
    ]
    name = models.CharField(max_length=255, verbose_name="Firma Adı")
    company_type = models.CharField(max_length=10, choices=COMPANY_TYPE_CHOICES, verbose_name="Firma Tipi")
    address = models.TextField(blank=True, null=True, verbose_name="Adres")
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Telefon")
    email = models.EmailField(blank=True, null=True, verbose_name="E-posta")
    tax_id_number = models.CharField(max_length=20, blank=True, null=True, verbose_name="Vergi Numarası")
    is_active = models.BooleanField(default=True, verbose_name="Aktif mi?")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.get_company_type_display()} - {self.name}"

    class Meta:
        verbose_name = "Firma"
        verbose_name_plural = "Firmalar"
        ordering = ['name']


# 2. CustomUser (Özel Kullanıcı) Modeli
class CustomUser(AbstractUser):
    # AbstractUser'dan username, password, email, first_name, last_name gibi alanlar geliyor.
    # Biz ek olarak kullanıcıyı bir firmaya bağlayacağız.
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Bağlı Olduğu Firma")
    # on_delete=models.SET_NULL: Eğer bir firma silinirse, o firmaya bağlı kullanıcıların `company` alanı NULL olur.
    # null=True, blank=True: Bu alan boş olabilir (örneğin, sistemin ilk süper kullanıcısı bir firmaya bağlı olmayabilir).

    def __str__(self):
        return self.username # Kullanıcı adını döndürmek daha mantıklı

    class Meta:
        verbose_name = "Kullanıcı"
        verbose_name_plural = "Kullanıcılar"

# 3. Carrier (Taşıyıcı / Araç Sahibi) Modeli
class Carrier(models.Model):
    IDENTITY_DOCUMENT_CHOICES = [
        ('TCKN', 'T.C. Kimlik Numarası'),
        ('VERGI_NO', 'Vergi Kimlik Numarası'),
        ('PASAPORT', 'Pasaport Numarası'),
    ]

    managed_by_shipper = models.ForeignKey(
        'Company', # String olarak referans vermek sıralama sorunlarını azaltır
        on_delete=models.CASCADE, # Nakliyeci firma silinirse, yönettiği taşıyıcılar da silinir.
        limit_choices_to={'company_type': 'NAKLIYECI'}, # Sadece NAKLIYECI tipindeki şirketleri seçilebilir yap
        related_name='managed_carriers',
        verbose_name="Yöneten Nakliyeci Firma"
    )
    full_name = models.CharField(max_length=255, verbose_name="Adı Soyadı / Firma Ünvanı")
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Telefon Numarası")
    email = models.EmailField(blank=True, null=True, verbose_name="E-posta Adresi")
    address = models.TextField(blank=True, null=True, verbose_name="Adres")
    tax_id_number = models.CharField(max_length=20, blank=True, null=True, verbose_name="Vergi Numarası / TC Kimlik No")
    tax_plate_document = models.FileField(
        upload_to='carrier_documents/tax_plates/',
        blank=True,
        null=True,
        verbose_name="Vergi Levhası",
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png'])]
    )
    identity_document_type = models.CharField(
        max_length=10,
        choices=IDENTITY_DOCUMENT_CHOICES,
        default='TCKN',
        verbose_name="Kimlik Belgesi Tipi"
    )
    identity_document_number = models.CharField(max_length=50, blank=True, null=True, verbose_name="Kimlik Belgesi Numarası")
    identity_document_image = models.FileField(
        upload_to='carrier_documents/identity_documents/',
        blank=True,
        null=True,
        verbose_name="Kimlik Belgesi Görseli",
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png'])]
    )
    driving_license_number = models.CharField(max_length=50, blank=True, null=True, verbose_name="Ehliyet Numarası")
    license_expiry_date = models.DateField(blank=True, null=True, verbose_name="Ehliyet Geçerlilik Tarihi") # Ehliyetin son geçerlilik tarihi
    driving_license_image = models.FileField(
        upload_to='carrier_documents/driving_licenses/',
        blank=True,
        null=True,
        verbose_name="Ehliyet Görseli",
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png'])]
    )

    is_active = models.BooleanField(default=True, verbose_name="Aktif mi?")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.full_name

    class Meta:
        verbose_name = "Taşıyıcı (Araç Sahibi)"
        verbose_name_plural = "Taşıyıcılar (Araç Sahipleri)"
        ordering = ['full_name']


# 4. BankAccount Modeli (Carrier'a bağlı)
class BankAccount(models.Model):
    carrier = models.ForeignKey(
        Carrier,
        on_delete=models.CASCADE,
        related_name='bank_accounts',
        verbose_name="Taşıyıcı (Araç Sahibi)"
    )
    bank_name = models.CharField(max_length=100, verbose_name="Banka Adı")
    account_owner_name = models.CharField(max_length=255, verbose_name="Hesap Sahibi Adı")
    iban = models.CharField(max_length=34, unique=True, verbose_name="IBAN Numarası")
    is_primary = models.BooleanField(default=False, verbose_name="Birincil Hesap mı?") # Bir taşıyıcının birden fazla hesabı olabilir.
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        return f"{self.bank_name} - {self.iban} ({self.carrier.full_name})"

    class Meta:
        verbose_name = "Banka Hesabı"
        verbose_name_plural = "Banka Hesapları"
        ordering = ['carrier', '-is_primary', 'bank_name']
        unique_together = [['carrier', 'iban']] # Bir taşıyıcı için IBAN tekil olmalı


# 5. Vehicle (Araç) Modeli (Carrier'a bağlı)
class Vehicle(models.Model):
    VEHICLE_TYPE_CHOICES = [
        ('CEKICI', 'Çekici'),
        ('DORSE', 'Dorse'),
        ('KAMYON', 'Kamyon'),
        ('KAMYONET', 'Kamyonet'),
        ('MUTEAHHIT', 'Müteahhit (İş Makinesi)'),
        ('DIGER', 'Diğer'),
    ]

    carrier = models.ForeignKey(
        Carrier,
        on_delete=models.CASCADE, # Taşıyıcı silinirse araçları da silinir.
        related_name='vehicles',
        verbose_name="Araç Sahibi (Taşıyıcı)",
    )
    plate_number = models.CharField(max_length=20, unique=True, verbose_name="Plaka Numarası")
    vehicle_type = models.CharField(max_length=20, choices=VEHICLE_TYPE_CHOICES, default='KAMYON', verbose_name="Araç Tipi")
    capacity_ton = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, verbose_name="Kapasite (Ton)")
    capacity_m3 = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, verbose_name="Kapasite (m³)")

    driver_name = models.CharField(max_length=100, verbose_name="Sürücü Adı Soyadı", blank=True, null=True)
    driver_phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Sürücü Telefonu")

    license_plate_image = models.FileField(
        upload_to='vehicle_documents/plate_images/',
        blank=True,
        null=True,
        verbose_name="Sürücü Belgesi Görseli",
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png'])]
    )
    vehicle_license_image = models.FileField(
        upload_to='vehicle_documents/vehicle_licenses/',
        blank=True,
        null=True,
        verbose_name="Araç Ruhsat Görseli",
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png'])]
    )
    insurance_document = models.FileField(
        upload_to='vehicle_documents/insurances/',
        blank=True,
        null=True,
        verbose_name="Sigorta Poliçesi (PDF/Resim)",
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png'])]
    )
    inspection_document = models.FileField(
        upload_to='vehicle_documents/inspections/',
        blank=True,
        null=True,
        verbose_name="Muayene Belgesi (PDF/Resim)",
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png'])]
    )

    insurance_expiry_date = models.DateField(blank=True, null=True, verbose_name="Sigorta Bitiş Tarihi")
    inspection_expiry_date = models.DateField(blank=True, null=True, verbose_name="Muayene Bitiş Tarihi")

    is_active = models.BooleanField(default=True, verbose_name="Aktif mi?")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def is_inspection_expired(self):
        """Checks if the inspection date has passed."""
        if not self.inspection_expiry_date:
            return False
        return self.inspection_expiry_date < timezone.now().date()

    def is_insurance_expired(self):
        """Checks if the insurance date has passed."""
        if not self.insurance_expiry_date:
            return False
        return self.insurance_expiry_date < timezone.now().date()

    def __str__(self):
        return f"{self.plate_number} (Şoför: {self.driver_name if self.driver_name else 'Yok'})"

    class Meta:
        verbose_name = "Araç"
        verbose_name_plural = "Araçlar"
        ordering = ['plate_number']

    def get_managing_shipper(self):
        """Returns the shipper company managing this vehicle."""
        if self.carrier:
            return self.carrier.managed_by_shipper
        return None


# 6. QuoteRequest (Fiyat Teklifi Talebi) Modeli
class QuoteRequest(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Beklemede'),
        ('QUOTED', 'Fiyat Verildi'),
        ('ACCEPTED', 'Kabul Edildi'),
        ('REJECTED', 'Reddedildi'),
        ('COMPLETED', 'Tamamlandı (İşe Dönüştü)'), # Teklif işe dönüştürüldüğünde
    ]

    factory = models.ForeignKey(
        Company,
        on_delete=models.CASCADE, # Fabrika silinirse talepleri de silinir.
        limit_choices_to={'company_type': 'FABRIKA'},
        related_name='quote_requests_as_factory',
        verbose_name="Talep Eden Fabrika"
    )
    created_by_user = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='quote_requests_created',
        verbose_name="Oluşturan Kullanıcı"
    )
    # Teklif veren nakliyeci firma (Sadece bir tane olabilir)
    priced_by_shipper_company = models.ForeignKey(
        Company,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        limit_choices_to={'company_type': 'NAKLIYECI'},
        related_name='given_quotes',
        verbose_name="Fiyat Veren Nakliyeci Firma"
    )

    origin = models.CharField(max_length=255, verbose_name="Yükleme Yeri (Çıkış)")
    destination = models.CharField(max_length=255, verbose_name="Teslimat Yeri (Varış)")
    load_description = models.TextField(verbose_name="Yük Açıklaması (Cinsi, Ağırlığı, Hacmi vb.)")
    weight = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, verbose_name="Ağırlık (kg)")
    volume = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, verbose_name="Hacim (m³)")
    requested_pickup_date = models.DateField(verbose_name="Talep Edilen Yükleme Tarihi")
    delivery_date_earliest = models.DateField(null=True, blank=True, verbose_name="En Erken Teslimat Tarihi")
    delivery_date_latest = models.DateField(null=True, blank=True, verbose_name="En Geç Teslimat Tarihi")

    # Nakliyecinin verdiği fiyat
    offered_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Teklif Edilen Fiyat (Nakliyeci)")
    shipper_notes = models.TextField(blank=True, null=True, verbose_name="Nakliyeci Notları")

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING', verbose_name="Durum")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma Tarihi")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Son Güncellenme Tarihi")


    def __str__(self):
        return f"{self.factory.name} -> {self.origin} - {self.destination} ({self.get_status_display()})"

    class Meta:
        verbose_name = "Fiyat Teklifi Talebi"
        verbose_name_plural = "Fiyat Teklifi Talepleri"
        ordering = ['-created_at']


# 7. Shipment (İş / Sevkiyat) Modeli
class Shipment(models.Model):
    STATUS_CHOICES = [
        ('PENDING_ASSIGNMENT', 'Atama Bekliyor'), # Tekliften sonra veya manuel oluşturulduğunda ilk durum
        ('ASSIGNED', 'Taşıyıcıya Atandı'),
        ('IN_TRANSIT', 'Yolda'),
        ('DELIVERED', 'Teslim Edildi'),
        ('BILLED', 'Faturalandırıldı'), # Fatura kesildiğinde
        ('COMPLETED', 'Tamamlandı'), # Hem teslim edildi hem de tüm süreç bitti (fatura vs.)
        ('CANCELLED', 'İptal Edildi'),
    ]
    # Bu iş bir tekliften mi geldi, yoksa manuel mi oluşturuldu?
    quote_request = models.OneToOneField(
        QuoteRequest,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name="İlişkili Fiyat Teklifi",
        related_name='shipment' # Tekliften sevkiyata doğru ters ilişki için
    )
    # Manuel giriş için fabrika bilgisi (Eğer quote_request yoksa bu alan doldurulmalı)
    factory = models.ForeignKey(
        Company,
        on_delete=models.PROTECT, # Fabrika silinirse sevkiyatları koru
        limit_choices_to={'company_type': 'FABRIKA'},
        related_name='shipments_as_customer_factory',
        verbose_name="Müşteri Fabrika"
    )
    # Bu işi hangi Nakliyeci firma yönetiyor
    shipper_company = models.ForeignKey(
        Company,
        on_delete=models.PROTECT, # Nakliyeci silinirse sevkiyatları koru
        limit_choices_to={'company_type': 'NAKLIYECI'},
        related_name='shipments_managed_by_shipper',
        verbose_name="Nakliyeci Firma"
    )
    origin = models.CharField(max_length=255, verbose_name="Yükleme Yeri")
    destination = models.CharField(max_length=255, verbose_name="Teslimat Yeri")
    load_description = models.TextField(verbose_name="Yük Açıklaması")
    pickup_date = models.DateField(verbose_name="Yükleme Tarihi")
    delivery_date = models.DateField(null=True, blank=True, verbose_name="Teslim Tarihi")
    assigned_vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name="Atanan Araç",
        related_name='assigned_shipments' # Aracın atandığı sevkiyatları izlemek için
    )
    price_for_factory = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Fabrikaya Kesilecek Fiyat (TL)")
    cost_for_shipper = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Nakliyeciye Maliyet (Taşıyıcıya Ödenen) (TL)")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING_ASSIGNMENT', verbose_name="Durum")
    created_by_user = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='shipments_created',
        verbose_name="Oluşturan Nakliyeci Kullanıcı"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma Tarihi")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Son Güncelleme Tarihi")

    @property
    def kar_tutari(self):
        """Calculates the net profit of the shipment."""
        if self.price_for_factory is not None and self.cost_for_shipper is not None:
            return self.price_for_factory - self.cost_for_shipper
        return Decimal('0.00')

    @property
    def kar_orani(self):
        """Calculates the profit margin of the shipment as a percentage."""
        if self.price_for_factory and self.price_for_factory > 0 and self.cost_for_shipper is not None:
            kar = self.price_for_factory - self.cost_for_shipper
            return (kar / self.price_for_factory) * Decimal('100')
        return Decimal('0.00')

    def __str__(self):
        return f"Sevkiyat #{self.id}: {self.factory.name} - {self.origin} -> {self.destination}"

    class Meta:
        verbose_name = "İş / Sevkiyat"
        verbose_name_plural = "İşler / Sevkiyatlar"
        ordering = ['-created_at']


# 8. Invoice (Fatura) Modeli
class Invoice(models.Model):
    TYPE_CHOICES = [
        ('E_FATURA', 'E-Fatura'),
        ('E_ARSIV', 'E-Arşiv Faturası'),
    ]
    STATUS_CHOICES = [
        ('DRAFT', 'Taslak'),
        ('SENT', 'Gönderildi'),
        ('PAID', 'Ödendi'),
        ('PARTIALLY_PAID', 'Kısmen Ödendi'),
        ('OVERDUE', 'Gecikmiş'),
        ('VOID', 'İptal Edildi'),
    ]

    billed_to_factory = models.ForeignKey(
        'Company',
        on_delete=models.PROTECT,
        limit_choices_to={'company_type': 'FABRIKA'},
        related_name='invoices_to_factory',
        verbose_name="Faturalanan Fabrika"
    )
    issued_by_shipper = models.ForeignKey(
        'Company',
        on_delete=models.PROTECT,
        limit_choices_to={'company_type': 'NAKLIYECI'},
        related_name='invoices_from_shipper',
        verbose_name="Faturayı Kesen Nakliyeci"
    )

    shipment = models.ForeignKey(
        'Shipment',
        on_delete=models.SET_NULL, # Fatura silinse bile Shipment objesi silinmez, sadece bu ilişki NULL olur.
        null=True, blank=True,
        verbose_name="İlişkili Sevkiyat"
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name="Oluşturan Kullanıcı"
    )

    invoice_number = models.CharField(max_length=50, unique=True, verbose_name="Fatura Numarası")
    invoice_type = models.CharField(max_length=10, choices=TYPE_CHOICES, verbose_name="Fatura Tipi")
    issue_date = models.DateField(default=timezone.now, verbose_name="Düzenlenme Tarihi")
    due_date = models.DateField(verbose_name="Vade Tarihi")
    # 'amount' alanı manuel girilen faturalar için kullanılabilir.
    # Eğer her fatura bir sevkiyattan geliyorsa, bu alanı kaldırmayı düşünebiliriz.
    # Şimdilik, sevkiyat bağlantısı olmayan faturalar için tutarı manuel girmeye izin verelim.
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Net Tutar (KDV Hariç)", default=Decimal('0.00'))

    vat_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="KDV Oranı (%)",
        help_text="Faturaya uygulanacak KDV oranı (örneğin %18 için 18.00 girin)"
    )
    total_vat_amount = models.DecimalField(
        max_digits=10, decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Toplam KDV Tutarı",
        blank=True, null=True
    )
    total_amount = models.DecimalField(
        max_digits=10, decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Toplam Tutar (KDV Dahil)",
        blank=True, null=True
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT', verbose_name="Durum")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma Tarihi")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Son Güncelleme Tarihi")

    class Meta:
        verbose_name = "Fatura"
        verbose_name_plural = "Faturalar"
        ordering = ['-issue_date', '-created_at']

    def __str__(self):
        return f"Fatura #{self.invoice_number} ({self.billed_to_factory.name})"

    def save(self, *args, **kwargs):
        # Eğer fatura bir sevkiyata bağlıysa ve sevkiyatın fiyatı varsa, net tutarı buradan al.
        # Aksi takdirde, 'amount' alanı zaten manuel olarak girilmiş olabilir.
        if self.shipment and self.shipment.price_for_factory is not None:
            net_amount_for_calc = self.shipment.price_for_factory
        else:
            net_amount_for_calc = self.amount # Eğer sevkiyat yoksa veya fiyat boşsa, manuel amount kullan

        vat_rate_decimal = self.vat_rate / Decimal('100')

        self.total_vat_amount = net_amount_for_calc * vat_rate_decimal
        self.total_amount = net_amount_for_calc + self.total_vat_amount
        self.update_status_based_on_payments()

        super().save(*args, **kwargs)

    # Bir fatura silindiğinde ilişkili sevkiyatın durumunu güncelleyecek metot
    def delete(self, *args, **kwargs):
        related_shipment = self.shipment
        super().delete(*args, **kwargs) # Fatura objesini önce sil

        # Faturayla ilişkili bir sevkiyat varsa ve bu sevkiyatın durumu 'BILLED' ise
        # Fatura silindikten sonra, sevkiyatın faturalandırılmış olma durumunu geri al.
        if related_shipment and related_shipment.status == 'BILLED':
            related_shipment.status = 'DELIVERED' # Sevkiyatı 'Teslim Edildi' durumuna geri döndür
            related_shipment.save()
            print(f"Invoice deleted: Shipment ID {related_shipment.pk} status updated to 'DELIVERED'.")

    def get_status_display(self):
        return dict(self.STATUS_CHOICES).get(self.status, self.status)

    def get_invoice_type_display(self):
        return dict(self.TYPE_CHOICES).get(self.invoice_type, self.invoice_type)
    
    def update_status_based_on_payments(self):
        """
        Updates the status of the invoice based on its payment history.
        """
        # Ensure Decimal is imported for calculations
        from decimal import Decimal

        total_paid_amount = self.payment_set.filter(direction='INCOMING').aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')

        if total_paid_amount >= self.total_amount:
            self.status = 'PAID'
            return # İşlem tamamlandı, fonksiyondan çık.

        if total_paid_amount > 0:
            self.status = 'PARTIALLY_PAID'
            return # İşlem tamamlandı, fonksiyondan çık.

    # Eğer buraya kadar geldiysek, hiç ödeme yapılmamış demektir.
    # Şimdi vadesinin geçip geçmediğini kontrol edelim.
        if self.due_date and self.due_date < timezone.localdate():
            self.status = 'OVERDUE'
        else:
        # Vadesi geçmemiş ve ödeme yapılmamışsa, durumu 'Gönderildi'dir.
            self.status = 'SENT'


# 9. Payment (Ödeme/Tahsilat) Modeli
class Payment(models.Model):
    DIRECTION_CHOICES = [
        ('INCOMING', 'Gelen Ödeme (Tahsilat)'),
        ('OUTGOING', 'Giden Ödeme (Ödeme)'),
    ]
    shipper_company = models.ForeignKey('Company', on_delete=models.CASCADE, related_name='payments_as_shipper', verbose_name="Nakliyeci Firma")
    direction = models.CharField(max_length=10, choices=DIRECTION_CHOICES, verbose_name="Ödeme Yönü")
    invoice = models.ForeignKey('Invoice', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="İlişkili Fatura")
    shipment = models.ForeignKey('Shipment', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="İlişkili Sevkiyat")

    # Karşı taraf bilgisi (ya firma ya da serbest metin)
    counterparty_company = models.ForeignKey(
        'Company',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payments_with_counterparty',
        verbose_name="Karşı Taraf Firma (Fabrika/Diğer)"
    )
    counterparty_name = models.CharField(max_length=255, blank=True, null=True, verbose_name="Karşı Taraf Adı (Serbest Metin)")

    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Tutar")
    payment_date = models.DateField(default=timezone.now, verbose_name="Ödeme Tarihi")
    description = models.TextField(blank=True, null=True, verbose_name="Açıklama")
    recorded_by_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Kaydeden Kullanıcı")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def status(self):
        """
        Determines the payment status.
        If linked to an invoice, determined by invoice status and amount.
        If no associated invoice, it is generally considered 'Paid'.
        """
        if self.invoice:
            # Bu ödemenin faturanın toplamını karşılayıp karşılamadığına bakarak durum belirlenebilir.
            # Ancak fatura durumu direkt Payment objesinin bir özelliği olmamalı,
            # Invoice modelinin kendi `update_status_based_on_payments` metodu daha uygun.
            # Burada sadece ödemenin kendisi ile ilgili bir durum dönebiliriz (örn: tamamlandı).
            return 'ODENDI' # Basitçe her ödeme kaydedildiğinde 'Ödendi' olarak kabul edelim
        else:
            return 'ODENDI'

    def get_status_display(self):
        """
        Returns a readable text corresponding to the codes returned by the status property.
        """
        status_map = {
            'ODENDI': 'Ödendi',
            'BEKLIYOR': 'Bekliyor', # Bu Payment objesi için geçerli olmayabilir
            'GECIKTI': 'Gecikti', # Bu Payment objesi için geçerli olmayabilir
            'KISMI_ODEME': 'Kısmi Ödeme', # Bu Payment objesi için geçerli olmayabilir
        }
        return status_map.get(self.status, 'Bilinmiyor')

    def __str__(self):
        direction_display = self.get_direction_display()
        if self.invoice:
            return f"{direction_display}: {self.amount} TL - Fatura #{self.invoice.invoice_number}"
        elif self.shipment:
            return f"{direction_display}: {self.amount} TL - Sevkiyat #{self.shipment.tracking_number}"
        else:
            return f"{direction_display}: {self.amount} TL - {self.counterparty_company.name if self.counterparty_company else self.counterparty_name or 'Serbest Ödeme'}"

    class Meta:
        verbose_name = "Ödeme"
        verbose_name_plural = "Ödemeler"
        ordering = ['-payment_date', '-created_at']

