import os

import click

from nostr._version import __version__

plugin_folder = os.path.join(os.path.dirname(__file__), "commands")


class CLI(click.MultiCommand):
    def list_commands(self, ctx):
        rv = []
        for filename in os.listdir(plugin_folder):
            if filename.endswith(".py") and filename != "__init__.py":
                rv.append(filename[:-3])
        rv.sort()
        return rv

    def get_command(self, ctx, name):
        ns = {}
        fn = os.path.join(plugin_folder, name + ".py")
        if not os.path.exists(fn):
            return
        with open(fn) as f:
            code = compile(f.read(), fn, "exec")
            eval(code, ns, ns)
        return ns["cli"]


@click.version_option(__version__, "-v", "--version")
@click.command(cls=CLI)
def cli():
    """The CLI of nostr."""


if __name__ == "__main__":
    cli()
