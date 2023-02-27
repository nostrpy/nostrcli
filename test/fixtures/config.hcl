nostr {
    relays = [
        "wss://nostr-pub.wellorder.net",
        "wss://relay.damus.io",
    ]

    self {
        name = "Ali Kiten"

        nsec = "nsec1jqaxtwk4tymddju9dmn58tdxgwgl5ck23gg847fla9cyuslxklrq86fcjd"
    }

    receiver "Ray" {
        name = "Ray Nostr"

        npub = "npub1q75f9j9w4zzjf5978eh6ym3pewvrnq5p7tdpaf9anzqmvgkgz8ys22c62u"
    }

    listen "jon" {
        name = "Jonathon Gate"

        npub = "npub1s9c53smfq925qx6fgkqgw8as2e99l2hmj32gz0hjjhe8q67fxdvs3ga9je"
    }

    listen "jack" {
        name = "Jack Hoose"

        npub = "npub1s9c53smfq925qx6fgkqgw8as2e99l2hmj32gz0hjjhe8q67fxdvs3ga9je"
    }
}
