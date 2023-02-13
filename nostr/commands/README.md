
## KEY

### Create a key pair
```
❯ python -m nostr.cli key create
Private key: nsec18tyg07d7x2qqu0xfja3ujmeca3g2dcs2ykcwhmggfc8z434w23ss002xz6
Public key: npub1rak2mfruhnckmtdvwpr3ds5p5609ppqmszfqgad4unxer2l0gjwsk658cm
```

### Transform public key to hex format
```
❯ python -m nostr.cli key npub-to-hex npub1rak2mfruhnckmtdvwpr3ds5p5609ppqmszfqgad4unxer2l0gjwsk658cm
npub: npub1rak2mfruhnckmtdvwpr3ds5p5609ppqmszfqgad4unxer2l0gjwsk658cm
hex: 1f6cada47cbcf16dadac704716c281a69e50841b80920475b5e4cd91abef449d
```

### Show version
```
❯ python -m nostr.cli --version
python -m nostr.cli, version 0.0.3.dev5+g649c474.d20230212
```

## MESSAGE

### Receive message from relay
```
python -m nostr.cli message receive <npub> 20
❯ python -m nostr.cli message receive <npub> 20
npub: <npub>
Websocket connected
OPEN: wss://nostr-pub.wellorder.net
Websocket connected
OPEN: wss://relay.damus.io
Hello send message CLI
...
CLOSE: wss://nostr-pub.wellorder.net - None
```

### Send a message
```
❯ python -m nostr.cli message send <nsec> "Hello send message CLI"
Websocket connected
OPEN: wss://nostr-pub.wellorder.net
Websocket connected
OPEN: wss://relay.damus.io
CLOSE: wss://nostr-pub.wellorder.net - None
CLOSE: wss://relay.damus.io - None
```

### Send an encryped direct message
```
❯ python -m nostr.cli message direct <nsec> "Hello encryped direct message" <receiver npub>
Websocket connected
OPEN: wss://relay.damus.io
Websocket connected
OPEN: wss://nostr-pub.wellorder.net
CLOSE: wss://nostr-pub.wellorder.net - None
CLOSE: wss://relay.damus.io - None
```
