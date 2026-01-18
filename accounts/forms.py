from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Profile, PREFECTURES

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, label="メールアドレス")
    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('email',)

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['company_name', 'location', 'description', 'image', 'id_card_image']
        widgets = {
            'company_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '株式会社〇〇 / 山田 太郎'}),
            'location': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': '経歴や保有資格を詳しく記入してください'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'id_card_image': forms.FileInput(attrs={'class': 'form-control'}),
        }