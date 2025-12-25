from django import forms
from .models import Job, Message

class JobForm(forms.ModelForm):
    class Meta:
        model = Job
        # 新しい項目（unit, headcount, deadline）を追加しました
        fields = ['title', 'description', 'price', 'unit', 'headcount', 'deadline']
        
        labels = {
            'title': '仕事のタイトル',
            'description': '詳しい内容',
            'price': '報酬金額', # 円は単位で選ぶので削除
            'unit': '単位',
            'headcount': '募集人数',
            'deadline': '募集期限',
        }
        
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '例：大阪市内でクロスの張り替え'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': '詳細な条件、現場の雰囲気などを記入'}),
            'price': forms.NumberInput(attrs={'class': 'form-control'}),
            
            # ★新機能用のデザイン設定
            'unit': forms.Select(attrs={'class': 'form-select'}), # プルダウン
            'headcount': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'deadline': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}), # カレンダー
        }

# チャット用フォーム（そのまま維持）
class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['content']
        labels = {'content': 'メッセージ'}
        widgets = {
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'ここにメッセージを入力...'}),
        }