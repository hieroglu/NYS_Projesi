# Generated by Django 5.2.1 on 2025-06-28 20:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ana_uygulama', '0006_alter_vehicle_license_plate_image'),
    ]

    operations = [
        migrations.AlterField(
            model_name='invoice',
            name='status',
            field=models.CharField(choices=[('DRAFT', 'Taslak'), ('SENT', 'Gönderildi'), ('PAID', 'Ödendi'), ('PARTIALLY_PAID', 'Kısmen Ödendi'), ('OVERDUE', 'Gecikmiş'), ('VOID', 'İptal Edildi')], default='DRAFT', max_length=20, verbose_name='Durum'),
        ),
    ]
