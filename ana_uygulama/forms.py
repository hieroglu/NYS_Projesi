# ana_uygulama/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.forms import inlineformset_factory
from .models import CustomUser, Company, Carrier, Vehicle, QuoteRequest, Shipment, Invoice, BankAccount, Payment
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import date, timedelta
from django.db.models import Q

# CustomUser forms
class CustomUserCreationForm(UserCreationForm):
    """
    Form for creating a new CustomUser.
    Can be used for admin panel or adding company users.
    """
    email = forms.EmailField(required=True, label="E-posta") # Email made mandatory

    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = UserCreationForm.Meta.fields + ('email', 'first_name', 'last_name', 'company')
        labels = {
            'username': 'Kullanıcı Adı',
            'email': 'E-posta',
            'first_name': 'Adı',
            'last_name': 'Soyadı',
            'company': 'Firma',
        }

class CustomUserChangeForm(UserChangeForm):
    """
    Form for editing CustomUser information.
    Can be used for admin panel or profile editing.
    """
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'first_name', 'last_name', 'company')
        labels = {
            'username': 'Kullanıcı Adı',
            'email': 'E-posta',
            'first_name': 'Adı',
            'last_name': 'Soyadı',
            'company': 'Firma',
        }

# Company user creation form
class CompanyUserCreationForm(UserCreationForm):
    """
    Form for creating a new user belonging to a company (CustomUser).
    Used when adding users to an existing company.
    """
    email = forms.EmailField(required=True, label="E-posta") # Email made mandatory

    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = UserCreationForm.Meta.fields + ('email', 'first_name', 'last_name', 'company')
        labels = {
            'username': 'Kullanıcı Adı',
            'email': 'E-posta',
            'first_name': 'Adı',
            'last_name': 'Soyadı',
            'company': 'Firma',
        }

# Company form
class CompanyForm(forms.ModelForm):
    """
    Form for creating and updating Company instances.
    Used for superusers to manage companies.
    """
    class Meta:
        model = Company
        fields = ['name', 'company_type', 'address', 'phone', 'email', 'tax_id_number']
        widgets = {
            'company_type': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'tax_id_number': forms.TextInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'name': 'Firma Adı',
            'company_type': 'Firma Tipi',
            'address': 'Adres',
            'phone': 'Telefon',
            'email': 'E-posta',
            'tax_id_number': 'Vergi Numarası',
        }

# Simplified form for adding Shipper by Factory
class CarrierForm(forms.ModelForm):
    """
    Form for Carriers, used by Shipper companies.
    Can also be used by Factories to add new Shipper (Nakliyeci) companies.
    """
    class Meta:
        model = Carrier
        fields = ['full_name', 'email', 'phone', 'address', 'tax_id_number']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'tax_id_number': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        labels = {
            'full_name': 'Taşıyıcı Adı/Unvanı',
            'phone': 'Telefon Numarası',
            'email': 'E-posta Adresi',
            'tax_id_number': 'Vergi Numarası/TC Kimlik No',
            'address': 'Adres',
        }

class FactoryCreationByShipperForm(forms.ModelForm):
    """
    A simplified form for Shippers to create new Factory (client) companies.
    Sets company_type to 'FABRIKA' by default.
    """
    class Meta:
        model = Company
        fields = ['name', 'address', 'phone', 'email', 'tax_id_number']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'tax_id_number': forms.TextInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'name': 'Fabrika Adı',
            'address': 'Adres',
            'phone': 'Telefon',
            'email': 'E-posta',
            'tax_id_number': 'Vergi Numarası',
        }

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.company_type = 'FABRIKA' # Hardcode company type to 'FABRIKA'
        if commit:
            instance.save()
        return instance


