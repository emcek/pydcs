from logging import basicConfig, DEBUG, info, debug, warning
from socket import socket, error
from time import sleep

from packaging import version
from requests import get

from dcsbiosParser import ProtocolParser
from specelG13Handler import G13Handler

__version__ = 'v1.12'
basicConfig(format='%(asctime)s | %(levelname)-6s | %(message)s / %(filename)s:%(lineno)d', level=DEBUG)


def attempt_connect(s: socket) -> None:
    """
    Attempt to connect to localhost.

    :param s: socket
    """
    connected = False
    info('Waiting for DCS connection...')
    while not connected:
        try:
            s.connect(('127.0.0.1', 7778))
            info('Connected')
            connected = True
        except error:
            sleep(2)


def check_current_version() -> None:
    """Check if version is current."""
    try:
        url = 'https://api.github.com/repos/specel/specelUFC/releases/latest'
        response = get(url)
        if response.status_code == 200:
            json_response = response.json()
            online_version = json_response['tag_name']
            if version.parse(online_version) > version.parse(__version__):
                info('There is updated version of specelUFC: ', online_version,
                      '- get it on https://github.com/specel/specelUFC')
            elif version.parse(online_version) == version.parse(__version__):
                info('This is up-to-date version')
            else:
                debug('Something goes wrong: local version:', __version__, ', a online_version:', online_version)
        else:
            warning('Unable to check version online. Try again later. Status=', response.status_code)
    except Exception as e:
        warning('Unable to check version online: ', e)


def run() -> None:
    """Main of running function."""
    info('specelUFC ', __version__, ' https://github.com/specel/specelUFC')
    check_current_version()
    while True:
        parser = ProtocolParser()
        g13 = G13Handler(parser)
        g13.info_display(('G13 initialised OK', 'Waiting for DCS', '', 'specel UFC ' + __version__))

        s = socket()
        s.settimeout(None)

        attempt_connect(s)
        while True:
            try:
                c = s.recv(1)
                parser.process_byte(c)
                if g13.shouldActivateNewAC:
                    g13.activate_new_ac()

                g13.button_handle(s)

            except error as e:
                debug('Main loop socket error: ', e)
                sleep(2)

            except Exception as e:
                debug('Unexpected error: resetting... : ', e)
                sleep(2)
                break

        del s
        del g13
        del parser


if __name__ == '__main__':
    run()
