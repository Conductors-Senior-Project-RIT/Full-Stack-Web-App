# Deployment files

## ftf-backend.service
systemd unit that starts the uWSGI backend on boot.

Install (on the server):
    sudo cp deploy/ftf-backend.service /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable --now ftf-backend

Daily stuff:
    sudo systemctl restart ftf-backend    # after deploying changes
    journalctl -u ftf-backend -f          # logs

Assumes the repo lives at /deployment/Full-Stack-Web-App and uWSGI is at /usr/local/bin/uwsgi.