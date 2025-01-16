import requests

# Setup thông báo về Telegram
bot_token = '5830945089:AAE9iWQ13YAGGAGA_TWoqakg6IWodDrv2wY'
chat_id = '-1001913742038' # ID nhóm không thay đổi

# Cách lấy chat id bằng cách nhập url sau: https://api.telegram.org/bot<botToken>/getUpdates
def functionSendMessageToTelegram(messageWantSend):

    try:        
        send_message_url = f'https://api.telegram.org/bot{bot_token}/sendMessage?chat_id={chat_id}&text={messageWantSend}'
        response = requests.get(send_message_url)
        if response.status_code == 200: print('Message sent successfully!')
        else: print('Failed to send message.')
        
    except: print("Loi~ telegram")