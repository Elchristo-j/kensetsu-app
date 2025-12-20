from django import forms
from .models import Profile

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['image', 'location', 'description']
        labels = {
            'image': 'プロフィール画像（顔写真やロゴ）',
            'location': '活動エリア',
            'description': '自己紹介・実績など',
        }
        widgets = {
             # 見た目を整えるための設定
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '例：大阪府全域、東京都23区内'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': '得意な施工内容や、保有資格などを書きましょう'}),
        }