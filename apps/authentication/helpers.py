from django.core.mail import send_mail
from django.conf import settings

def send_forgot_password_mail(email, token):
    base_url = settings.BASE_URL
    link = f'{base_url}change_password/{token}'
    subject = 'パスワードの設定'
    message = f'''
            光防除システム管理サイトログイン

            光防除システム管理サイトへようこそ！
            下記の「パスワードの設定」をクリックして進んでください。

            パスワードの設定：{link}

            ★！現段階ではまた登録は完了しておりません！★
            ※ご本人様確認のため、上記URLへ「24時間以内」にアクセスしアカウントの本登録を完了いただけますようお願いいたします。

            ID：{email}

            ご不明な点がございましたら、このメールへご返信いただくか、
            info@beam~ までご連絡ください。'''
    
    email_from = settings.EMAIL_HOST_USER
    recipient_list = [email]

    send_mail(subject, message, email_from, recipient_list)
    return True