import json
import readline
import subprocess
import sys
from distutils.version import LooseVersion
from urllib import request

from Jovian import __version__

from .functions import color, tabCompleter


def AskPrompts(intro, prompt, options, fixedchoices=False):
    if fixedchoices is True:
        completer = tabCompleter()
        completer.createListCompleter(options)

        readline.set_completer_delims("\t")
        readline.parse_and_bind("tab: complete")
        readline.set_completer(completer.listCompleter)

    subprocess.call("/bin/clear", shell=False)
    print(intro)
    while "the answer is invalid":
        if fixedchoices is True:
            reply = input(prompt).lower().strip()
            if reply in options:
                return reply
            if reply == "quit":
                print("Quitting...")
                sys.exit(-1)
            else:
                print("The given answer was invalid. Please choose one of the available options\n")
        if fixedchoices is False:
            reply = input(prompt).strip()
            if reply == "quit":
                sys.exit(-1)
            else:
                return reply


def update(sysargs):

    try:
        latest_release = request.urlopen("https://api.github.com/repos/DennisSchmitz/jovian/releases/latest")
    except Exception as e:
        sys.stderr.write("Unable to connect to GitHub API\n" f"{e}")
        return

    latest_release = json.loads(latest_release.read().decode("utf-8"))

    latest_release_tag = latest_release["tag_name"]
    latest_release_tag_tidied = LooseVersion(latest_release["tag_name"].lstrip("v").strip())

    localversion = LooseVersion(__version__)

    if localversion < latest_release_tag_tidied:
        if (
            AskPrompts(
                f"""
There's a new version of Jovian available.
Current version: {color.RED + color.BOLD}{'v' + __version__}{color.END}
Latest version: {color.GREEN + color.BOLD}{latest_release_tag}{color.END}\n""",
                f"""Do you want to update? [yes/no] """,
                ["yes", "no"],
                fixedchoices=True,
            )
            == "yes"
        ):
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pip",
                    "install",
                    "--upgrade",
                    f"git+https://github.com/DennisSchmitz/jovian@{latest_release_tag}",
                ],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

            print(f"Jovian updated to {color.YELLOW + color.BOLD}{latest_release_tag}{color.END}")

            subprocess.run(sysargs)
            sys.exit(0)
        print(f"Skipping update to version {latest_release_tag}")
        print(f"Continuing...")
        return
    return
