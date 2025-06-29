# ana_uygulama/signals.py

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Payment
from django.contrib.contenttypes.models import ContentType
from .models import Invoice, Vehicle, ActivityLog

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

@receiver(post_save, sender=Invoice)
def log_invoice_creation(sender, instance, created, **kwargs):
    """Bir fatura oluşturulduğunda aktivite kaydı oluşturur."""
    if created:
        ActivityLog.objects.create(
            profile=instance.nakliyeci,
            action_type=ActivityLog.ActionTypes.INVOICE_CREATED,
            description=f"#{instance.invoice_number} numaralı fatura oluşturuldu.",
            content_object=instance
        )

@receiver(post_save, sender=Payment)
def log_payment_received(sender, instance, created, **kwargs):
    """Gelen bir ödeme kaydedildiğinde aktivite kaydı oluşturur."""
    if created and instance.direction == 'INCOMING':
        ActivityLog.objects.create(
            profile=instance.invoice.nakliyeci,
            action_type=ActivityLog.ActionTypes.PAYMENT_RECEIVED,
            description=f"#{instance.invoice.invoice_number} nolu fatura için {instance.amount} TL ödeme alındı.",
            content_object=instance
        )

@receiver(post_save, sender=Vehicle)
def log_vehicle_added(sender, instance, created, **kwargs):
    """Yeni bir araç eklendiğinde aktivite kaydı oluşturur."""
    if created:
        ActivityLog.objects.create(
            profile=instance.owner, # Modelinizde 'owner' veya 'user_profile' olabilir, ona göre düzeltin.
            action_type=ActivityLog.ActionTypes.VEHICLE_ADDED,
            description=f"{instance.plate_number} plakalı yeni bir araç envantere eklendi.",
            content_object=instance
        )