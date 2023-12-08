from django import forms
from apps.authentication.models import Plant



class PlantForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
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

    def save(self, commit=True, *args, **kwargs):
        instance = super(PlantForm, self).save(commit=False, *args, **kwargs)
        instance.createdBy = self.request.user.id if self.request and self.request.user else 1 
        if commit:
            instance.save()
        return instance

    class Meta:
        model = Plant
        fields = ['plant_name', 'distance', 'time_required','remarks']


