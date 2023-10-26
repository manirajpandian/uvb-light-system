from rest_framework import serializers
from .models import UserProfile  # Import your data model

class YourDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = '__all__'  # You can specify specific fields here if needed
