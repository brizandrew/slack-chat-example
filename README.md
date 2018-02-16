# Slack Chat

A Django app to create a public API for a private Slack channel's messages.

## Slack Buttons Tutorial
Check out our [Source article]() explaining how the LA Times uses Slack to create published live chats and how you can make your own.

## Getting Started

Create a virtualenv to store the codebase.
```bash
$ virtualenv slack_chat
```

Activate the virtualenv.
```bash
$ cd slack_chat
$ . bin/activate
```

Clone the git repository from GitHub.
```bash
$ git clone https://github.com/brizandrew/slack-chat-example.git repo
```

Enter the repo and install its dependencies.
```bash
$ cd repo
$ pip install -r requirements.txt
```

Make a copy of the .env file to add your own credentials
```bash
$ cp .env.template .env
```

Fill in your Slack app's credentials in the copied [env](.env.template#L8-L10) file. You also need a random string for the `secret_key`, and once you have a URL for your app fill that out in `site_url`.

Make the SQLite file
```bash
$ python manage.py migrate
```

Make a superuser
```bash
$ python manage.py createsuperuser
```

Now run the test server and check out the results on [localhost:8000/admin](localhost:8000/admin).
```bash
$ python manage.py runserver
```
