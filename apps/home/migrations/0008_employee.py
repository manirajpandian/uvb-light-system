# Generated by Django 3.2.6 on 2023-10-20 05:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0007_delete_cars'),
    ]

    operations = [
        migrations.CreateModel(
            name='Employee',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('mobile', models.CharField(max_length=15)),
            ],
        ),
    ]
