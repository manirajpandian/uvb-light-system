from django import forms
from .models import users


class UserAddForm(forms.ModelForm):
    name = forms.CharField(
    widget=forms.TextInput(
        attrs={
            "placeholder": "Username",
            "class": "form-control"
        }
    ))
    email = forms.CharField(
    widget=forms.EmailInput(
        attrs={
            "placeholder": "Email",
            "class": "form-control"
        }
    ))
    affiliation = forms.CharField(
    widget=forms.TextInput(
        attrs={
            "placeholder": "Affiliation",
            "class": "form-control"
        }
    ))
    address = forms.CharField(
    widget=forms.TextInput(
        attrs={
            "placeholder": "Address",
            "class": "form-control"
        }
    ))
    houseName = forms.CharField(
    widget=forms.TextInput(
        attrs={
            "placeholder": "Housename",
            "class": "form-control"
        }
    ))
    plantName = forms.CharField(
    widget=forms.TextInput(
        attrs={
            "placeholder": "Plantname",
            "class": "form-control"
        }
    ))
    class Meta:
        model = users
        fields = ('name', 'email','affiliation','address','houseName', 'plantName')

