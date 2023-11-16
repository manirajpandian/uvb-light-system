from django import forms
from .models import User


class UserAddForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(UserAddForm, self).__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'placeholder': ''})
        self.fields['email'].widget.attrs.update({'placeholder': ''})
        CHOICES = [(0, '権限を選択してください'), (1, '管理者'), (2, 'ユーザ')]
        self.fields['role_id'] = forms.ChoiceField(choices=CHOICES, initial='option1', widget=forms.Select(attrs={'class': 'form-control'}), label="")

        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})
            self.fields[field].label = ''

    class Meta:
        model = User
        fields = ('username', 'email', 'role_id')