# Vehicle Form
class VehicleForm(forms.ModelForm):
    """
    Form for creating and updating Vehicle instances.
    Carrier field is filtered based on the current user's shipper company.
    """
    class Meta:
        model = Vehicle
        fields = [
            'carrier', 'plate_number', 'vehicle_type', 'capacity_ton', 'capacity_m3',
            'inspection_expiry_date', 'insurance_expiry_date',
            'driver_name', 'driver_phone', 'license_plate_image', 'vehicle_license_image',
            'insurance_document', 'inspection_document'
        ]
        widgets = {
            'carrier': forms.Select(attrs={'class': 'form-select select2-enable'}), # Class added for Select2
            'plate_number': forms.TextInput(attrs={'class': 'form-control'}),
            'vehicle_type': forms.Select(attrs={'class': 'form-select'}),
            'capacity_ton': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'capacity_m3': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'inspection_expiry_date': forms.DateInput(attrs={'class': 'form-control datepicker', 'type': 'date'}),
            'insurance_expiry_date': forms.DateInput(attrs={'class': 'form-control datepicker', 'type': 'date'}),
            'driver_name': forms.TextInput(attrs={'class': 'form-control'}),
            'driver_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'license_plate_image': forms.FileInput(attrs={'class': 'form-control'}),
            'vehicle_license_image': forms.FileInput(attrs={'class': 'form-control'}),
            'insurance_document': forms.FileInput(attrs={'class': 'form-control'}),
            'inspection_document': forms.FileInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'carrier': 'Taşıyıcı (Araç Sahibi)',
            'plate_number': 'Plaka Numarası',
            'vehicle_type': 'Araç Tipi',
            'capacity_ton': 'Kapasite (Ton)',
            'capacity_m3': 'Kapasite (m³)',
            'inspection_expiry_date': 'Muayene Bitiş Tarihi',
            'insurance_expiry_date': 'Sigorta Bitiş Tarihi',
            'driver_name': 'Sürücü Adı Soyadı',
            'driver_phone': 'Sürücü Telefonu',
            'license_plate_image': 'Sürücü Belgesi Görseli',
            'vehicle_license_image': 'Araç Ruhsat Görseli',
            'insurance_document': 'Sigorta Poliçesi',
            'inspection_document': 'Muayene Belgesi',
        }

    def __init__(self, *args, **kwargs):
        request_user_company = kwargs.pop('request_user_company', None)
        super().__init__(*args, **kwargs)
        if request_user_company:
            # List only carriers managed by the current shipper company
            self.fields['carrier'].queryset = Carrier.objects.filter(managed_by_shipper=request_user_company)
        else:
            # If no request_user_company (e.g., admin panel), show all carriers
            self.fields['carrier'].queryset = Carrier.objects.all()

        # Placeholder for empty selection
        self.fields['carrier'].empty_label = "Bir Taşıyıcı Seçin"


# Quote Request Form
class QuoteRequestForm(forms.ModelForm):
    """
    Form for creating and updating QuoteRequest instances.
    Used by Factory companies.
    """
    class Meta:
        model = QuoteRequest
        fields = [
            'origin', 'destination', 'load_description', 'weight', 'volume',
            'requested_pickup_date', 'delivery_date_earliest', 'delivery_date_latest'
        ]
        widgets = {
            'origin': forms.TextInput(attrs={'class': 'form-control'}),
            'destination': forms.TextInput(attrs={'class': 'form-control'}),
            'load_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'weight': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'volume': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'requested_pickup_date': forms.DateInput(attrs={'class': 'form-control datepicker', 'type': 'date'}),
            'delivery_date_earliest': forms.DateInput(attrs={'class': 'form-control datepicker', 'type': 'date'}),
            'delivery_date_latest': forms.DateInput(attrs={'class': 'form-control datepicker', 'type': 'date'}),
        }
        labels = {
            'origin': 'Yükleme Yeri',
            'destination': 'Teslimat Yeri',
            'load_description': 'Yük Açıklaması',
            'weight': 'Ağırlık (Ton)',
            'volume': 'Hacim (Metreküp)',
            'requested_pickup_date': 'İstenen Yükleme Tarihi',
            'delivery_date_earliest': 'En Erken Teslimat Tarihi',
            'delivery_date_latest': 'En Geç Teslimat Tarihi',
        }

    def clean(self):
        cleaned_data = super().clean()
        requested_pickup_date = cleaned_data.get('requested_pickup_date')
        delivery_date_earliest = cleaned_data.get('delivery_date_earliest')
        delivery_date_latest = cleaned_data.get('delivery_date_latest')

        if requested_pickup_date and requested_pickup_date < timezone.now().date():
            self.add_error('requested_pickup_date', "Yükleme tarihi bugünden eski olamaz.")

        if delivery_date_earliest and requested_pickup_date and delivery_date_earliest < requested_pickup_date:
            self.add_error('delivery_date_earliest', "En erken teslimat tarihi, yükleme tarihinden önce olamaz.")

        if delivery_date_latest and delivery_date_earliest and delivery_date_latest < delivery_date_earliest:
            self.add_error('delivery_date_latest', "En geç teslimat tarihi, en erken teslimat tarihinden önce olamaz.")

        return cleaned_data


