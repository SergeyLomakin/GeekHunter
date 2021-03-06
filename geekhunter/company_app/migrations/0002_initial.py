# Generated by Django 4.0.1 on 2022-01-27 20:36

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('employee_app', '0001_initial'),
        ('company_app', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='offer',
            name='resume',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='offers', to='employee_app.resume'),
        ),
        migrations.AddField(
            model_name='offer',
            name='vacancy',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='offers', to='company_app.vacancy'),
        ),
        migrations.AddField(
            model_name='hrmanager',
            name='company',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='companies', to='company_app.company'),
        ),
        migrations.AddField(
            model_name='favoriteresume',
            name='hr_manager',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='hr_managers', to='company_app.hrmanager'),
        ),
        migrations.AddField(
            model_name='favoriteresume',
            name='resume',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='fav_resumes', to='employee_app.resume'),
        ),
        migrations.AddField(
            model_name='card',
            name='company',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='card', to='company_app.company'),
        ),
    ]
