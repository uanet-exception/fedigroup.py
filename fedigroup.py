#!/usr/bin/env python3

import argparse
import configparser
import getpass
import html
import mastodon
import os
import re
import requests
import sys
import signal
import time


class FediGroupBot:
    def __init__(self, base_url, access_token, accept_dms,
                 accept_retoots, save_file):
        self.base_url = base_url
        self.accept_dms = accept_dms
        self.accept_retoots = accept_retoots
        self.save_file = save_file

        self.masto = mastodon.Mastodon(
            debug_requests=False,
            access_token=access_token,
            api_base_url=base_url)

        self.id = self.masto.account_verify_credentials().id
        self.username = self.masto.account_verify_credentials().username

        followers = self.masto.account_followers(self.id, limit=sys.maxsize)
        self.group_members = [member.acct for member in followers]

        following = self.masto.account_following(self.id, limit=sys.maxsize)
        self.group_admins = [member.acct for member in following]

    def run(self):
        last_seen_id = 0
        if os.path.exists(self.save_file):
            with open(self.save_file, 'r') as fd:
                try:
                    last_seen_id = int(fd.readline())
                except ValueError:
                    pass

        while True:
            for notification in sorted(self.masto.notifications(since_id=last_seen_id), key=lambda x: x.id):  # NOQA: E501
                if notification.id > last_seen_id:
                    last_seen_id = notification.id
                    self._do_action(notification)
                    with open(self.save_file, 'w') as fd:
                        fd.write(str(last_seen_id))

            time.sleep(2)

    def _do_action(self, notification):
        if notification.type != "mention":
            return

        if notification.status.in_reply_to_id is not None:
            return

        if self.accept_retoots and notification.status.visibility == "public" \
           and notification.status.account.acct in self.group_members:
            self.masto.status_reblog(notification.status.id)

        if self.accept_dms and notification.status.visibility == "direct" \
           and notification.status.account.acct in self.group_admins:
            new_status = re.sub("<br />", "\n", notification.status.content)
            new_status = re.sub("</p><p>", "\n\n", new_status)
            new_status = re.sub("<.*?>", "", new_status)

            if new_status.startswith("@" + self.username):
                new_status = re.sub("@" + self.username, "", new_status)
                new_status = html.unescape(new_status)

                media_ids = []
                for media in notification.status.media_attachments:
                    response = requests.get(media.url)
                    mime_type = response.headers['Content-Type']
                    media_data = response.content
                    media_ids.append(self.masto.media_post(
                        media_data, mime_type, description=media.description))

                self.masto.status_post(
                    new_status,
                    media_ids=media_ids,
                    sensitive=notification.status.sensitive,
                    visibility="public",
                    spoiler_text=notification.status.spoiler_text)


