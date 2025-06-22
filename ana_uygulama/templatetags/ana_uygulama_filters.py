# ana_uygulama/templatetags/ana_uygulama_filters.py
from django import template

register = template.Library()

@register.filter
def payment_status_class(status):
    """
    Ödeme durumuna göre Bootstrap metin rengi sınıfı döndürür.
    """
    if status == 'ODENDI':
        return 'text-success'
    elif status == 'BEKLIYOR':
        return 'text-warning'
    elif status == 'GECIKTI':
        return 'text-danger'
    elif status == 'KISMI_ODEME':
        return 'text-info'
    else:
        return '' # Diğer durumlar için belirli bir sınıf yoksa boş döner