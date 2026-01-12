from django import forms
from .models import Profile
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

class CustomUserCreationForm(UserCreationForm):
    # メールアドレスを必須項目として定義
    email = forms.EmailField(
        required=True, 
        label="メールアドレス", 
        help_text="Stripe決済の通知などに使用するため、必ず入力してください。"
    )
    class Meta(UserCreationForm.Meta):
        model = User
        # ユーザー名、メールアドレス、パスワードの順で表示されます
        fields = UserCreationForm.Meta.fields + ('email',)

    def clean_email(self):
        """メールアドレスの重複チェック"""
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("このメールアドレスは既に登録されています。")
        return email
        
class ProfileForm(forms.ModelForm):
    """
    ユーザープロフィール編集用フォーム。
    画像の取り扱いと、視認性の高いUIコンポーネントを統合しています。
    """
    class Meta:
        model = Profile
        fields = ['image', 'location', 'description', 'id_card_image']
        
        labels = {
            'image': 'プロフィール画像（顔写真や屋号ロゴ）',
            'location': '拠点（主な活動エリア）',
            'description': '自己紹介・経歴・保有資格',
        }

        widgets = {
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',  # ブラウザ側で画像ファイルのみに制限し、誤操作を防止
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': '例：徳島県全域、鳴門市周辺（複数入力可）'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 5, 
                'placeholder': '得意な施工内容や、保有資格（例：一級建築士、塗装技能士）を詳細に記載すると信頼性が高まります'
            }),
        }

    def clean_image(self):
        """
        画像アップロードにおける副作用とリスクを防止するバリデーション。
        """
        image = self.cleaned_data.get('image')
        if image:
            # 5MBを超えるファイルはサーバー負荷と表示速度低下を招くため制限（一例）
            if image.size > 5 * 1024 * 1024:
                raise forms.ValidationError("画像サイズは5MB以下にしてください。")
        return image