# Generated by Django 3.2.12 on 2023-09-20 14:58

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('delivery', '0004_remove_qrcodedata_receiver_check'),
    ]

    operations = [
        migrations.CreateModel(
            name='DeliveryData',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code_data', models.CharField(max_length=255)),
                ('arriving_at', models.DateTimeField(auto_now_add=True)),
                ('receiver', models.CharField(max_length=255)),
                ('qty', models.IntegerField(default=1)),
                ('checkout', models.DateTimeField(blank=True, null=True)),
                ('admin_pic', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name_plural': 'QR Scanning Data',
            },
        ),
        migrations.DeleteModel(
            name='QRCodeData',
        ),
    ]