# Offer Price Form (for Shipper to submit a price quote)
class OfferPriceForm(forms.ModelForm):
    """
    Form for Shipper to offer a price for a QuoteRequest.
    """
    offered_price = forms.DecimalField(
        max_digits=10, decimal_places=2,
        label="Teklif Edilen Fiyat (TL)",
        min_value=Decimal('0.01'),
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
    )
    shipper_notes = forms.CharField(
        label="Nakliyeci Notları (Opsiyonel)",
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )

    class Meta:
        model = QuoteRequest
        fields = ['offered_price', 'shipper_notes']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # If instance exists, show existing price and notes in the form
        if self.instance and self.instance.offered_price is not None:
            self.fields['offered_price'].initial = self.instance.offered_price
        if self.instance and self.instance.shipper_notes is not None:
            self.fields['shipper_notes'].initial = self.instance.shipper_notes


# Shipment Form (for Shipper)
class ShipmentFormNakliyeci(forms.ModelForm):
    """
    Form for creating and updating Shipment instances by Shipper companies.
    Filters 'factory' and 'assigned_vehicle' fields based on user's company.
    """
    class Meta:
        model = Shipment
        fields = [
            'factory', 'origin', 'destination', 'load_description',
            'pickup_date', 'delivery_date', 'price_for_factory', 'assigned_vehicle'
        ]
        widgets = {
            'factory': forms.Select(attrs={'class': 'form-select select2-enable', 'data-placeholder': "Müşteri Fabrika Seçin"}),
            'origin': forms.TextInput(attrs={'class': 'form-control'}),
            'destination': forms.TextInput(attrs={'class': 'form-control'}),
            'load_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'pickup_date': forms.DateInput(attrs={'class': 'form-control datepicker', 'type': 'date'}),
            'delivery_date': forms.DateInput(attrs={'class': 'form-control datepicker', 'type': 'date'}),
            'price_for_factory': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'assigned_vehicle': forms.Select(attrs={'class': 'form-select select2-enable', 'data-placeholder': "Araç Seçin (Opsiyonel)"}),
        }
        labels = {
            'factory': 'Müşteri Fabrika',
            'origin': 'Yükleme Yeri',
            'destination': 'Teslimat Yeri',
            'load_description': 'Yük Açıklaması',
            'pickup_date': 'Yükleme Tarihi',
            'delivery_date': 'Teslimat Tarihi',
            'price_for_factory': 'Faturamdaki Tutar (TL)',
            'assigned_vehicle': 'Atanan Araç',
        }

    def __init__(self, *args, **kwargs):
        request_user_company = kwargs.pop('request_user_company', None)
        super().__init__(*args, **kwargs)
        if request_user_company:
            # Show only factories managed by the shipper (or added by them)
            self.fields['factory'].queryset = Company.objects.filter(
                company_type='FABRIKA' # Assuming factories are added by shippers or superuser
            ).order_by('name')

            # Show only vehicles belonging to carriers managed by the shipper
            self.fields['assigned_vehicle'].queryset = Vehicle.objects.filter(
                carrier__managed_by_shipper=request_user_company
            ).order_by('plate_number')
            self.fields['assigned_vehicle'].required = False # Make it optional if not already

        # Add empty label by default
        self.fields['factory'].empty_label = "Müşteri Fabrika Seçin"
        self.fields['assigned_vehicle'].empty_label = "Bir Araç Seçin (Opsiyonel)"

    def clean(self):
        cleaned_data = super().clean()
        pickup_date = cleaned_data.get('pickup_date')
        delivery_date = cleaned_data.get('delivery_date')

        if pickup_date and pickup_date < timezone.now().date():
            # Only for new records, check past date
            if not self.instance or not self.instance.pk:
                self.add_error('pickup_date', "Yükleme tarihi bugünden eski olamaz.")

        if delivery_date and pickup_date and delivery_date < pickup_date:
            self.add_error('delivery_date', "Teslimat tarihi, yükleme tarihinden önce olamaz.")

        # Price check
        price = cleaned_data.get('price_for_factory')
        if price is not None and price <= 0:
            self.add_error('price_for_factory', "Sevkiyat fiyatı sıfırdan büyük olmalıdır.")

        return cleaned_data


