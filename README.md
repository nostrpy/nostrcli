# nostrpy

| | | |
| --- | --- | --- |
| CI/CD | [![codecov](https://codecov.io/gh/nostrpy/nostrcli/branch/main/graph/badge.svg?token=VVTLYM68Z5)](https://codecov.io/gh/nostrpy/nostrcli) | [![CircleCI](https://circleci.com/gh/nostrpy/nostrcli.svg?style=svg)](https://circleci.com/gh/nostrpy/nostrcli) |
 -----

CLI for [Nostr](https://github.com/nostr-protocol/nostr)

## Installation
```bash
❯ pip install nostrpy
```

## Usage

**Show nostr version**
```bash
❯ nostr --version
nostr, version 0.6.0
```

**Generate a key pair**
```bash
❯ nostr key new
{
  "Private key": "nsec1w54...edu3",
  "Public key": "npub1s92...7ckp"
}
```

**Transform a public key to hex format, or from hex format to public key format**
```bash
❯ nostr key convert -i 1a60c40a7...b472
{
  "npub": "npub1rfs...c9tg",
  "hex": "1a60c40a7...b472"
}
```

**Publish a message**
```bash
❯ nostr message publish -s <the sender nsec key> -m "Hello, publishing a message through nostr CLI."
{
  "Message": "Hello, publishing a message through nostr CLI."
}
```

**Send an encryped direct message**
```bash
❯ nostr message send -s <the sender nsec key> -m "Hello, sending an encryped direct message" -p <the receiver npub key>
{
  "Message": "Hello, sending an encryped direct message"
}
```

**Receive message(s)**
```
❯ nostr message receive -p <the npub key to receive the messages>
{
  "Public key": "npub1rfs...c9tg",
  "Events": [
    "Hello, publishing a message through nostr CLI.",
    "Hello, sending an encryped direct message"
  ],
  "Notices": []
}
```

### Simplify the CLI with a config file: `config.hcl`:
```config.hcl
nostr {
    relays = [
        "wss://nostr-pub.wellorder.net",
        "wss://relay.damus.io",
    ]

    self {
        name = "Ali Kiten"

        nsec = "nsec1jqa...fcjd"
    }

    receiver "Ray" {
        name = "Ray Nostr"

        npub = "npub1q75...c62u"
    }

    listen "jon" {
        name = "Jonathon Gate"

        npub = "npub1s9c...a9je"
    }

    listen "jack" {
        name = "Jack Hoose"

        npub = "npub1s9c...a9je"
    }
}
```
By default, nostr will search the current path `config.hcl` first, then `${HOME}/.nostr/config.hcl`.

You can also manually specify the config file by:
```
❯ nostr message -c <path/to/the/config.hcl> receive -i jack
```
Once setting up the config file, the above message commands could be much simpler:

**Publish a message with config file**
```bash
❯ nostr message publish -m "Hello, publishing a message through nostr CLI."
{
  "Message": "Hello, publishing a message through nostr CLI."
}
```

**Send an encryped direct message**
```bash
❯ nostr message send -m "Hello, sending an encryped direct message" -i <the receiver identifier, like "Ray" in the above sample>
{
  "Message": "Hello, sending an encryped direct message"
}
```

**Receive message(s)**
```
❯ nostr message receive -i <the listen indentifier in the above sample config file>
{
  "Public key": "npub1rfs...c9tg",
  "Events": [
    "Hello, publishing a message through nostr CLI.",
    "Hello, sending an encryped direct message"
  ],
  "Notices": []
}
```



## Development & Test
See the [Test Suite README](test/README.md)

Feel free to add issues, add PRs, or provide any feedback!

## Credits
Repositories:
- https://github.com/jeffthibault/python-nostr
- https://github.com/BrightonBTC/bija
- https://github.com/holgern/pynostr
