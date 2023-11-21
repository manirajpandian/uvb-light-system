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
    class Meta:
        model = Plant
        fields = ['plant_name', 'distance', 'time_required','remarks']
