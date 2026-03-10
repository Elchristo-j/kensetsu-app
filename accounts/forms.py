from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Profile

# ⛔️ ブラックリスト（捨てアドのドメイン）
DISPOSABLE_DOMAINS = [
    'yopmail.com', 'mailinator.com', '10minutemail.com',
    'guerrillamail.com', 'superrito.com', 'sharklasers.com',
    'tempmail.com', 'throwawaymail.com', 'acac.com',
]

class CustomUserCreationForm(UserCreationForm):
    """
    ユーザー登録用フォーム
    """
    email = forms.EmailField(required=True, label="メールアドレス")

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('email',)

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            try:
                domain = email.split('@')[1].lower().strip()
                if domain in DISPOSABLE_DOMAINS:
                    raise forms.ValidationError("申し訳ありませんが、使い捨てメールアドレスは使用できません。")
            except IndexError:
                raise forms.ValidationError("正しいメールアドレスを入力してください。")
        return email
    def clean_email(self):
        email = self.cleaned_data.get('email')
        
        # データベースに同じメールアドレスがすでに存在するかチェック
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("このメールアドレスはすでに登録されています。")
            
        return email

class ProfileForm(forms.ModelForm):
    """
    プロフィール編集用フォーム
    """
    class Meta:
        model = Profile
        fields = [
            'company_name', 
            'position',
            'age_group',
            'occupation_main',
            'occupation_sub',
            'location', 
            'bio',
            'avatar',
            'id_card_image',
            'experience_years',
            'qualifications',
            'skills',
            'invoice_num',
            # ▼ 連絡先情報
            'real_name',
            'phone_number',
            'line_id',
            'contact_email'  # ← これがリストに入っている必要があります！
        ]
        
        widgets = {
            'company_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '会社名または個人名'}),
            'position': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '役職・部署'}),
            'age_group': forms.Select(attrs={'class': 'form-select'}),
            'occupation_main': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '例: 電気工事'}),
            'occupation_sub': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '例: 空調設備, 消防設備'}),
            'location': forms.Select(attrs={'class': 'form-select'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'avatar': forms.FileInput(attrs={'class': 'form-control'}),
            'id_card_image': forms.FileInput(attrs={'class': 'form-control'}),
            'experience_years': forms.NumberInput(attrs={'class': 'form-control'}),
            'qualifications': forms.TextInput(attrs={'class': 'form-control'}),
            'skills': forms.TextInput(attrs={'class': 'form-control'}),
            'invoice_num': forms.TextInput(attrs={'class': 'form-control'}),
            # ▼ 連絡先情報
            'real_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '例: 山田 太郎（契約者のみ公開）'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '例: 090-0000-0000（契約者のみ公開）'}),
            'line_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'LINE ID（契約者のみ公開）'}),
            'contact_email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': '例: info@el-christo.jp（契約者のみ公開）'}),
        }

        labels = {
            'company_name': '会社名 / 屋号',
            'position': '役職',
            'age_group': '年代',
            'occupation_main': 'メイン職種',
            'occupation_sub': 'サブ職種',
            'location': '活動エリア',
            'bio': '自己紹介',
            'avatar': 'プロフィール画像',
            'id_card_image': '本人確認書類',
            'experience_years': '経験年数',
            'qualifications': '保有資格',
            'skills': 'スキル・得意分野',
            'invoice_num': 'インボイス登録番号',
            # ▼ 連絡先情報
            'real_name': '担当者名（本名）',
            'phone_number': '電話番号',
            'line_id': 'LINE ID',
            'contact_email': '連絡用メールアドレス',
        }