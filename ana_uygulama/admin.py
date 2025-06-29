# ana_uygulama/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin # CustomUser için
from .models import (
    Company, CustomUser, Carrier, BankAccount, Vehicle, 
    QuoteRequest, Shipment, Invoice, Payment )
from .models import ActivityLog
from .models import Expense

# CustomUser için admin ayarlarını özelleştirebiliriz
class CustomUserAdmin(UserAdmin):
    # UserAdmin'in varsayılan fieldset'lerini alıp 'company' alanını ekleyelim
    # UserAdmin.fieldsets'i kopyalayıp kendi fieldset'lerimizi oluşturabiliriz.
    # Ya da basitçe list_display'e ekleyebiliriz.
    # Şimdilik sadece temel field'ları gösterelim.
    # Daha detaylı fieldset'ler için Django dokümantasyonuna bakabilirsiniz.
    model = CustomUser
    list_display = ['username', 'email', 'first_name', 'last_name', 'is_staff', 'company']
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('company',)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('company',)}),
    )

class BankAccountInline(admin.TabularInline):
    model = BankAccount
    extra = 1

class CarrierAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'managed_by_shipper', 'phone', 'email', 'tax_id_number', 'is_active')
    list_filter = ('is_active', 'bank_accounts__bank_name')
    search_fields = ('full_name', 'tax_id_number', 'phone', 'email')
    raw_id_fields = ('managed_by_shipper',)
    inlines = [BankAccountInline]

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('expense_date', 'profile', 'category', 'amount', 'description')
    list_filter = ('category', 'expense_date', 'profile')
    search_fields = ('description',)

# VehicleAdmin (Bir önceki yanıtta tanımlamıştık)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ('plate_number', 'carrier_name_admin', 'get_managing_shipper_admin', 'driver_name', 'inspection_expiry_date')
    list_filter = ('carrier__managed_by_shipper__name', 'carrier__full_name')
    search_fields = ('plate_number', 'driver_name', 'carrier__full_name')
    raw_id_fields = ('carrier',)
    
    @admin.display(description='Araç Sahibi (Taşıyıcı)', ordering='carrier__full_name')
    def carrier_name_admin(self, obj):
        if obj.carrier:
            return obj.carrier.full_name
        return "-"

    @admin.display(description='Yöneten Nakliyeci', ordering='carrier__managed_by_shipper__name')
    def get_managing_shipper_admin(self, obj):
        if obj.carrier and obj.carrier.managed_by_shipper:
            return obj.carrier.managed_by_shipper.name
        return "-"

# --- BU SATIRLARIN OLDUĞUNDAN EMİN OLUN ---
admin.site.register(Carrier, CarrierAdmin)
admin.site.register(Vehicle, VehicleAdmin)
admin.site.register(BankAccount) # BankAccount'u da ayrı yönetmek isterseniz
# --- ---

# ... (QuoteRequestAdmin, ShipmentAdmin, InvoiceAdmin, PaymentAdmin aynı kalacak) ...

#admin.site.register(Carrier, CarrierAdmin) # Carrier'ı kaydet
# VehicleAdmin zaten kayıtlıydı, değişiklikler etkili olacak.
# Eğer VehicleAdmin daha önce register edilmemişse: admin.site.register(Vehicle, VehicleAdmin)

class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'company_type', 'email', 'phone')
    list_filter = ('company_type',)
    search_fields = ('name', 'email')

class VehicleAdmin(admin.ModelAdmin):
    list_display = ('plate_number', 'driver_name', 'owned_by_shipper', 'inspection_expiry_date', 'insurance_expiry_date')
    list_filter = ('owned_by_shipper',)
    search_fields = ('plate_number', 'driver_name')
    raw_id_fields = ('owned_by_shipper',) # Çok fazla firma olunca dropdown yerine ID ile arama sağlar

class QuoteRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'factory', 'origin', 'destination', 'status', 'created_at', 'offered_price')
    list_filter = ('status', 'factory', 'requested_pickup_date')
    search_fields = ('factory__name', 'origin', 'destination')
    raw_id_fields = ('factory', 'created_by_user')
    readonly_fields = ('created_at',)

class ShipmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'factory', 'shipper_company', 'origin', 'destination', 'status', 'pickup_date', 'assigned_vehicle')
    list_filter = ('status', 'shipper_company', 'factory', 'pickup_date')
    search_fields = ('factory__name', 'shipper_company__name', 'origin', 'destination')
    raw_id_fields = ('factory', 'shipper_company', 'assigned_vehicle', 'quote_request', 'created_by_user')
    readonly_fields = ('created_at',)

class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'billed_to_factory', 'issued_by_shipper', 'total_amount', 'issue_date', 'due_date', 'status')
    list_filter = ('status', 'invoice_type', 'issued_by_shipper', 'billed_to_factory')
    search_fields = ('invoice_number', 'billed_to_factory__name', 'issued_by_shipper__name')
    raw_id_fields = ('billed_to_factory', 'issued_by_shipper', 'shipment')
    readonly_fields = ('created_at',)

class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'shipper_company', 'direction', 'amount', 'payment_date', 'invoice', 'shipment', 'counterparty_company', 'counterparty_name')
    list_filter = ('direction', 'shipper_company', 'payment_date')
    search_fields = ('shipper_company__name', 'invoice__invoice_number', 'counterparty_name')
    raw_id_fields = ('shipper_company', 'invoice', 'shipment', 'counterparty_company', 'recorded_by_user')
    readonly_fields = ('created_at',)

# Sadece bir VehicleAdmin ve bir CarrierAdmin tanımı bırakılmalı, tekrar eden tanımlar kaldırıldı.
# Ayrıca VehicleAdmin ve CarrierAdmin tanımlarının sadece bir tane olduğundan emin ol.

@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'profile', 'action_type', 'description', 'content_object')
    list_filter = ('action_type', 'profile')

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Company, CompanyAdmin)
admin.site.register(QuoteRequest, QuoteRequestAdmin)
admin.site.register(Shipment, ShipmentAdmin)
admin.site.register(Invoice, InvoiceAdmin)
admin.site.register(Payment, PaymentAdmin)