from django import forms
from .models import Job, Message
# ここが重要です：Profileは accounts アプリから読み込みます
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
            'city': '市区町村（例：世田谷区、横浜市など）',
            'headcount': '募集人数',
            'deadline': '募集期限',
        }

        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '例：マンション塗装の手元作業'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': '作業内容や集合場所など、詳しく記入してください'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '半角数字で入力'}),
            'unit': forms.Select(attrs={'class': 'form-select'}),
            'prefecture': forms.Select(attrs={'class': 'form-select'}), 
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '例：徳島市'}),
            'headcount': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'deadline': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['content']
        labels = {'content': ''}
        widgets = {
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'メッセージを入力してください...'}),
        }

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['image', 'location', 'description']
        labels = {
            'image': 'アイコン画像',
            'location': '主な活動エリア（都道府県など）',
            'description': '自己紹介 / 経歴',
        }
        widgets = {
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '例：徳島県全域、鳴門市周辺'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': '持っている資格や得意な作業など'}),
        }