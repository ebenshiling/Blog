# Generated by Django 5.0.4 on 2024-05-04 10:39

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cart', '0003_remove_cartitem_variation'),
        ('store', '0004_alter_variation_variation_category'),
    ]

    operations = [
        migrations.DeleteModel(
            name='variation',
        ),
    ]
