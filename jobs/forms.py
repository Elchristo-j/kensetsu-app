from django import forms
from .models import Job, Message
from accounts.models import Profile

class JobForm(forms.ModelForm):
    class Meta:
        model = Job
        # work_date を追加しました
        fields = [
            'title', 'work_date', 'description', 'working_hours', 'break_time', 
            'qualifications', 'price', 'unit', 'prefecture', 'city', 
            'headcount', 'deadline', 'notes'
        ]
        labels = {
            'title': '仕事のタイトル',
            'work_date': '勤務日・期間',
            'description': '作業内容の詳細',
            'working_hours': '勤務時間帯',
            'break_time': '休憩時間',
            'qualifications': '応募資格・必要な道具',
            'price': '金額',
            'unit': '単位',
            'prefecture': '都道府県',
            'city': '市区町村',
            'headcount': '募集人数',
            'deadline': '募集期限',
            'notes': '備考・特記事項',
        }
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '例：木造住宅の荷揚げ作業'}),
            'work_date': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '例：1月15日(水)〜17日(金)の3日間'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': '具体的な作業手順を記入してください'}),
            'working_hours': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '例：8:00〜17:00'}),
            'break_time': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '例：合計120分'}),
            'qualifications': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': '例：要普通免許、腰道具持参'}),
            'price': forms.NumberInput(attrs={'class': 'form-control'}),
            'unit': forms.Select(attrs={'class': 'form-select'}),
            'prefecture': forms.Select(attrs={'class': 'form-select'}), 
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '例：徳島市'}),
            'headcount': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'deadline': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'その他、伝えたいことがあれば記入してください'}),
        }

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['image', 'location', 'description']
        labels = {'image': 'プロフィール画像', 'location': '拠点', 'description': '自己紹介・実績'}
        widgets = {
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }

class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['content']
        widgets = {'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 3})}