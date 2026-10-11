from unittest import mock

from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from django.core import mail
from django.test import Client, TestCase
from django.urls import reverse

from config.utils import is_blocked_email_domain


def _recaptcha_response(success=True):
    """urllib.request.urlopen の返り値（reCAPTCHA API のレスポンス）を模したモック"""
    response = mock.Mock()
    response.read.return_value = b'{"success": true}' if success else b'{"success": false}'
    return response


class SignupBotProtectionTests(TestCase):
    """signup のハニーポット／メールドメイン拒否のテスト。reCAPTCHA の外部通信はモックする。"""

    def setUp(self):
        self.url = reverse('signup')

    def _post_data(self, **overrides):
        data = {
            'username': 'testuser',
            'email': 'testuser@gmail.com',
            'password1': 'Kensetsu-Test-Pass-2026',
            'password2': 'Kensetsu-Test-Pass-2026',
            'g-recaptcha-response': 'dummy-token',
            'website': '',
        }
        data.update(overrides)
        return data

    def _messages(self, response):
        return [str(m) for m in get_messages(response.wsgi_request)]

    def _post_success_control(self):
        """対照群：正常に仮登録できたときのリダイレクト先とメッセージを取得する
        （セッションのメッセージが混ざらないよう、別クライアントで送信する）"""
        with mock.patch('urllib.request.urlopen', return_value=_recaptcha_response()):
            response = Client().post(self.url, self._post_data(
                username='controluser', email='controluser@gmail.com',
            ))
        return response['Location'], self._messages(response)

    # ケース1【対照・正常系】
    @mock.patch('urllib.request.urlopen')
    def test_valid_signup_creates_inactive_user(self, mock_urlopen):
        mock_urlopen.return_value = _recaptcha_response()

        response = self.client.post(self.url, self._post_data())

        mock_urlopen.assert_called_once()
        self.assertRedirects(response, reverse('login'), fetch_redirect_response=False)
        self.assertEqual(User.objects.count(), 1)
        user = User.objects.get(username='testuser')
        self.assertFalse(user.is_active)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(len(self._messages(response)), 1)
        self.assertIn('仮登録が完了しました', self._messages(response)[0])

    # ケース2【ハニーポット】
    @mock.patch('urllib.request.urlopen')
    def test_honeypot_discards_silently(self, mock_urlopen):
        response = self.client.post(self.url, self._post_data(website='http://spam.example'))

        mock_urlopen.assert_not_called()
        self.assertEqual(User.objects.count(), 0)
        self.assertEqual(len(mail.outbox), 0)

        location, messages = response['Location'], self._messages(response)
        control_location, control_messages = self._post_success_control()
        self.assertEqual(location, control_location)
        self.assertEqual(messages, control_messages)

    # ケース3【ドメイン拒否】
    @mock.patch('urllib.request.urlopen')
    def test_blocked_domain_discards_silently(self, mock_urlopen):
        with self.assertLogs('accounts.views', level='WARNING') as logs:
            response = self.client.post(self.url, self._post_data(email='testuser@gmx.us'))

        mock_urlopen.assert_not_called()
        self.assertEqual(User.objects.count(), 0)
        self.assertEqual(len(mail.outbox), 0)
        self.assertTrue(any('Signup blocked by email domain:' in line for line in logs.output))

        location, messages = response['Location'], self._messages(response)
        control_location, control_messages = self._post_success_control()
        self.assertEqual(location, control_location)
        self.assertEqual(messages, control_messages)


class BlockedEmailDomainTests(TestCase):
    """ケース4【誤爆防止】日本の主要プロバイダはブロック対象にならない"""

    def test_major_japanese_providers_are_not_blocked(self):
        domains = [
            'gmail.com', 'yahoo.co.jp', 'icloud.com', 'outlook.com', 'outlook.jp',
            'hotmail.com', 'hotmail.co.jp', 'live.jp', 'me.com',
            'docomo.ne.jp', 'ezweb.ne.jp', 'au.com', 'softbank.ne.jp', 'i.softbank.jp',
            'ymobile.ne.jp', 'ocn.ne.jp', 'nifty.com', 'biglobe.ne.jp', 'so-net.ne.jp',
        ]
        for domain in domains:
            with self.subTest(domain=domain):
                self.assertFalse(is_blocked_email_domain(f'user@{domain}'))

    def test_blocked_domains_are_detected(self):
        for email in ['user@gmx.us', 'user@GMX.US', 'user@mail.gmx.us', 'user@mailinator.com']:
            with self.subTest(email=email):
                self.assertTrue(is_blocked_email_domain(email))

    def test_invalid_input_is_not_blocked(self):
        for email in [None, '', 'no-at-mark', 'user@']:
            with self.subTest(email=email):
                self.assertFalse(is_blocked_email_domain(email))
