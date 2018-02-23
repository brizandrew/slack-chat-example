#!/usr/bin/env python
import os
import sys
import configparser

if __name__ == "__main__":
    # Allow invoking manage.py from any directory
    repo_dir = os.path.dirname(os.path.realpath(__file__))

    # Load env variables from .env config file
    cp = configparser.SafeConfigParser()
    cp.read(os.path.join(repo_dir, ".env"))

    # Load the files variables into the environment
    for i in cp.items('django'):
        os.environ[i[0]] = i[1]

    # Load the settings
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "chat.settings")

    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)
