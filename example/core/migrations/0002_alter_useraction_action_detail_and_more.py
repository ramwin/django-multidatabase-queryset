# Generated by Django 4.2.7 on 2023-12-02 02:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='useraction',
            name='action_detail',
            field=models.JSONField(default={}),
        ),
        migrations.AlterField(
            model_name='useraction',
            name='action_type',
            field=models.TextField(default=''),
        ),
    ]
