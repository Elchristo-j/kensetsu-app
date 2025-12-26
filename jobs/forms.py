from django import forms
from .models import Job, Message
# ★ここ重要：Profileは accounts.models から読み込むように変更
from accounts.models import Profile

class JobForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = ['title', 'description', 'price', 'unit', 'prefecture', 'city', 'deadline', 'headcount']
        widgets = {
            'deadline': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 5}),
        }
        labels = {
            'title': '仕事のタイトル',
            'description': '仕事内容の詳細',
            'price': '金額',
            'unit': '単位',
            'prefecture': '都道府県',
            'city': '市区町村（例：世田谷区、横浜市など）',
            'deadline': '募集期限（任意）',
            'headcount': '募集人数',
        }

class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 2, 'placeholder': 'メッセージを入力...'}),
        }

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['image', 'location', 'description']
        labels = {
            'image': 'アイコン画像',
            'location': '主な活動エリア',
            'description': '自己紹介',
        }
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }