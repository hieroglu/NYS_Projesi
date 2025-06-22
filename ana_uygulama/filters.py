import django_filters
from django import forms
from ana_uygulama.models import Shipment

class ShipmentFilter(django_filters.FilterSet):
    factory_name = django_filters.CharFilter(...)
    origin = django_filters.CharFilter(...)
    destination = django_filters.CharFilter(...)
    status = django_filters.ChoiceFilter(...)
    assigned_vehicle_plate = django_filters.CharFilter(...)
    pickup_date_after = django_filters.DateFilter(...)
    pickup_date_before = django_filters.DateFilter(...)
    origin = django_filters.CharFilter(lookup_expr='icontains', label='Yükleme Yeri')
    destination = django_filters.CharFilter(lookup_expr='icontains', label='Teslimat Yeri')
    status = django_filters.ChoiceFilter(choices=Shipment.STATUS_CHOICES, label='Durum', empty_label="Tüm Durumlar")
    assigned_vehicle_plate = django_filters.CharFilter(
        field_name='assigned_vehicle__plate_number',
        lookup_expr='icontains',
        label='Atanan Araç Plakası'
    )
    pickup_date_after = django_filters.DateFilter(
        field_name='pickup_date', 
        lookup_expr='gte',
        label='Yükleme Tarihi (Başlangıç)',
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control form-control-sm'})
    )
    pickup_date_before = django_filters.DateFilter(
        field_name='pickup_date', 
        lookup_expr='lte',
        label='Yükleme Tarihi (Bitiş)',
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control form-control-sm'})
    )

    class Meta:
        model = Shipment
        fields = ['factory_name', 'origin', 'destination', 'status', 
                  'assigned_vehicle_plate', 'pickup_date_after', 'pickup_date_before']