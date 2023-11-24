# -*- encoding: utf-8 -*-
"""
© copyrights BEAM Technologies
"""

from django.contrib import admin
from .models import Plant, Farm, House, Line, Pole, LED

# Register your models here.
admin.site.register(Plant)
admin.site.register(Farm)
admin.site.register(House)
admin.site.register(Line)
admin.site.register(Pole)
admin.site.register(LED)