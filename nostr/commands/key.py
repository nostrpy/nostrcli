import click

from nostr.key import PrivateKey, PublicKey


@click.group()
def cli():
    """Command related to key(s)."""


@cli.command()
def create():
    """Creates a private and public key."""
    private_key = PrivateKey()
    public_key = private_key.public_key
    click.echo(f"Private key: {private_key.bech32()}")
    click.echo(f"Public key: {public_key.bech32()}")


@cli.command()
@click.option("-p", "--pub-key", "npub", required=True, type=str)
def npub_to_hex(npub: str):
    """Converts npub key to hex."""
    public_key = PublicKey.from_npub(npub)
    click.echo(f"npub: {public_key.bech32()}")
    click.echo(f"hex: {public_key.hex()}")
