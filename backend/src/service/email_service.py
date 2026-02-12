import os
from dotenv import load_dotenv
import requests

from service_core import BaseService

load_dotenv()
MAILGUN_API_KEY = os.getenv("MAILGUN_API_KEY")
MAILGUN_DOMAIN = os.getenv("MAILGUN_DOMAIN")
WEBSITE_DOMAIN = os.getenv("WEBSITE_DOMAIN")


# class EmailService(BaseService):
#     def __init__(self, session):
#         super().__init__("Email")


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

def send_forgot_password_email(email: str, reset_token) -> bool:
    """
    Email sent to user who wants to reset their password
    """
    response = requests.post(
        f"https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/messages",
        auth=("api", MAILGUN_API_KEY),
        data={
            "from": f"Follow That FRED! <no-reply@{MAILGUN_DOMAIN}>",
            "to": email,
            "subject": "Password Reset Request",
            "text": f"""Hi {email},\n\nA password reset request was made from your account. If you wish to reset your password, please click the following link: {WEBSITE_DOMAIN}/reset-password?token={reset_token} \n\nIf you did not request to reset your password, please disregard this email.""",
            "html": f"<html><body><h3>Hi {email},</h3>\n\n<p>A password reset request was made from your account. If you wish to reset your password, please click the following link: {WEBSITE_DOMAIN}/reset-password?token={reset_token} \n\nIf you did not request to reset your password, please disregard this email.</p></body></html>",
        },
    )

    return response.status_code == 200


