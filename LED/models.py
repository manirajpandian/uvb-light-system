from django.db import models

# Create your models here.
from django.db import models

class LineSensor(models.Model):
    date = models.DateField(auto_now_add=True)
    time = models.TimeField(auto_now_add=True)
    raspberry_pi_id = models.CharField(max_length=10)  # Add Raspberry Pi ID field
    temperature = models.DecimalField(max_digits=5, decimal_places=1)
    humidity = models.DecimalField(max_digits=5, decimal_places=1)
    soil_moisture = models.DecimalField(max_digits=5, decimal_places=1)
