from django import forms
from .models import Plant,Farm



class PlantForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(PlantForm, self).__init__(*args, **kwargs)
     
        self.fields['plant_name'] = forms.CharField(
            required=False,
            widget=forms.TextInput(attrs={'placeholder': '', 'maxlength': '50'})
        )
        self.fields['distance'] = forms.FloatField(
            required=False,
            widget=forms.NumberInput(attrs={'placeholder': '',})
        )
        self.fields['remarks'] = forms.CharField(
            required=False,
            widget=forms.TextInput(attrs={'placeholder': '', 'maxlength': '150'})
        )

        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})
            self.fields[field].label = ''

        self.fields['time_required'].widget = forms.HiddenInput()

    class Meta:
        model = Plant
        fields = ['plant_name', 'distance', 'time_required','remarks']

class FarmForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(FarmForm, self).__init__(*args, **kwargs)
        self.fields['farm_name']=forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': ''}),error_messages={'required': 'Please enter your name'})
        self.fields['address']=forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': ''}),error_messages={'required': 'Please enter your address'})

        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})
            self.fields[field].label = ''
        
        
    class Meta:
        model=Farm
        fields=['farm_name','address']

