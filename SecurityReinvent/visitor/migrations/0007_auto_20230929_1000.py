# Generated by Django 3.2.12 on 2023-09-29 15:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('visitor', '0006_auto_20230929_0954'),
    ]

    operations = [
        migrations.DeleteModel(
            name='ApprovalStatus',
        ),
        migrations.AddField(
            model_name='visitordata',
            name='approval_status',
            field=models.CharField(default='Requested', max_length=20),
        ),
    ]