import re

from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, SetPasswordForm
from django.contrib.auth.password_validation import validate_password

from .models import Profile


class UserRegistrationForm(UserCreationForm):
    full_name = forms.CharField(max_length=200)

    class Meta:
        model = Profile
        fields = ['full_name', 'email', 'password1', 'password2']


class ProfileForm(forms.ModelForm):
    phone = forms.CharField(max_length=17, required=False)
    new_password1 = forms.CharField(
        label="Пароль",
        widget=forms.PasswordInput(),
        validators=[validate_password],
        required=False,
    )
    new_password2 = forms.CharField(
        label="ПоПароль",
        widget=forms.PasswordInput(), required=False)

    def clean_phone(self):
        phone = self.cleaned_data['phone']
        cleaned_phone = re.sub(r'\D', '', phone[2:])
        if 0 != len(cleaned_phone) < 10:
            raise forms.ValidationError(f'Телефон должен содержать 10 символов, у вас - {len(cleaned_phone)}')
        return cleaned_phone

    class Meta:
        model = Profile
        fields = ['phone', 'avatar', 'username', 'new_password1', 'new_password2']

