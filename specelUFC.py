from socket import socket, error
from time import sleep

from packaging import version
from requests import get

from dcsbiosParser import ProtocolParser
from specelG13Handler import G13Handler

__version__ = "v1.12"


def attemptConnect(s):
    """
    Attempt to connect to localhost.

    :param s: socket
    """
    connected = False
    print("Waiting for DCS connection...")
    while not connected:
        try:
            s.connect(("127.0.0.1", 7778))
            print("Connected")
            connected = True
        except error:
            sleep(2)


def checkCurrentVersion():
    """Check if version is current."""
    try:
        url = "https://api.github.com/repos/specel/specelUFC/releases/latest"
        response = get(url)
        if response.status_code == 200:
            jsonResponse = response.json()
            onlineVersion = jsonResponse["tag_name"]
            if version.parse(onlineVersion) > version.parse(__version__):
                print("There is updated version of specelUFC: ", onlineVersion,
                      "- get it on https://github.com/specel/specelUFC")
            elif version.parse(onlineVersion) == version.parse(__version__):
                print("This is up-to-date version")
            else:
                print("Something goes wrong: local version:", __version__, ", a onlineVersion:", onlineVersion)
        else:
            print("Unable to check version online. Try again later. Status=", response.status_code())
    except Exception as e:
        print("Unable to check version online: ", e)


def run():
    """Main of running function."""
    print("specelUFC ", __version__, " https://github.com/specel/specelUFC")
    checkCurrentVersion()
    while True:
        parser = ProtocolParser()
        g13 = G13Handler(parser)
        g13.infoDisplay(("G13 initialised OK", "Waiting for DCS", "", "specel UFC " + __version__))

        s = socket()
        s.settimeout(None)

        attemptConnect(s)
        while True:
            try:
                c = s.recv(1)
                parser.processByte(c)
                if g13.shouldActivateNewAC:
                    g13.activateNewAC()

                g13.buttonHandle(s)

            except error as e:
                print("Main loop socket error: ", e)
                sleep(2)

            except Exception as e:
                print("Unexpected error: resetting... : ", e)
                sleep(2)
                break

        del s
        del g13
        del parser


if __name__ == '__main__':
    run()
