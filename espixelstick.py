import sacn


def create_sender(**kwargs):
    host_addr = "192.168.1.237"

    sender = sacn.sACNsender(**kwargs)  # provide an IP-Address to bind to if you are using Windows and want to use multicast
    sender.start()  # start the sending thread
    sender.activate_output(1)  # start sending out data in the 1st universe
    sender[1].multicast = False  # set multicast to True
    sender[1].destination = host_addr  # or provide unicast information.
    # Keep in mind that if multicast is on, unicast is not used

    return sender
