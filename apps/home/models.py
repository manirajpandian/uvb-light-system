# -*- encoding: utf-8 -*-
"""
© copyrights BEAM Technologies
"""

from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.contrib.auth.models import User


class Plant(models.Model):
    plant_id = models.BigAutoField(primary_key=True)
    plant_name = models.CharField(max_length=255)
    distance = models.DecimalField(max_digits=10, decimal_places=2)                  # Example for distance in centimeters
    time_required = models.CharField(max_length=8)                                  # Time required in minutes
    remarks = models.CharField(max_length=255)
    createdBy = models.IntegerField(default=1)
    createdAt = models.DateTimeField(auto_now_add=True, blank=True)
    updatedBy = models.IntegerField(default=1)
    updatedAt = models.DateTimeField(auto_now=True, null=True)
    
    def delete(self, *args, **kwargs):
        # Update related House's is_active field to False
        self.house_set.update(is_active=False)
        super().delete(*args, **kwargs)

@receiver(pre_delete, sender=Plant)
def delete_related_house(sender, instance, **kwargs):
    # Update related House's is_active field to False
    instance.house_set.update(is_active=False)

class Farm(models.Model):
    farm_id=models.BigAutoField(primary_key=True)
    farm_name = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='farms')
    
class House(models.Model):
    house_id = models.CharField(max_length=10, primary_key=True)
    house_name = models.CharField(max_length=255)
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name='houses')
    plant = models.ForeignKey(Plant, on_delete=models.SET_NULL, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    memo = models.CharField(max_length=255,null=True, blank=True)
    total_line_count = models.IntegerField(default=0)
    total_pole_count = models.IntegerField(default=0)
    total_leds = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if not self.house_id:
            last_instance = House.objects.last()
            if last_instance:
                last_number = int(last_instance.house_id[1:])
                new_number = last_number + 1
            else:
                new_number = 1
            self.house_id = f'H{new_number}'
        super().save(*args, **kwargs)
    def __str__(self):
        return f"{self.house_name} ({self.house_id})"
class Line(models.Model):
    line_id = models.CharField(max_length=15, primary_key=True)
    house = models.ForeignKey(House, on_delete=models.CASCADE, related_name='lines')
    pole_count = models.PositiveIntegerField(default=0)  # Added field
    def save(self, *args, **kwargs):
        if not self.line_id:
            last_instance = Line.objects.filter(house=self.house).last()
            if last_instance:
                last_number = int(last_instance.line_id[-1])
                new_number = last_number + 1
            else:
                new_number = 1
            self.line_id = f'{self.house.house_id}L{new_number}'
        super().save(*args, **kwargs)
class Pole(models.Model):
    pole_id = models.CharField(max_length=20, primary_key=True)
    line = models.ForeignKey(Line, on_delete=models.CASCADE, related_name='poles')
    led_count = models.PositiveIntegerField(default=0)  # Added field
    def save(self, *args, **kwargs):
        if not self.pole_id:
            last_instance = Pole.objects.filter(line=self.line).last()
            if last_instance:
                last_number = int(last_instance.pole_id[-1])
                new_number = last_number + 1
            else:
                new_number = 1
            self.pole_id = f'{self.line.line_id}P{new_number}'
        super().save(*args, **kwargs)
class LED(models.Model):
    led_id = models.CharField(max_length=25, primary_key=True)
    pole = models.ForeignKey(Pole, on_delete=models.CASCADE, related_name='leds')
    is_on = models.BooleanField(default=False)
    def save(self, *args, **kwargs):
        if not self.led_id:
            last_instance = LED.objects.filter(pole=self.pole).last()
            if last_instance:
                last_number = int(last_instance.led_id[-1])
                new_number = last_number + 1
            else:
                new_number = 1
            self.led_id = f'{self.pole.pole_id}B{new_number}'
        super().save(*args, **kwargs)












