from django import forms
from .models import Job, Message
from .models import Contact
# ▼ jobs/forms.py の一番上あたり
from .models import Job, Application, News, UraProfile  # ← UraProfile を追加

class JobForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = [
            'category', # ★ここに追加しました
            'title', 'work_date', 'description', 'working_hours', 'break_time', 
            'qualifications', 'price', 'unit', 'prefecture', 'city', 
            'headcount', 'deadline', 'notes'
        ]
        labels = {
            'category': '業種・職種', # ★ラベル
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
            'category': forms.Select(attrs={'class': 'form-select'}), # ★ドロップダウンのデザイン
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

class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['content']
        widgets = {'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 3})}

class ContactForm(forms.ModelForm):
    class Meta:
        model = Contact
        fields = ['name', 'email', 'subject', 'message']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'お名前'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'example@email.com'}),
            'subject': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '件名'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'お問い合わせ内容を入力してください'}),
        }

# ▼▼ jobs/forms.py の一番下に追記 ▼▼

class UraProfileForm(forms.ModelForm):
    class Meta:
        model = UraProfile
        fields = [
            'is_published', 'main_occupation', 'sub_occupations', 
            'base_location', 'experience_years', 'good_at', 'bad_at', 
            'desired_daily_wage', 'self_introduction'
        ]
        labels = {
            'is_published': 'この裏プロフィールを公開してスカウトを受け付ける',
        }
        widgets = {
            'is_published': forms.CheckboxInput(attrs={'class': 'form-check-input', 'style': 'transform: scale(1.5); margin-right: 10px;'}),
            'main_occupation': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '例: 電気工'}),
            'sub_occupations': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '例: 空調・手元'}),
            'base_location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '例: 徳島県徳島市'}),
            'experience_years': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '例: 25年'}),
            'good_at': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': '例: 木造建築物の配線、ボード開口など'}),
            'bad_at': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': '例: 汚水、浄化槽、高所作業など'}),
            'desired_daily_wage': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '例: 20,000円+交通費'}),
            'self_introduction': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': '自由に自己アピールを書いてください！'}),
        }        