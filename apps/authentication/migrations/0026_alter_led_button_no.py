# Generated by Django 3.2.6 on 2024-01-03 19:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0025_alter_led_button_no'),
    ]

    operations = [
        migrations.AlterField(
            model_name='led',
            name='button_no',
            field=models.PositiveIntegerField(),
        ),
    ]
