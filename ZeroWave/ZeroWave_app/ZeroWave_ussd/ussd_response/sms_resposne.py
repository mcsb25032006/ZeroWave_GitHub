

import africastalking
import os
from dotenv import load_dotenv

load_dotenv()

africastalking.initialize(
    username="EMID",
    api_key=os.getenv("AT_API_KEY")
)

sms = africastalking.SMS


def send_message(phone_number, message_context):

    recipients = [f"{str(phone_number)}"]

    print(recipients)
    print(phone_number)

    # Set your message
    message = f"{message_context}"

    # Set your shortCode or senderId
    sender = 20880

    try:
        response = sms.send(message, recipients, sender)

        print(response)

    except Exception as e:
        print(f'Houston, we have a problem: {e}')
