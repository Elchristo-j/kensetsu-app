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
            'position', # ★ここに追加！
            'location', 
            'bio',          # description から変更
            'avatar',       # image から変更
            'id_card_image',
            # --- 追加項目 ---
            'experience_years',
            'qualifications',
            'skills',
            'invoice_num'
        ]
        
        # 入力欄のデザイン（Bootstrapのクラスを適用）
        widgets = {
            'company_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '会社名または個人名'}),
            'location': forms.Select(attrs={'class': 'form-select'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': '自己紹介、経歴、得意な作業などを記入してください'}),
            'avatar': forms.FileInput(attrs={'class': 'form-control'}),
            'id_card_image': forms.FileInput(attrs={'class': 'form-control'}),
            
            # 追加項目のデザイン
            'experience_years': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '例: 10'}),
            'qualifications': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '例: 第一種電気工事士, 高所作業車'}),
            'skills': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '例: 屋内配線, エアコン設置, 盤結線'}),
            'invoice_num': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Tから始まる13桁の番号'}),
        }
        
        # 画面に表示されるラベル名
        labels = {
            'company_name': '屋号・会社名',
            'location': '所在地（都道府県）',
            'bio': '自己紹介',
            'avatar': 'プロフィール画像',
            'id_card_image': '本人確認書類',
            'experience_years': '経験年数',
            'qualifications': '保有資格 (カンマ区切り)',
            'skills': '得意な工事・スキル (カンマ区切り)',
            'invoice_num': 'インボイス登録番号',
        }