# Important

Currently, we're using a free plan from Brevo to send emails and their API [https://developers.brevo.com/docs/getting-started](https://developers.brevo.com/docs/getting-started). There's limits so how much emails can be sent from Brevo in their free plan and other limitations. One option to look into would be Firebase Cloud Messaging for their generous no cost usage limits. If you wish to continue using Brevo's free plan for now at least, email me at `tmg2102@rit.edu` or `cjt7922@rit.edu` for Brevo login information if you can't find it.

Two emails this app sends currently are: registration confirmation emails and password reset link emails. A single instance, [`email_service`][src.service.email_service], is created at import time and reused.

::: src.service.email_service