# -*- encoding: utf-8 -*-
"""
© copyrights BEAM Technologies
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models.signals import pre_delete
from django.dispatch import receiver



class Profile(models.Model):
    address = models.CharField(max_length=150,null=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    forget_password_token = models.CharField(max_length=100, null=True)
    role_id = models.CharField(max_length=100, null=True)
    mapped_under = models.IntegerField(default=0,null=True)
    image = models.ImageField(upload_to='images/', null=True, blank=True)
    username = models.CharField(max_length=100,null=True)
    token_expiration_time = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_created=True, default=timezone.now)

    def __str__(self):
        return self.user.username


class Company(models.Model):
    company_name = models.CharField(max_length=200)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    company_address = models.CharField(max_length=150,null=True)
    phone = models.CharField(max_length=30,null=True)
    website = models.URLField(blank=True,null=True)
    description = models.TextField(null=True)
    created_at = models.DateTimeField(auto_created=True, default=timezone.now)

    def __str__(self):
        return self.user.username
    


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


class Farm(models.Model):
    farm_id=models.BigAutoField(primary_key=True)
    farm_name = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='farms')
    is_active = models.BooleanField(default=True)
    
class House(models.Model):
    house_id = models.CharField(max_length=10, primary_key=True)
    house_name = models.CharField(max_length=255)
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name='houses')
    plant = models.ForeignKey(Plant, on_delete=models.SET_NULL, null=True, blank=True)
    user = models.ManyToManyField(User, blank=True)
    memo = models.CharField(max_length=255,null=True, blank=True)
    total_line_count = models.IntegerField(default=0)
    total_pole_count = models.IntegerField(default=0)
    total_leds = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if not self.house_id:
            last_instance = House.objects.last()
            if last_instance:
                last_number = int(last_instance.house_id)
                new_number = last_number + 1
            else:
                new_number = 1
            self.house_id = f'{new_number}'
        super().save(*args, **kwargs)
    def __str__(self):
        return f"{self.house_name} ({self.house_id})"
    
class Line(models.Model):
    line_id = models.CharField(max_length=15, primary_key=True)
    house = models.ForeignKey(House, on_delete=models.CASCADE, related_name='lines')
    pole_count = models.PositiveIntegerField(default=0) 

    def save(self, *args, **kwargs):
        if not self.line_id:
            last_instance = Line.objects.filter(house=self.house).last()
            if last_instance:
                last_number = int(last_instance.line_id[-1])
                new_number = last_number + 1
            else:
                new_number = 1
            self.line_id = f'{self.house.house_id}-{new_number}'
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
            self.pole_id = f'{self.line.line_id}-{new_number}'
        super().save(*args, **kwargs)
        
class LED(models.Model):
    led_id = models.CharField(max_length=25, primary_key=True)
    pole = models.ForeignKey(Pole, on_delete=models.CASCADE, related_name='leds')
    is_on = models.BooleanField(default=False)
    button_no = models.PositiveIntegerField(unique=False)
    led_on_date= models.DateTimeField(null=True, blank=True)
    led_off_date = models.DateTimeField(null=True, blank=True)
    rasp = models.ForeignKey('Rasp', on_delete=models.SET_NULL, related_name='led', null=True, blank=True)

    def save(self, *args, **kwargs):  
        
        if not self.led_id:
            last_instance = LED.objects.filter(pole=self.pole).last()
            if last_instance:
                last_number = int(last_instance.led_id.split('-')[-1])
                new_number = last_number + 1
            else:
                new_number = 1
            self.led_id = f'{self.pole.pole_id}-{new_number}'

        if not self.button_no:  
            # Check if button_no is not set or it's a new instance
            last_instance_same_house = LED.objects.filter(pole__line__house=self.pole.line.house).order_by('-led_id').first()
            if last_instance_same_house:
                new_button_no = (last_instance_same_house.button_no % 23) + 1
            else:
                new_button_no = 1
            self.button_no = new_button_no

        super().save(*args, **kwargs)




class Rasp(models.Model):
    rbi = models.CharField(max_length=20, primary_key=True)
    is_assigned = models.CharField(max_length=200,null=True, blank=True)
    rasp_status  = models.CharField(max_length=200,null=True, blank=True)
    

class data(models.Model):
    raspberry_id = models.ForeignKey(Rasp, on_delete=models.CASCADE, related_name='raspberry_instances')
    date = models.DateTimeField()
    temperature = models.FloatField()
    humidity = models.FloatField()
    soil_moisture = models.FloatField()

    class Meta:
        unique_together = ('date', 'raspberry_id')
    