#!/usr/bin/env python3

import argparse
import os
import datetime


def get_cli_args():
    parser = argparse.ArgumentParser(
        description="Creates a bi-directional TCP dump for 2 addresses for a specified number of packets"
    )
    parser.add_argument(
        '-1', '--ip1', type=str, help='First IP address to capture', required=True
    )
    parser.add_argument(
        '-2', '--ip2', type=str, help='Second IP address to capture', required=True
    )
    parser.add_argument(
        '-c', '--count', type=int, help='Number of Packets to capture', required=True
    )
    parser.add_argument(
        '-f', '--file', action='store_true', help='Outputs to PCAP File', required=False
    )
    args = parser.parse_args()
    if not (args.ip1 and args.ip2 and args.count):
        print(('{0}' * 50).format('*'))
        print('Must specify First IP, Second IP, and Packet Count')
        print(('{0}' * 50).format('*'))
        parser.print_help()
        os.sys.exit(1)
    return args


def main():
    cli_args = get_cli_args()
    if not cli_args.file:
        print(('{0}' * 50).format('*'))
        print('Collecting TCPDUMP between {ip1} and {ip2} for {count} packets.''\n''Please initiate traffic between'
              ' these addresses.''\n''This will automatically close when the specified packet count is reached''\n'
              'Press Ctrl C to Terminate'.format(**cli_args.__dict__))
        print(('{0}' * 50).format('*'))
        os.system('tcpdump -i eth0 -nc {count} "ip host {ip1} and ip host {ip2}"'.format(**cli_args.__dict__))
        print(('{0}' * 50).format('*'))
        print('TCPDUMP Complete.')
        print(('{0}' * 50).format('*'))
    elif cli_args.file:
        timestamp = str(datetime.datetime.now().strftime('%Y-%m-%d-%H%M'))
        print(('{0}' * 50).format('*'))
        print('Collecting TCPDUMP between {ip1} and {ip2} for {count} packets.''\n''Please initiate traffic between'
              ' these addresses.''\n''This will automatically close when the specified packet count is reached''\n'
              'Press Ctrl C to Terminate'.format(**cli_args.__dict__))
        print(('{0}' * 50).format('*'))
        filename = 'TCPDUMP_{}.pcap'.format(timestamp)
        os.system('tcpdump -i eth0 -nc {count} "ip host {ip1} and ip host {ip2}" -w {filename}'
                  .format(filename=filename, **cli_args.__dict__))
        print(('{0}' * 50).format('*'))
        print('TCPDUMP Complete! PCAP file Exported as:''\n''{}'.format(filename))
        print(('{0}' * 50).format('*'))


main()