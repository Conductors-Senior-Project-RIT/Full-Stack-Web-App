import os
from threading import Thread
from brevo import Brevo, SendTransacEmailRequestSender, SendTransacEmailRequestToItem

class EmailService:
    """ 
    currently using brevo: https://developers.brevo.com/docs/api-clients/python 

    TODO: authenticate a domain to send email from and setup env vars then test to see if it works lol 
    """

    def __init__(self) -> None:
        self.client = Brevo(api_key=os.getenv("BREVO_API_KEY", "fallback-value")) # Override the default httpx client for proxies, custom transports, or mTLS:
        self.website_domain = os.getenv("WEBSITE_DOMAIN", "fallback-value")
        
        self.sent_from_email = os.getenv("BREVO_SENDER_EMAIL", "hello@brevo.com") # change this if email ever switches https://help.brevo.com/hc/en-us/articles/12163873383186-Authenticate-your-domain-with-Brevo-Brevo-code-DKIM-DMARC + https://help.brevo.com/hc/en-us/articles/208836149-Create-a-new-sender-From-name-and-From-email
        
        # You can only authenticate a domain that you or your business own and control. Domains from free email services, such as Gmail or Yahoo (e.g., @gmail.com or @yahoo.com), cannot be authenticated.
        
        #If you don’t have your own domain yet, you will need to purchase one. To learn more, check our dedicated article Why you need to replace your free email address with a professional one.

    # def _send_async(self, app, subject: str, email_body: str, send_to_name: str, send_to_email: str):
    #     """
    #     method to send emails "asyncronously" by starting new background thread so main thread doesn't wait for email to send

    #     NOTE: bandage solution
    #     """
    #     with app.app_context():
    #         self._send(subject, email_body, send_to_name, send_to_email) 

    def _send(self, subject: str, email_body: str, send_to_name: str, send_to_email: str):
        """
        NOTE: the SDK raises ApiError (or a typed subclass) for non-2xx HTTP responses
        
        Synchronous email send (default behavior, will block main thread unless background jobs are set up).
        """        
        self.client.transactional_emails.send_transac_email(
            subject=subject,
            html_content=email_body,
            sender=SendTransacEmailRequestSender(
                name="SWEN student from RIT",
                email=self.sent_from_email, # put brevo eamil here
            ),
            to=[
                SendTransacEmailRequestToItem(
                    email=send_to_email,
                    name=send_to_name,
                )
            ],
        )
        # print("Email sent. Message ID:", result.message_id)

    def send_email(self, subject: str, email_body: str, send_to_name: str, send_to_email: str, sync=False):
        """
        sync argument determines if email is sent async or not
        """
        if sync:
            self._send(subject, email_body, send_to_name, send_to_email)
        else:
            Thread(target=self._send, # boot up new thread to start in background so main thread in flask isnt blocked
                   args=(subject, email_body, send_to_name, send_to_email)).start() 

    """
    TODO: update email body with html content to be sent
    """
    def send_registered_email(self, send_to_email, send_to_name):
        "register() route if successful"

        subject = "Welcome to Follow That FRED!"
        email_body = f"<h1>Hello {send_to_name}, thanks for registering with us!<h1>"
        send_to_email = send_to_email
        send_to_name = send_to_name

        self.send_email(subject, email_body, send_to_name, send_to_email)

    def send_forgot_password_email(self,send_to_email, send_to_name, reset_token):
        """
        forgot_password() route
        """
        
        subject = "Password Reset Request"
        email_body = f"<h1>A password reset request was made from your account. If you wish to reset your password, please click the following link: {self.website_domain}/reset-password?token={reset_token} \n\nIf you did not request to reset your password, please disregard this email!<h1>"
        send_to_email = send_to_email
        send_to_name = send_to_name

        self.send_email(subject, email_body, send_to_name, send_to_email)

email_service = EmailService()