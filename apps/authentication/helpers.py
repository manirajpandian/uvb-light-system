from django.core.mail import send_mail
from django.conf import settings

def send_forgot_password_mail(email, token, farm_id):
    base_url = settings.BASE_URL
    link = f'{base_url}change_password/{token}'
    subject = 'パスワードの再設定'
    message = f'''
        パスワードリセットの申請を受け付けました。
        パスワードの再設定をご希望の場合は、以下URLをクリックし
        新しいパスワードをご登録ください。

        ※パスワードリセットの申請に心当たりがない場合は、
        以降の対応は不要となります。

        ▼パスワードの再設定URL
        {link}

        ※パスワード変更時は秘密の質問に回答いただきます。
        回答が不明な場合はアカウントの再作成が必要になります。
        ※URLの期限は24時間です。

        パスワードの設定：{link}

        ★！現段階ではまた登録は完了しておりません！★
        ※ご本人様確認のため、上記URLへ「24時間以内」にアクセスしアカウントの本登録を完了いただけますようお願いいたします。
            
        農家ID：{farm_id}
        ID：{email}

        ご不明な点がございましたら、このメールへご返信いただくか、
        info@beam~ までご連絡ください。'''
    
    email_from = settings.EMAIL_HOST_USER
    recipient_list = [email]

    send_mail(subject, message, email_from, recipient_list)
    return True