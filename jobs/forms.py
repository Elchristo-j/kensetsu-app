from django import forms
from .models import Job, Message
from accounts.models import Profile

class JobForm(forms.ModelForm):
    class Meta:
        model = Job
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
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'working_hours': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '例：8:00〜17:00'}),
            'break_time': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '例：合計120分'}),
            'qualifications': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'price': forms.NumberInput(attrs={'class': 'form-control'}),
            'unit': forms.Select(attrs={'class': 'form-select'}),
            'prefecture': forms.Select(attrs={'class': 'form-select'}), 
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'headcount': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'deadline': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        # --- id_card_image を追加しました ---
        fields = ['image', 'location', 'description', 'id_card_image']
        labels = {
            'image': 'プロフィール画像（顔写真など）',
            'location': '拠点',
            'description': '自己紹介・実績',
            'id_card_image': '本人確認書類（免許証など）',
        }
        widgets = {
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'id_card_image': forms.FileInput(attrs={'class': 'form-control'}),
        }
        # ----------------------------------

class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['content']
        widgets = {'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 3})}