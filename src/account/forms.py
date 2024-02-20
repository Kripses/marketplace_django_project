import re

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from account.models import Profile


class UserRegistrationForm(UserCreationForm):
    full_name = forms.CharField(max_length=200)
    password1 = forms.CharField(
        label="Пароль",
        widget=forms.PasswordInput(),
        validators=[validate_password],
        required=False,
    )
    password2 = forms.CharField(
        label="Подтверждение пароля",
        widget=forms.PasswordInput(), required=False)

    class Meta:
        model = Profile
        fields = ['full_name', 'email', 'password1', 'password2']

    def clean_full_name(self):
        full_name = self.cleaned_data.get('full_name')
        if Profile.objects.filter(username=full_name.split()[0]).exists():
            raise ValidationError(f"User with username {full_name[0]} already exists.")
        return full_name


class ProfileForm(forms.ModelForm):
    full_name = forms.CharField(max_length=200)
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
        fields = ['phone', 'avatar', 'full_name', 'new_password1', 'new_password2']
