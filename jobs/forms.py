from django import forms
from .models import Job, Message
from accounts.models import Profile

class JobForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = ['title', 'description', 'price', 'unit', 'prefecture', 'city', 'headcount', 'deadline']
        labels = {
            'title': '仕事のタイトル',
            'description': '仕事内容の詳細',
            'price': '金額',
            'unit': '単位',
            'prefecture': '都道府県',
            'city': '市区町村（例：世田谷区など）',
            'headcount': '募集人数',
            'deadline': '募集期限',
        }
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'price': forms.NumberInput(attrs={'class': 'form-control'}),
            'unit': forms.Select(attrs={'class': 'form-select'}),
            # ここがプルダウンの設定です
            'prefecture': forms.Select(attrs={'class': 'form-select'}), 
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'headcount': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'deadline': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['image', 'location', 'description']
        labels = {
            'image': 'プロフィール画像',
            'location': '拠点（主な活動エリア）', # 「拠点」に修正
            'description': '自己紹介・実績',
        }
        widgets = {
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '例：徳島県全域'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }

class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['content']
        widgets = {'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 3})}