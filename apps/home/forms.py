from django import forms
from .models import users


class UserAddForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(UserAddForm, self).__init__(*args, **kwargs)
        self.fields['name'].widget.attrs.update({'placeholder': '⽒名'})
        self.fields['email'].widget.attrs.update({'placeholder': 'メール'})
        self.fields['affiliation'].widget.attrs.update({'placeholder': 'Affiliation'})
        self.fields['address'].widget.attrs.update({'placeholder': '住所'})
        self.fields['houseName'].widget.attrs.update({'placeholder': 'ハウス名'})
        self.fields['plantName'].widget.attrs.update({'placeholder': 'Plant Name'})
        CHOICES = [('option1', '権限を選択してください'), ('管理者', '管理者'), ('ユーザ', 'ユーザ')]
        self.fields['role'] = forms.ChoiceField(choices=CHOICES, initial='option1', widget=forms.Select(attrs={'class': 'form-control'}), label="")

        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})
            self.fields[field].label = ''

    class Meta:
        model = users
        fields = ('name', 'email', 'affiliation', 'address', 'houseName', 'plantName', 'role')
