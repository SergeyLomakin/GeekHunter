# Generated by Django 4.0.2 on 2022-02-23 10:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('company_app', '0005_remove_card_id_alter_card_company'),
    ]

    operations = [
        migrations.AddField(
            model_name='card',
            name='logo',
            field=models.ImageField(blank=True, upload_to='company_logo'),
        ),
    ]