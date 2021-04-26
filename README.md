`fedigroup.py` - emulate group accounts on Mastodon
=================================================

What is this?
-------------

Some social media platforms allow groups of users to post into a unified "group"
timeline/instance/whatever you want to call it. This is currently not possible
on Mastodon without giving all members full login credentials to a group.
`fedigroup.py` is an attempt to solve this specific use case.

How does it work?
-----------------

`fedigroup.py` has to be set up on a computer and run as a service. It reads the
notifications from the Mastodon account it is connected to and filters them for
messages to repost. There are two methods of creating a group post. One or both
of them can be enabled during the setup procedure.

1. Public mentions of group members are boosted if they mention the group's
   name in the first post.

2. `fedigroup.py` can also look for direct messages from following members. If the
   group is @mentioned at the very beginning, The message will be reposted as
   a new public toot originating directly from the group account. The status
   text as well as media files are included. The originating user will not be
   shown publicly. (It can still be seen by all group and instance
   administrators tough!)

But how to simply use it?
-------------------------

1. Subscribe to group account and write a message that should be boosted by the group:
   EXAMPLE: "OHAI! just found that @mastodon thingie!"

2. Make sure if group account is following you and write a message that should appear as a new post from the group:
   Put "@group_name" at the very beginning of a direct/private message.
   EXAMPLE: "@mastodon HERE BE THE MESSAGE TEXT"

How to set up?
--------------

The easiest way to install `fedigroup.py` is via PyPI, the Python Package Index.
Use `pip3 install fedigroup.py` to install it as well as all its dependencies.

It is also possible to download the script manually from the GitHub repository at
<https://github.com/uanet-exception/fedigroup.py"> In that case the necessary dependencies
have to be provided too:

`fedigroup.py` requires <https://github.com/halcy/Mastodon.py> to run. Install it via your
operating system's package manager, pip or even manually.

`fedigroup.py` will guide you through setup by asking all information it needs
when you run it from the commandline for the first time. Being somewhat
comfortable with Python scripting and the commandline in general might help
if difficulties should appear.

1. You need an account on any Mastodon instance/server that will act as your
   group account. Think about if you should mark it as a "Bot".

2. Run `fedigroup.py create <your-bots-name-here>` from the command line.

3. `fedigroup.py` will ask you for all needed setup data and try to get them
   right by connecting to the Mastodon server. If it cannot do so, it will
   tell you and you can retry. When successful, `fedigroup.py` will write the
   configuration to its fedigroups.ini file and read it from there next time
   you run the script.

   The place for storing configuration by default is next to `fedigroup.py` and
   will be shown during the first-run/setup phase.  You can specify your own path
   to config file using argument -c/--config.

4. If you want to set up `fedigroup.py` for more than one group, you can run it
   again while specifying the group bot name.

5. Test the funcionality by sending direct messages and "@mentions" to your
   group while running `fedigroup.py run <your-bots-name-here>` manually.
   See if things work as expected.
   If everything works, run the script via supervisor or systemd unit.

6. Use "-h" or "--help" for more information about all available options
