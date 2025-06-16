from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import Project
from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm


class RegisterForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label="Password"
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label="Confirm Password"
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'type': 'email',
                'required': 'required',
                'pattern': r'[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$',
                'placeholder': 'you@example.com'
            }),
        }
        labels = {
            'email': 'Email Address',
            'username': 'Username',
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Passwords do not match.")


'''
def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # Log in the user immediately after registration (optional)
            return redirect('login')  # Adjust to your login page name
    else:
        form = CustomUserCreationForm()
    return render(request, 'register.html', {'form': form})
'''


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['project_name']


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'placeholder': 'Enter your email'}))

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
