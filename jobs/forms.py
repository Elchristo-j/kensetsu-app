from django import forms
from .models import Job, Message

class JobForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = ['title', 'description', 'price']
        labels = {
            'title': '仕事のタイトル',
            'description': '詳しい内容',
            'price': '報酬金額（円）',
        }
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '例：大阪市内でクロスの張り替え'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': '詳細な条件などを記入'}),
            'price': forms.NumberInput(attrs={'class': 'form-control'}),
        }

# ★追加：チャット用のフォーム
class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['content']
        labels = {'content': 'メッセージ'}
        widgets = {
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'ここにメッセージを入力...'}),
        }