# Shipment Status Update Form (for Shipper)
class ShipmentStatusUpdateForm(forms.ModelForm):
    """
    Form for updating only the status of a Shipment.
    """
    class Meta:
        model = Shipment
        fields = ['status']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'status': 'Sevkiyat Durumu',
        }

    def clean_status(self):
        new_status = self.cleaned_data['status']
        current_status = self.instance.status

        # Status transition rules
        status_transitions = {
            'PENDING_ASSIGNMENT': ['ASSIGNED', 'CANCELLED'],
            'ASSIGNED': ['IN_TRANSIT', 'PENDING_ASSIGNMENT', 'CANCELLED'], # Can revert to PENDING_ASSIGNMENT
            'IN_TRANSIT': ['DELIVERED', 'CANCELLED'],
            'DELIVERED': ['BILLED'],
            'BILLED': [], # Cannot change status after billing
            'CANCELLED': [], # Cannot change status after cancellation
            'COMPLETED': [], # Final status after quote acceptance
        }

        if new_status not in status_transitions.get(current_status, []):
            if current_status == new_status:
                pass # Allow transition to the same status
            elif new_status == 'CANCELLED' and current_status not in ['BILLED', 'COMPLETED']:
                pass # Can be cancelled from any status (if not billed or completed)
            else:
                raise ValidationError(
                    f"'{dict(self.instance.STATUS_CHOICES).get(current_status)}' durumundan "
                    f"'{dict(self.instance.STATUS_CHOICES).get(new_status)}' durumuna geçişe izin verilmiyor."
                )

        # Delivery date check: If status is "DELIVERED", delivery date must be present
        if new_status == 'DELIVERED' and not self.instance.delivery_date:
            self.instance.delivery_date = timezone.now().date() # Auto-set to today
            # raise ValidationError("Sevkiyat durumu 'Teslim Edildi' olarak ayarlandığında teslimat tarihi belirtilmelidir.")

        # Billing status check
        if new_status == 'BILLED' and current_status != 'DELIVERED':
            raise ValidationError("Sadece 'Teslim Edildi' durumundaki sevkiyatlar 'Faturalandırıldı' olarak işaretlenebilir.")

        return new_status


# Assign Vehicle Form
class AssignVehicleForm(forms.ModelForm):
    """
    Form for assigning a vehicle to a shipment.
    Filters vehicles based on the current user's shipper company.
    """
    assigned_vehicle = forms.ModelChoiceField(
        queryset=Vehicle.objects.none(), # Empty initially, populated in __init__
        label="Atanacak Araç",
        required=False, # Required for unassignment operation
        widget=forms.Select(attrs={'class': 'form-select select2-enable', 'data-placeholder': "Bir araç seçin..."})
    )

    class Meta:
        model = Shipment
        fields = ['assigned_vehicle']

    def __init__(self, *args, **kwargs):
        request_user_company = kwargs.pop('request_user_company', None)
        super().__init__(*args, **kwargs)
        if request_user_company and request_user_company.company_type == 'NAKLIYECI':
            self.fields['assigned_vehicle'].queryset = Vehicle.objects.filter(
                carrier__managed_by_shipper=request_user_company
            ).order_by('plate_number')
        else:
            # If no shipper company or not a shipper type, empty queryset
            self.fields['assigned_vehicle'].queryset = Vehicle.objects.none()


