# Important

Currently, we're using a free plan from Brevo to send emails and their SDK (https://developers.brevo.com/docs/getting-started). There's limits so how much emails can be sent from Brevo in their free plan and other limitations. One option to look into would be firebase cloud messaging for their generous no cost usage limits. If you wish to continue using Brevo's free plan for now at least, email me at tmg2102@rit.edu for Brevo login information if you can't find it.

Two emails this app sends currently are: registration confirmation emails and password reset link emails. A single instance, `email_service`, is created at import time and reused.

::: src.service.email_service