class MainApp:
    def __init__(self):
        self.default_config = os.path.join(
            os.path.abspath(
                os.path.join(__file__, os.pardir, 'fedigroups.ini')))
        parser = argparse.ArgumentParser(
            description='FediGroupBot Manager',
            usage=f'{__file__} <command> [<args>]\n\n'
                  'The most commonly used commands are:\n'
                  '   create     Create a new bot\n'
                  '   remove     Remove selected bot from config file\n'
                  '   list       List all bots from config file\n'
                  '   run        Run selected bot')
        parser.add_argument('command', help='Subcommand to run')

        args = parser.parse_args(sys.argv[1:2])
        if not hasattr(self, args.command):
            parser.print_help()
            print(f'{__file__}: error: Unrecognized command: {args.command}')
            exit(1)

        getattr(self, args.command)()

    def create(self):
        def yes_or_no(question):
            while 'the answer is invalid':
                reply = input(question + ' (Y/n): ').lower().strip()
                if reply[:1].lower() in ['y', '']:
                    return 'yes'
                if reply[:1].lower() == 'n':
                    return 'no'
        parser = argparse.ArgumentParser(
            description='Create a new bot',
            usage=f'{__file__} create <name> [<args>]')
        parser.add_argument('name')
        parser.add_argument(
            '-c', '--config', help='config file', required=False,
            type=str, metavar="fedigroups.ini",
            default=self.default_config)

        args = parser.parse_args(sys.argv[2:])

        if os.path.exists(args.config):
            config = configparser.ConfigParser()
            config.read(args.config)
            if config.has_section(args.name):
                parser.print_help()
                print(f'{__file__}: error: Configuration group for "{args.name}" is already exist')  # NOQA: E501
                exit(1)

        print(f'New configuration will be stored in "{args.config}" file')

        base_url = input('Enter the URL of the Mastodon instance: ')
        email = input('Username (e-Mail) to log into Mastodon Instance: ')
        password = getpass.getpass('Password: ')

        accept_dms = yes_or_no('Should we repost direct messages?')
        accept_retoots = yes_or_no('Should we retoot public mentions from group members?')  # NOQA: E501
        if accept_dms == accept_retoots == 'no':
            print("Oh, no! You can't disable both direct messages and public mentions!")  # NOQA: E501
            exit(1)

        save_file = os.path.abspath(os.path.join(
            args.config, os.pardir, f'{args.name}.save'))
        save_file_choice = input(f'Savepoint file (default: {save_file}): ')
        if save_file_choice.strip() and os.path.exists(os.path.dirname(save_file_choice.strip())):  # NOQA: E501
            print(f'Savepoint file changed to "{save_file_choice}"')
            save_file = save_file_choice

        client_id, client_secret = mastodon.Mastodon.create_app(
            'FediGroupBot',
            api_base_url=base_url
        )
        access_token = mastodon.Mastodon(
            client_id=client_id,
            client_secret=client_secret,
            api_base_url=base_url
        ).log_in(email, password)

        config = configparser.ConfigParser()
        config.read(args.config)
        config.add_section(args.name)
        config.set(args.name, 'base_url', base_url)
        config.set(args.name, 'access_token', access_token)
        config.set(args.name, 'accept_dms', accept_dms)
        config.set(args.name, 'accept_retoots', accept_retoots)
        config.set(args.name, 'save_file', save_file)
        with open(args.config, 'w') as fd:
            config.write(fd)

        print(f"Now you start your bot using command: {__file__} run {args.name}")  # NOQA: E501

    def remove(self):
        parser = argparse.ArgumentParser(
            description='Remove selected bot',
            usage=f'{__file__} remove <name> [<args>]')
        parser.add_argument('name')
        parser.add_argument(
            '-c', '--config', help='config file', required=False,
            type=str, metavar="fedigroups.ini",
            default=self.default_config)

        args = parser.parse_args(sys.argv[2:])
        config = configparser.ConfigParser()
        config.read(args.config)
        config.remove_section(args.name)
        with open(args.config, 'w') as fd:
            config.write(fd)

    def list(self):
        def extant_file(x):
                if not os.path.exists(x):
                    raise argparse.ArgumentTypeError(
                        f'File "{x}" does not exist')
                return x
        parser = argparse.ArgumentParser(
            description='List all bots',
            usage=f"{__file__} list [<args>]")
        parser.add_argument(
            '-c', '--config', help='config file', required=False,
            type=extant_file, metavar="fedigroups.ini",
            default=self.default_config)

        args = parser.parse_args(sys.argv[2:])
        config = configparser.ConfigParser()
        config.read(args.config)
        if len(config.sections()) == 0:
            print(f'No configurations were found')
            return
        for section in config.sections():
            print(f'{section} - ({config.get(section, "base_url")})')

    def run(self):
        def extant_file(x):
                if not os.path.exists(x):
                    raise argparse.ArgumentTypeError(
                        f'File "{x}" does not exist')
                return x
        parser = argparse.ArgumentParser(
            description='Run selected bot',
            usage=f"{__file__} run <name> [<args>]")
        parser.add_argument('name')
        parser.add_argument(
            '-c', '--config', help='config file', required=False,
            type=extant_file, metavar="fedigroups.ini",
            default=self.default_config)

        args = parser.parse_args(sys.argv[2:])
        print(f'Starting "{args.name}" bot...')

        config = configparser.ConfigParser()
        config.read(args.config)
        base_url = config.get(args.name, 'base_url')
        access_token = config.get(args.name, 'access_token')
        accept_dms = config.getboolean(args.name, 'accept_dms')
        accept_retoots = config.getboolean(args.name, 'accept_retoots')
        save_file = config.get(args.name, 'save_file')

        FediGroupBot(base_url, access_token, accept_dms,
                     accept_retoots, save_file).run()


if __name__ == '__main__':
    signal.signal(signal.SIGINT, lambda _, frame: exit(130))
    MainApp()
