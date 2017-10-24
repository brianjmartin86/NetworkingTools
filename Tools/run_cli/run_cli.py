#!/usr/bin/env python2.7

import argparse
import itertools
import logging
import os
import pexpect
import re
import sys
import yaml
import errno

from collections import namedtuple
from datetime import *
from getpass import getpass

class Connect(object):
    def __init__(self, *args):
        self.host, self.dev_type, self.dev_method, self.username, \
        self.password, self.ssh_key, self.timeout = args

        if self.dev_method == 'ssh':
            self.connect = SSH(self.host, self.dev_type, self.username, self.password, self.ssh_key, self.timeout)
        else:
            raise ValueError("%s is not supported" % self.dev_method)

    def close(self):
        """Close method for session"""
        self.connect.device.close()

class SSH(object):
    def __init__(self, *args):
        self.stdout = True
        self.host, self.dev_type, self.username, self.password, self.ssh_key, self.timeout = args
        self.logger = logging.getLogger(__name__)
        self.dev_type = self.dev_type.lower()

        params_by_dev_type = dict(
            arista={'prompt': "#$"},
            force10={'prompt': "#$", 'extra_return': "\r"},
            hp_apm={'prompt': "> $"},
            root_unix={'prompt': "# $"},
            junos={'prompt': "[>%#] $"},
            cisco={'prompt': "# $"},
        )

        if self.dev_type not in params_by_dev_type.keys():
            raise ValueError("%s not yet supported" % self.dev_type)
        expect_params = params_by_dev_type.get(self.dev_type)

        self.prompt = expect_params.get('prompt')
        self.extra_return = expect_params.get('extra_return', "")

        self.login()

    def login(self):
        ''' Logs into a device or reports a failure '''
        ssh_newkey = 'Are you sure you want to continue connecting'

        self.logger.info('Connecting to %s' % self.host)
        if self.ssh_key:
            self.device = pexpect.spawn(
                'ssh -i %s -l %s %s' % (
                    self.ssh_key, self.username, self.host))
        else:
            self.device = pexpect.spawn(
                'ssh -l %s %s' % (self.username, self.host), maxread=100000)
        self.device.delaybeforesend = .0250
        def mkdirp(path):
            """Make the directories in a path if they don't exist."""
            try:
                os.makedirs(path)
            except OSError as e:
                # Ignore errors where it can't be created because it already exists.
                if e.errno != errno.EEXIST:
                    raise
        mkdirp(os.path.join(os.path.expanduser('~'), 'logs'))
        try:
            self.date = datetime.now().strftime('%Y-%m-%d-%H%M')
            self.device.logfile_read = open(
                '%s/logs/%s_%s.txt' % (
                    os.path.expanduser('~'), self.host, self.date),
                'w')
        except IOError as e:
            self.logger.critical('Could not open logfile for writing')
            self.logger.critical('Continuing to execute without log')
        self.device.logfile = None

        i = self.device.expect([pexpect.TIMEOUT, ssh_newkey,
            'assword:', 'verification failed.', '\$ $', self.prompt])
        if i == 0: # Timeout
            self.logger.error('ERROR!')
            self.logger.error('SSH could not login. Here is what SSH said:')
            raise ValueError('Device timed out')

        elif i == 1: # SSH does not have the public key. Just accept it.
            self.device.sendline ('yes')
            conn = self.device.expect([pexpect.TIMEOUT, 'assword:'])
            if conn == 0: # Timeout
                self.logger.error('ERROR!')
                self.logger.error('SSH could not login. Here is what SSH said:')
                self.logger.error(self.device.before, self.device.after)
                return None
            if conn == 1: # password
                self.device.sendline(self.password)
                last_check = self.device.expect([self.prompt, 'assword:'])
                if last_check == 1:
                    raise ValueError('Device credentials do not work')

        elif i == 2: # Got the password field
            self.device.sendline(self.password)
            conn = self.device.expect([pexpect.TIMEOUT, self.prompt, 'assword:'])
            if conn == 0: # Timeout
                self.logger.error('ERROR!')
                self.logger.error('SSH could not login. Here is what SSH said:')
                if self.device.before:
                    self.logger.error(self.device.before)
                if self.device.after:
                    self.logger.error(self.device.after)
                return None
            elif conn == 1:
                # do nothing, this is what we want
                pass
            elif conn == 2:
                self.logger.error('Device credentials do not work')
                raise ValueError('Device credentials do not work')

        elif i == 3: # SSH key has changed
            self.logger.error(self.device.before)
            raise ValueError('SSH key changed...exiting')
        elif i == 4: # Hop box
            pass
        elif i == 5: # ssh-key authentication
            pass

        self.logger.info("Connected to %s" % self.host)


    def send(self, output_file=None, *lines):
        self.output = ""
        for line in lines:
            if not line:
                continue
            self.logger.info("Executing: %s" % line)
            self.device.sendline('{0}{1}'.format(line, self.extra_return))
            self.device.expect(self.prompt, timeout=self.timeout)
            self.output += self.device.before
        if output_file:
            log_filename = '%s/logs/%s_%s_%s.txt' % (
                os.path.expanduser('~'), self.host, output_file, self.date)
            with open(log_filename, 'w+') as cli_results:
                cli_results.write(self.output + "\n")

