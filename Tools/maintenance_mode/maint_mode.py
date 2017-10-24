#!/usr/bin/env python

import argparse
from cli import *


# Obtain User Arguments for either 'maintenance' or 'production'
def get_cli_args():
    parser = argparse.ArgumentParser(
        description='Enables or Disables Maintenance Mode for a Cisco NXOS 9k Switch'
    )
    parser.add_argument(
        '-m', '--maintenance', action='store_true', default=False, help='Places Device into Maintenance Mode',
        required=False
    )
    parser.add_argument(
        '-p', '--production', action='store_true', default=False, help='Places Device into Production Mode',
        required=False
    )
    args = parser.parse_args()
    return args


def main():
    # Define/Generate Variables based on user input and device querying
    args = get_cli_args()
    save_config = 'copy run start'
    fqdn = cli('show hostname').split('-')
    hostname = '%s-%s-%s' % (fqdn[0], fqdn[1], fqdn[2])
    site = fqdn[0]
    role = fqdn[1]
    inst_side = fqdn[2]
    instance = int(inst_side[0:-1])
    user = cli('show users | grep *').split(' ')
    vpc_peer_status = cli('show ip bgp community ".*.10101" | grep 1.1.1')
    keep_alive_status = cli('show vpc brief | grep keep-alive')
    # Format ROUTE-MAP naming Suffix based on user input
    if args.maintenance:
        route_map_state = 'MAINT_OUT'
        status = 'Maintenance'
    elif args.production:
        route_map_state = 'OUT'
        status = 'Production'
    else:
        print('*' * 100)
        print('Must specify State as either maintenance or production. Use --help for assistance.')
        print('*' * 100)
        exit()

    if args.maintenance:
        print('Since %s mode was selected, checking if the vPC peer is in %s mode' % (status,status))
        # Determine if vPC Peer is in Maintenance Mode (If placing switch in Maintenance Mode)
        if vpc_peer_status != '':
            print('vPC Peer is in currently in Maintenance mode!  Aborting Script!')
            exit()
        else:
            print('vPC Peer is not in Maintenance Mode, Verifying status of vPC Peer')
        # Verify vPC Peer is alive to ensure peer switch is online (If placing switch in Maintenance Mode)
        if 'peer is alive' in keep_alive_status:
            print('vPC Peer is Alive.  Ready to place switch into %s Mode' % (status))
        else:
            print('vPC Peer is not currently alive!  Aborting Script!')
    else:
        print('Skipping vPC Peer Sanity Checks since %s was selected instead of Maintenance' % (status))

    print('%s is being put into %s by user %s from IP address: %s.' % (hostname,status,user[0],user[-3]))

    # Determine Configuration Criteria based on role/instance and make configuration changes
    if role == 'SPN':
        asn = 64600
        cli('configure ;router bgp %s ;template peer SPN_HLF_UNDERLAY_V4 '
            ';address-family ipv4 unicast ;route-map SPN_HLF_V4_%s out'
            % (asn, route_map_state))
        cli('configure ;router bgp %s ;template peer SPN_ELF_UNDERLAY_V4 '
            ';address-family ipv4 unicast ;route-map SPN_ELF_V4_%s out'
            % (asn, route_map_state))
    elif role == 'ELF':
        asn = 64590
        cli('configure ;router bgp %s ;template peer ELF_CFW_UNDERLAY_V4 '
            ';address-family ipv4 unicast ;route-map ELF_CFW_V4_%s out'
            % (asn, route_map_state))
        cli('configure ;router bgp %s ;template peer ELF_ELF_UNDERLAY_V4 '
            ';address-family ipv4 unicast ;route-map ELF_ELF_V4_%s out'
            % (asn, route_map_state))
        cli('configure ;router bgp %s ;template peer ELF_SPN_UNDERLAY_V4 '
            ';address-family ipv4 unicast ;route-map ELF_SPN_V4_%s out'
            % (asn, route_map_state))
    elif role == 'BLF':
        asn = 64684
        cli('configure ;router bgp %s ;template peer BLF_BLF_UNDERLAY_V4 '
            ';address-family ipv4 unicast ;route-map BLF_BLF_V4_%s out'
            % (asn, route_map_state))
        cli('configure ;router bgp %s ;template peer BLF_SPN_UNDERLAY_V4 '
            ';address-family ipv4 unicast ;route-map BLF_SPN_V4_%s out'
            % (asn, route_map_state))
    elif role == 'SVC':
        asn = 64685
        cli('configure ;router bgp %s ;template peer SVC_SVC_UNDERLAY_V4 '
            ';address-family ipv4 unicast ;route-map SVC_SVC_V4_%s out'
            % (asn, route_map_state))
        cli('configure ;router bgp %s ;template peer SVC_SPN_UNDERLAY_V4 '
            ';address-family ipv4 unicast ;route-map SVC_SPN_V4_%s out'
            % (asn, route_map_state))
    elif role == 'HLF':
        asn = 64670 + instance
        cli('configure ;router bgp %s ;template peer HLF_HLF_UNDERLAY_V4 '
            ';address-family ipv4 unicast ;route-map HLF_HLF_V4_%s out'
            % (asn, route_map_state))
        cli('configure ;router bgp %s ;template peer HLF_SPN_UNDERLAY_V4 '
            ';address-family ipv4 unicast ;route-map HLF_SPN_V4_%s out'
            % (asn, route_map_state))
    else:
        print('*' * 50)
        print('THIS DEVICE DOES NOT SUPPORT MAINT MODE!')
        print('*' * 50)
        exit()

    print('%s has been put into %s by user %s from IP address %s using the %s template.\nSaving Configuration!\n\n\n'
        % (hostname, status, user[0],user[-3],role))
    cli(save_config)
    print('Script Completed Successfully!\n')
    exit()

main()