# Invoice Form
class InvoiceForm(forms.ModelForm):
    """
    Form for creating and updating Invoice instances.
    Calculates total amount based on amount and vat_rate.
    """
    # Instead of an existing amount field, we will take net_amount and VAT rate to calculate total_amount.
    # This form will be based on shipment price, so we don't directly display the 'amount' field.
    # However, for Django form validation, the 'amount' field needs to be present,
    # so we can keep it as a hidden field in the form or remove it from the field list.
    # When saving the model, we will assign 'shipment.price_for_factory' to the 'amount' field.

    vat_rate = forms.DecimalField(
        max_digits=5, decimal_places=2,
        label="KDV Oranı (%)",
        min_value=Decimal('0.00'),
        max_value=Decimal('100.00'),
        initial=Decimal('18.00'), # Default VAT rate
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
    )

    class Meta:
        model = Invoice
        fields = [
            'invoice_number', 'issue_date', 'due_date', 'invoice_type', 'vat_rate',
            'amount', 'status'
        ]
        widgets = {
            'invoice_number': forms.TextInput(attrs={'class': 'form-control'}),
            'issue_date': forms.DateInput(attrs={'class': 'form-control datepicker', 'type': 'date'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control datepicker', 'type': 'date'}),
            'invoice_type': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.HiddenInput(),
            'vat_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }
        labels = {
            'invoice_number': 'Fatura Numarası',
            'issue_date': 'Fatura Tarihi',
            'due_date': 'Vade Tarihi',
            'invoice_type': 'Fatura Tipi',
            'status': 'Durum',
            'amount': 'Net Tutar',
            'vat_rate': 'KDV Oranı (%)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # If the amount field is hidden, a default value can be assigned
        if self.instance and self.instance.shipment and self.instance.shipment.price_for_factory:
            self.fields['amount'].initial = self.instance.shipment.price_for_factory
        elif self.instance and self.instance.amount is not None:
             self.fields['amount'].initial = self.instance.amount

    def clean(self):
        cleaned_data = super().clean()
        issue_date = cleaned_data.get('issue_date')
        due_date = cleaned_data.get('due_date')

        if issue_date and issue_date > timezone.now().date():
            self.add_error('issue_date', "Fatura tarihi gelecek bir tarih olamaz.")

        if due_date and issue_date and due_date < issue_date:
            self.add_error('due_date', "Vade tarihi, fatura tarihinden önce olamaz.")

        # 'amount' can be made mandatory here, even if it's hidden
        amount = cleaned_data.get('amount')
        if amount is None or amount <= 0:
            # This error is for the developer, not directly for the user.
            # Since 'amount' is hidden, the user won't directly see this error.
            # Shipment price control should be done in the view.
            if not self.instance or self.instance.shipment is None or self.instance.shipment.price_for_factory is None:
                raise ValidationError("Fatura tutarı belirtilmelidir veya ilişkili sevkiyatın fiyatı olmalıdır.")

        return cleaned_data


# Bank Account Form
class BankAccountForm(forms.ModelForm):
    """
    Form for creating and updating BankAccount instances.
    """
    class Meta:
        model = BankAccount
        fields = [
            'bank_name', 'iban', 'account_owner_name', 'is_primary'
        ]
        widgets = {
            'bank_name': forms.TextInput(attrs={'class': 'form-control'}),
            'iban': forms.TextInput(attrs={'class': 'form-control'}),
            'account_owner_name': forms.TextInput(attrs={'class': 'form-control'}),
            'is_primary': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'bank_name': 'Banka Adı',
            'iban': 'IBAN',
            'account_owner_name': 'Hesap Sahibi Adı',
            'is_primary': 'Birincil Hesap mı?',
        }

    def __init__(self, *args, **kwargs):
        carrier_instance = kwargs.pop('carrier_instance', None)
        super().__init__(*args, **kwargs)
        # If a carrier instance is provided, you can restrict fields accordingly
        # Currently, there are no specific restrictions, we just take the carrier_instance.
        # You can customize fields here if needed.

class PaymentForm(forms.ModelForm):
    
    class Meta:
        model = Payment
        fields = [
            'direction', 'amount', 'payment_date', 'description',
            'invoice', 'shipment', 'counterparty_company', 'counterparty_name',
            'shipper_company' # shipper_company alanını Meta.fields'a ekledik
        ]
        
        widgets = {
            'direction': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'payment_date': forms.DateInput(attrs={'class': 'form-control datepicker', 'type': 'date'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'invoice': forms.Select(attrs={'class': 'form-select select2-enable', 'data-placeholder': "İlgili Fatura Seçin (Opsiyonel)"}),
            'shipment': forms.Select(attrs={'class': 'form-select select2-enable', 'data-placeholder': "İlgili Sevkiyat Seçin (Opsiyonel)"}),
            'counterparty_company': forms.Select(attrs={'class': 'form-select select2-enable', 'data-placeholder': "Karşı Taraf Firma Seçin (Opsiyonel)"}),
            'counterparty_name': forms.TextInput(attrs={'class': 'form-control'}),
            'shipper_company': forms.HiddenInput(), # Bu alanı gizli yaptık
        }
        labels = {
            'direction': 'Yön',
            'amount': 'Tutar',
            'payment_date': 'Tarih',
            'description': 'Açıklama',
            'invoice': 'İlişkili Fatura',
            'shipment': 'İlişkili Sevkiyat',
            'counterparty_company': 'Karşı Taraf Firma',
            'counterparty_name': 'Karşı Taraf Adı (Serbest Metin)',
            'shipper_company': 'Nakliyeci Firma', # Label for consistency
        }

    def __init__(self, *args, **kwargs):
        request_user = kwargs.pop('user', None) # request_user'ı kwargs'tan çıkar
        super().__init__(*args, **kwargs)

        if request_user and request_user.company:
            user_company = request_user.company
            
            # shipper_company alanını otomatik doldur ve devre dışı bırak
            if 'shipper_company' in self.fields: # Alanın var olduğundan emin olun
                self.fields['shipper_company'].initial = user_company.pk
                self.fields['shipper_company'].disabled = True
                self.fields['shipper_company'].required = False # Otomatik ayarlandığı için zorunlu olmasın

            # Invoice filtering: Only invoices belonging to the relevant shipper or factory company
            if user_company.company_type == 'NAKLIYECI':
                self.fields['invoice'].queryset = Invoice.objects.filter(issued_by_shipper=user_company).order_by('-issue_date')
                self.fields['shipment'].queryset = Shipment.objects.filter(shipper_company=user_company).order_by('-pickup_date')
                # List factories and other shippers as counterparties
                self.fields['counterparty_company'].queryset = Company.objects.filter(
                    Q(company_type='FABRIKA') | (Q(company_type='NAKLIYECI') & ~Q(pk=user_company.pk))
                ).order_by('name')

            elif user_company.company_type == 'FABRIKA':
                self.fields['invoice'].queryset = Invoice.objects.filter(billed_to_factory=user_company).order_by('-issue_date')
                self.fields['shipment'].queryset = Shipment.objects.filter(factory=user_company).order_by('-pickup_date')
                # List shippers and other factories as counterparties
                self.fields['counterparty_company'].queryset = Company.objects.filter(
                    Q(company_type='NAKLIYECI') | (Q(company_type='FABRIKA') & ~Q(pk=user_company.pk))
                ).order_by('name')
            else:
                # For other cases (e.g., superuser or unassigned users), show all
                self.fields['invoice'].queryset = Invoice.objects.all().order_by('-issue_date')
                self.fields['shipment'].queryset = Shipment.objects.all().order_by('-pickup_date')
                self.fields['counterparty_company'].queryset = Company.objects.all().order_by('name')

        else:
            # If no request_user or company (e.g., test environment, or anonymous user)
            # It might be better to leave Querysets empty for security.
            self.fields['invoice'].queryset = Invoice.objects.none()
            self.fields['shipment'].queryset = Shipment.objects.none()
            self.fields['counterparty_company'].queryset = Company.objects.none()

        # Placeholder for empty selection
        self.fields['invoice'].empty_label = "Fatura Seçin (Opsiyonel)"
        self.fields['shipment'].empty_label = "Sevkiyat Seçin (Opsiyonel)"
        self.fields['counterparty_company'].empty_label = "Firma Seçin (Opsiyonel)"

        # If in edit mode and some fields are already populated,
        # you might want to remove or disable empty options.
        # These parts might require more logic to adjust form behavior based on existing data.
        if self.instance.pk:
            if self.instance.invoice:
                self.fields['shipment'].queryset = Shipment.objects.filter(pk=self.instance.shipment.pk if self.instance.shipment else None)
                self.fields['shipment'].disabled = True
                self.fields['counterparty_company'].queryset = Company.objects.filter(pk=self.instance.counterparty_company.pk if self.instance.counterparty_company else None)
                self.fields['counterparty_company'].disabled = True
                self.fields['counterparty_name'].disabled = True
            elif self.instance.shipment:
                self.fields['invoice'].queryset = Invoice.objects.filter(pk=self.instance.invoice.pk if self.instance.invoice else None)
                self.fields['invoice'].disabled = True
                self.fields['counterparty_company'].queryset = Company.objects.filter(pk=self.instance.counterparty_company.pk if self.instance.counterparty_company else None)
                self.fields['counterparty_company'].disabled = True
                self.fields['counterparty_name'].disabled = True
            elif self.instance.counterparty_company or self.instance.counterparty_name:
                self.fields['invoice'].queryset = Invoice.objects.filter(pk=self.instance.invoice.pk if self.instance.invoice else None)
                self.fields['invoice'].disabled = True
                self.fields['shipment'].queryset = Shipment.objects.filter(pk=self.instance.shipment.pk if self.instance.shipment else None)
                self.fields['shipment'].disabled = True
                
        # Restrict other fields based on current payment direction
        direction = self.initial.get('direction') or self.data.get('direction')
        if direction == 'INCOMING':
            self.fields['invoice'].label = "İlişkili Fatura (Tahsilat Faturası)"
            self.fields['shipment'].label = "İlişkili Sevkiyat (Tahsilat Sevkiyatı)"
        elif direction == 'OUTGOING':
            self.fields['invoice'].label = "İlişkili Fatura (Ödeme Faturası)"
            self.fields['shipment'].label = "İlişkili Sevkiyat (Ödeme Sevkiyatı)"

        # Remove 'recorded_by_user' field from the form
        if 'recorded_by_user' in self.fields:
            del self.fields['recorded_by_user']

    def clean(self):
        cleaned_data = super().clean()
        invoice = cleaned_data.get('invoice')
        shipment = cleaned_data.get('shipment')
        direction = cleaned_data.get('direction')
        counterparty_company = cleaned_data.get('counterparty_company')
        counterparty_name = cleaned_data.get('counterparty_name')

        # Rule that record must have at least one association
        if not invoice and not shipment and not (counterparty_company or counterparty_name):
            raise ValidationError(
                "Bir ödeme/tahsilat kaydı ya bir faturaya, ya bir sevkiyata ya da bir karşı tarafa (firma/adı) bağlı olmalıdır."
            )
        
        # Counterparty and invoice consistency checks
        if invoice:
            # If there's an invoice, ensure the counterparty company matches the one on the invoice
            if direction == 'INCOMING': # If it's a collection
                if invoice.billed_to_factory != counterparty_company:
                    self.add_error('counterparty_company', "Tahsilat faturadaki faturalanan fabrika ile eşleşmelidir.")
                # Removed direct amount check here, it should be handled by update_status_based_on_payments in model.
                # if invoice.total_amount != cleaned_data.get('amount'):
                #     self.add_error('amount', "Tahsilat tutarı fatura toplam tutarına eşit olmalıdır.")
            elif direction == 'OUTGOING': # If it's a payment
                # If payment is made and invoice is not issued by our company, check counterparty
                if invoice.issued_by_shipper != self.instance.shipper_company: 
                    if invoice.issued_by_shipper != counterparty_company: 
                        self.add_error('counterparty_company', "Ödeme, faturayı kesen nakliyeci firma ile eşleşmelidir.")
                # Removed direct amount check here, it should be handled by update_status_based_on_payments in model.
                # if invoice.total_amount != cleaned_data.get('amount'):
                #     self.add_error('amount', "Ödeme tutarı fatura toplam tutarına eşit olmalıdır.")

        # Consistency check if shipment exists and counterparty company is selected
        if shipment and counterparty_company:
            if direction == 'INCOMING' and shipment.factory != counterparty_company:
                self.add_error('counterparty_company', "Tahsilat sevkiyattaki fabrika ile eşleşmelidir.")
            elif direction == 'OUTGOING' and shipment.shipper_company != counterparty_company:
                # This part is only valid for payments made to carriers,
                # in this case Carrier should be selected instead of counterparty_company.
                # In the current model structure, the shipment's counterparty is the Shipper itself,
                # so the logic here might become a bit complex.
                pass # For now, we skip this check or a more specific logic can be written.

        # If both counterparty_company and counterparty_name are entered
        if counterparty_company and counterparty_name:
            raise ValidationError("Hem 'Karşı Taraf Firma' hem de 'Karşı Taraf Adı' aynı anda girilemez. Lütfen birini seçin.")
        
        # If only counterparty_name is entered, counterparty_company must be empty
        if counterparty_name and not counterparty_company and not invoice and not shipment:
            pass # It's okay if only a free-text counterparty name is entered.
        
        return cleaned_data