def check_cli_args():
    logger = logging.getLogger(__name__)
    parser = argparse.ArgumentParser(
        description="Bulk CLI execution")
    dev_group = parser.add_mutually_exclusive_group(required=True)
    dev_group.add_argument(
        '-d', '--device', type=str,
        help='device name or IP address delimintated by semi-colon'
    )
    dev_group.add_argument(
        '-l', '--device_list', type=str,
        help='CSV seperated file: <ip>,<hostname>,<device_type>'
    )
    dev_group.add_argument(
        '-y', '--yaml', type=str,
        help='YAML file with commands per device type'
    )

    cmd_group = parser.add_mutually_exclusive_group(required=False)
    cmd_group.add_argument(
        '-c', '--commands', type=str,
        help='commands deliminated by semi-colon')
    cmd_group.add_argument(
        '-x', '--command_file', type=str,
        help='File with commands to execute, one per line')

    parser.add_argument(
        '-u', '--username', type=str, required=True,
        help='username for accessing device')

    parser.add_argument(
        '-t', '--type', type=str, help='device type arista', required=True,
        choices=['arista', 'force10', 'hp_apm', 'junos', 'yaml', 'cisco'])

    parser.add_argument(
        '-i', '--debug', type=int, default=20,
        help='10 = Debug, 20 = Info, 30 = Warning, 40 = Error, 50 = Critical')
    parser.add_argument(
        '-w', '--write_cli', action='store_true',
        help='Create individual files with command outout')

    parser.add_argument(
        '-s', '--ssh_key', type=str,
        help='Private key to use for authentication', default=None)
    parser.add_argument(
        '--timeout', type=int,
        help='CLI timeout for expect in seconds', default=180)

    args = parser.parse_args()

    # Convert the ; delminated fields to list
    if args.device:
        tmp = args.device.split(';')
        args.device = [dev.strip() for dev in tmp]

    elif args.device_list:
        with open(args.device_list) as raw_file:
            contents = (raw_file.read()).split('\n')
            #args.device = (raw_file.read()).split('\n')
        args.device = [host.split(',')[0] for host in contents]
    if args.commands:
        tmp = args.commands.split(';')
        args.commands = [cmd.strip() for cmd in tmp]

    elif args.command_file:
        with open(args.command_file) as raw_file:
            args.commands = (raw_file.read()).split('\n')
    return args

def main():

    # Check CLI arguments
    args = check_cli_args()

    # Setup Logging
    logger = logging.getLogger(__name__)
    logger.setLevel(args.debug)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # Need to add a handler for a logfile that records the log output
    # (not just the pexpect stuff)

    # Get a password
    if not args.ssh_key:
        password = getpass("Enter password: ")
    else:
        # need to try and see if the key is valid
        try:
            with open(args.ssh_key):
                pass
        except IOError:
            logger.critical('Could not open %s' % args.ssh_key)
        password = None


    print ""
    bad_devices = []
    # Loop through device list

    if args.yaml:
        with open(args.yaml) as raw:
            devices = yaml.load(raw)
    else:
        devices = args.device
        commands = args.commands

    for host in devices:

        if not host or host.lower() == 'default':
            continue

        if args.yaml:
            # Get the lists of commands
            raw_commands = devices[host]

            # Get the device_type
            dev_type = devices[host]['type']

            # Check to see if we have commands specified
            if 'commands' not in raw_commands \
            and 'global_commands' not in raw_commands:
                # this would indicate that neither the commands
                # nor global commands are present
                logger.critical('YAML file must define commands'
                                'for a host or global_commands for default')

            elif 'commands' in raw_commands \
            and 'global_commands' in raw_commands:
                commands = raw_commands['global_commands'] + raw_commands['commands']

            elif 'commands' in raw_commands:
                commands = raw_commands['commands']

            elif 'global_commands' in raw_commands:
                commands = raw_commands['global_commands']

        else:
            dev_type = args.type
            commands = args.commands
        try:
            device = Connect(
                host,
                dev_type,
                'ssh',
                args.username,
                password,
                args.ssh_key,
                args.timeout)
        except ValueError as error:
            logger.critical(error)
            bad_devices.append(host)
            continue

        if not args.write_cli:
            device.connect.send(None, *commands)
            logger.debug(device.connect.output)
        else:
            for command in commands:
                if not command:
                    continue
                filename = re.sub(r'\s+|/', '_', command)
                filename = re.sub(r'\|', 'pipe', filename)
                device.connect.send(filename, command)
                logger.debug(device.connect.output)

        device.close()
        logger.info('Closing connection to %s' % host)

    for device in bad_devices:
        logger.critical("Could not connect to %s" % device)

if __name__ == '__main__':
    main()
    #try:
    #    main()
    #except KeyboardInterrupt:
    #    logger = logging.getLogger(__name__)
    #    logger.info('CTRL-C Detected... Cleaning up')
    #    os.sys.exit(1)
    #except Exception, err:
    #    logger.info('Main execption caught')
    #    logger.info (err)
    #    os.sys.exit(1)
    #finally:
    #    os.sys.exit(0)
