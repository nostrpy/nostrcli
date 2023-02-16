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
nostr, version 0.0.3.dev5+g649c474.d20230212
```

**Generate a key pair**
```bash
❯ nostr key create
Private key: nsec18ty...2xz6
Public key: npub1rak...58cm
```

**Transform a public key to hex format**
```bash
❯ nostr key npub-to-hex --pub-key npub1rak...58cm
npub: npub1rak...58cm
hex: 1f6cada4...449d
```

**Publish a message**
```bash
❯ nostr message publish -s <the sender nsec key> -m "Hello, publishing a message through nostr CLI."
```

**Send an encryped direct message**
```bash
❯ nostr message send -s <the sender nsec key> -m "Hello, sending an encryped direct message" -p <the receiver npub key>
```

**Receive message(s)**
```
❯ nostr message receive -p <the npub key to receive the messages>
Hello, publishing a message through nostr CLI.
...
```


## Development & Test
See the [Test Suite README](test/README.md)

Feel free to add issues, add PRs, or provide any feedback!

## Credits
Repositories:
- https://github.com/jeffthibault/python-nostr
- https://github.com/BrightonBTC/bija
- https://github.com/holgern/pynostr
