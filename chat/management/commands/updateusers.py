from django.conf import settings
from django.core.management.base import BaseCommand
from chat.models import ChatUser
from slackclient import SlackClient


class Command(BaseCommand):
    help = "Updates the list of slack users in the database"

    # list of fields to check for updates
    UPDATE_FIELDS = [
        'name',
        'real_name',
        'image_24',
        'image_32',
        'image_48',
        'image_72',
        'image_192'
    ]

    def add_arguments(self, parser):
        """
        Adds custom arguments specific to this command.
        """
        parser.add_argument(
            '--verbose',
            action="store_true",
            help="Don't print out a progress log."
        )

    def log_progress(self, msg):
        if self.verbose:
            print msg

    def handle(self, *args, **kwds):
        sc = SlackClient(settings.SLACK_BOT_TOKEN)
        self.verbose = kwds['verbose']

        users = sc.api_call('users.list')['members']

        for slack_user in users:
            slack_id = slack_user['id']
            self.log_progress('Checking "%s"...' % slack_user['name'])
            change_found = False

            # If it exists update it
            if ChatUser.objects.filter(user_id=slack_id).exists():
                self.log_progress('"%s" exists, checking fields...' % slack_user['name'])
                db_user = ChatUser.objects.get(user_id=slack_id)

                for field in self.UPDATE_FIELDS:
                    # Get the db value for the field
                    db_field = getattr(db_user, field)

                    # Get the slack API call value for the field
                    if field[:6] == 'image_':
                        user_field = slack_user['profile'][field]
                    else:
                        user_field = slack_user.get(field, None)

                    # Compare the fields and update if different
                    if user_field and db_field != user_field:
                        self.log_progress('Change Found: Updating "%s" from "%s" to "%s" for user "%s"' % (
                            field,
                            db_field,
                            user_field,
                            slack_user['name']
                        ))
                        change_found = True
                        setattr(db_user, field, user_field)

                if change_found:
                    db_user.save()
                    change_found = False

            # If not, add it
            else:
                self.log_progress('No user found. Adding "%s".' % slack_user['name'])
                user_data = {
                    'user_id': slack_id,
                    'name': slack_user.get('name', ''),
                    'real_name': slack_user.get('real_name', ''),
                    'image_24': slack_user['profile'].get('image_24', ''),
                    'image_32': slack_user['profile'].get('image_32', ''),
                    'image_48': slack_user['profile'].get('image_48', ''),
                    'image_72': slack_user['profile'].get('image_72', ''),
                    'image_192': slack_user['profile'].get('image_192', ''),
                }
                u = ChatUser(**user_data)
                u.save()
