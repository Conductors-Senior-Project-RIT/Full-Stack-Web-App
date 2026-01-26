import os
from dotenv import load_dotenv
import requests

load_dotenv()
MAILGUN_API_KEY = os.getenv("MAILGUN_API_KEY")
MAILGUN_DOMAIN = os.getenv("MAILGUN_DOMAIN")
WEBSITE_DOMAIN = os.getenv("WEBSITE_DOMAIN")

def send_welcome_email(email) -> bool:
    """
    Email sent after successful registration
    """
    response = requests.post(
        f"https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/messages",
        auth=("api", MAILGUN_API_KEY),
        data={
            "from": f"Follow That FRED! <no-reply@{MAILGUN_DOMAIN}>",
            "to": email,
            "subject": "Welcome to Our App!",
            "text": f"Hi {email},\n\nThank you for registering with our app! We're excited to have you on board.\n\nBest regards,\nThe Team",
        },
    )

    return response.status_code == 200


