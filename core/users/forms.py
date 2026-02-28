from django.contrib.auth.password_validation import validate_password
from django import forms
from django.contrib.auth.models import User


ALLOWED_EMAIL_DOMAINS = ("@gmail.com", "@yahoo.com", "@ukr.net", "@mail.ru", "@yandex.ru", "@outlook.com", "@icloud.com")

class RegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'confirm_password']

    def clean_email(self):
        email = self.cleaned_data.get('email')

        if not email or not email.endswith(ALLOWED_EMAIL_DOMAINS):
            raise forms.ValidationError(', '.join(ALLOWED_EMAIL_DOMAINS))

        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Email is already in use")

        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password:
            if password != confirm_password:
                raise forms.ValidationError("Passwords dont match")

            validate_password(password)

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user


class LoginForm(forms.Form):
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        password = cleaned_data.get('password')

        if username and password:
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                raise forms.ValidationError("Invalid username or password")

            if not user.check_password(password):
                raise forms.ValidationError("Invalid username or password")

            self._user = user

        return cleaned_data

    def get_user(self):
        return self._user
