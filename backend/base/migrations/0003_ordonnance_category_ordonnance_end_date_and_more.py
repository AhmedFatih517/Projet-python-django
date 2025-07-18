# Generated by Django 5.2.1 on 2025-05-18 03:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0002_alter_appointment_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='ordonnance',
            name='category',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='ordonnance',
            name='end_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='ordonnance',
            name='language',
            field=models.CharField(default='fr', max_length=2),
        ),
        migrations.AddField(
            model_name='ordonnance',
            name='notes',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='ordonnance',
            name='reminder',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='ordonnance',
            name='scanned_prescription',
            field=models.FileField(blank=True, null=True, upload_to='ordonnances/'),
        ),
    ]
