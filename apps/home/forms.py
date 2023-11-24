from django import forms
from .models import Plant



class PlantForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(PlantForm, self).__init__(*args, **kwargs)
     
        self.fields['plant_name'] = forms.CharField(
            required=False,
            widget=forms.TextInput(attrs={'placeholder': ''})
        )
        self.fields['distance'] = forms.FloatField(
            required=False,
            widget=forms.TextInput(attrs={'placeholder': ''})
        )
        self.fields['remarks'] = forms.CharField(
            required=False,
            widget=forms.TextInput(attrs={'placeholder': ''})
        )

        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})
            self.fields[field].label = ''

        self.fields['time_required'].widget = forms.HiddenInput()

    class Meta:
        model = Plant
        fields = ['plant_name', 'distance', 'time_required','remarks']
