import sacn


def create_sender(**kwargs):
    hosts = [
        "192.168.1.237",
        "192.168.1.240",
    ]

    host1_addr = "192.168.1.237"
    host2_addr = "192.168.1.240"
    bind_addr = "0.0.0.0"
    bind_addr = "127.0.0.1"

    sender = sacn.sACNsender(**kwargs)  # provide an IP-Address to bind to if you are using Windows and want to use multicast
    sender.start()  # start the sending thread

    for i, addr in enumerate(hosts):
        universe = i+1
        sender.activate_output(universe)
        sender[universe].multicast = False
        sender[universe].multicast = False
        sender[universe].destination = addr

    return sender
