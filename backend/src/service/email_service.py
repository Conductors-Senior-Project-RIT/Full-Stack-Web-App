import os
from threading import Thread
from brevo import Brevo, SendTransacEmailRequestSender, SendTransacEmailRequestToItem
from brevo.core.api_error import ApiError

class EmailService:
    """ 
    currently using brevo: https://developers.brevo.com/docs/api-clients/python 

    TODO: Send emails from a custom domain then authenticate your domain with DKIM and DMARC
    """

    def __init__(self) -> None:
        self.client = Brevo(api_key=os.getenv("BREVO_API_KEY", "fallback-value")) # Override the default httpx client for proxies, custom transports, or mTLS:
        self.website_domain = os.getenv("WEBSITE_DOMAIN", "fallback-value")
        self.sent_from_name = os.getenv("BREVO_SENDER_NAME", "FollowThatFRED")
        self.sent_from_email = os.getenv("BREVO_SENDER_EMAIL", "hello@brevo.com") # change this if email ever switches https://help.brevo.com/hc/en-us/articles/12163873383186-Authenticate-your-domain-with-Brevo-Brevo-code-DKIM-DMARC + https://help.brevo.com/hc/en-us/articles/208836149-Create-a-new-sender-From-name-and-From-email
        

    def _send(self, subject: str, email_body: str, send_to_email: str, send_to_name: str | None):
        """
        NOTE: the SDK raises ApiError (or a typed subclass) for non-2xx HTTP responses
        
        Synchronous email send (default behavior will block main thread -> background jobs (flask docs) can handle cleanly.
        """        
        try: # at the moment: email errors are caught silently and not bubbled
            self.client.transactional_emails.send_transac_email(
                subject=subject,
                html_content=email_body,
                sender=SendTransacEmailRequestSender(
                    name=self.sent_from_name,
                    email=self.sent_from_email, 
                ),
                to=[
                    SendTransacEmailRequestToItem(
                        email=send_to_email,
                        name=send_to_name,
                    )
                ],
            )
        except ApiError as e:
            print(f"Email failed to send: {e.status_code} {e.body}")
        except Exception as e:
            print(f"Unepected error sending email: {e}")

    def send_email(self, subject: str, email_body: str, send_to_email: str, send_to_name: str | None=None, sync=False):
        """
        sync argument determines if email is sent asynchronously 

        send_to_name argument has placeholder value atm as users don't have usernames (no biggie)
        """
        if sync:
            self._send(subject, email_body, send_to_email, send_to_name)
        else:
            Thread(target=self._send, # boot up new thread to start in background so main thread in flask isnt blocked
                   args=(subject, email_body, send_to_email, send_to_name)).start() 

    """
    TODO: update email body with html content to be sent
    """
    def send_registered_email(self, send_to_email: str, send_to_name: str | None=None):
        "register() route"
        if send_to_name is None:
            send_to_name = send_to_email.split("@")[0] # for now use first part of email

        subject = "Welcome to Follow That FRED!"
        email_body = f"<h1>Hello {send_to_name}, thanks for registering with us!<h1>"
        send_to_email = send_to_email

        self.send_email(subject, email_body, send_to_email, send_to_name)

    def send_forgot_password_email(self, send_to_email, reset_token, send_to_name: str | None=None):
        """
        forgot_password() route
        """
        if send_to_name is None:
            send_to_name = send_to_email.split("@")[0] # for now use first part of email

        subject = "Password Reset Request"
        email_body = f"<h1>A password reset request was made from your account. If you wish to reset your password, please click the following link: {self.website_domain}/reset-password?token={reset_token} \n\nIf you did not request to reset your password, please disregard this email!</h1>"

        self.send_email(subject, email_body, send_to_email, send_to_name)

email_service = EmailService()