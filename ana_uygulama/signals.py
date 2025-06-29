# ana_uygulama/signals.py

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Payment, Invoice

@receiver([post_save, post_delete], sender=Payment)
def update_invoice_status_on_payment_change(sender, instance, **kwargs):
    """
    Bir Payment (Ödeme) kaydedildiğinde veya silindiğinde, 
    ilgili Invoice (Fatura) nesnesinin durumunu günceller.
    """
    # instance, değiştirilen Payment nesnesidir.
    # Bu ödemenin ilişkili olduğu faturayı alıyoruz.
    invoice_to_update = instance.invoice
    
    # Eğer fatura bir şekilde silinmişse veya yoksa, hiçbir şey yapma.
    if not invoice_to_update:
        return
        
    print(f"Sinyal tetiklendi: {invoice_to_update.invoice_number} numaralı fatura güncelleniyor...")
    
    # Invoice modelindeki durum güncelleme metodunu çağır.
    invoice_to_update.update_status_based_on_payments()