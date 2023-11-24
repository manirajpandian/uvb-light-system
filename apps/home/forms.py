from django import forms
from .models import User,Plant


class UserAddForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(UserAddForm, self).__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'placeholder': ''})
        self.fields['email'].widget.attrs.update({'placeholder': ''})
        self.fields['mapped_under'].widget = forms.HiddenInput()
        CHOICES = [(1, '管理者'), (2, 'ユーザ')]
        self.fields['role_id'] = forms.ChoiceField(choices=CHOICES, initial='option1', widget=forms.Select(attrs={'class': 'form-control'}), label="")

        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})
            self.fields[field].label = ''

    class Meta:
        model = User
        fields = ('username', 'email', 'role_id', 'mapped_under')

class PlantForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(PlantForm, self).__init__(*args, **kwargs)
        self.fields['plant_name'] = forms.CharField(required=True, widget=forms.TextInput(attrs={'placeholder': ''}),error_messages={'required': 'Please enter your name'})
        self.fields['distance'] = forms.DecimalField(required=True, widget=forms.NumberInput(attrs={'placeholder': ''}))
        self.fields['remarks'] = forms.CharField(required=True, widget=forms.TextInput(attrs={'placeholder': ''}))
    
        # self.fields['plant_name'].widget.attrs.update({'placeholder': ''})
        # self.fields['distance'].widget.attrs.update({'placeholder': ''})
        # self.fields['remarks'].widget.attrs.update({'placeholder': ''})

        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})
            self.fields[field].label = ''

        self.fields['time_required'].widget = forms.HiddenInput()

    class Meta:
        model = Plant
        fields = ['plant_name', 'distance', 'time_required','remarks']
