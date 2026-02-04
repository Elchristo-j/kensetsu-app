from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Profile

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, label="メールアドレス")
    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('email',)

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = [
            'company_name', 
            'position',    # 役職
            'age_group',   # 年代
            'occupation',  # 職種
            'location', 
            'bio',
            'avatar',
            'id_card_image',
            'experience_years',
            'qualifications',
            'skills',
            'invoice_num'
        ]
        
        widgets = {
            'company_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '会社名または個人名'}),
            'position': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '役職・部署'}),
            'age_group': forms.Select(attrs={'class': 'form-select'}),
            'occupation': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '職種 (例: 電気工事士)'}),
            'location': forms.Select(attrs={'class': 'form-select'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'avatar': forms.FileInput(attrs={'class': 'form-control'}),
            'id_card_image': forms.FileInput(attrs={'class': 'form-control'}),
            'experience_years': forms.NumberInput(attrs={'class': 'form-control'}),
            'qualifications': forms.TextInput(attrs={'class': 'form-control'}),
            'skills': forms.TextInput(attrs={'class': 'form-control'}),
            'invoice_num': forms.TextInput(attrs={'class': 'form-control'}),
        }