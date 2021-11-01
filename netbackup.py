#!/usr/bin/env python3.7
from netmiko import Netmiko
from getpass import getpass
from datetime import date, timedelta
from keyring import get_password
from progress.bar import ShadyBar
import os, logging, sys, time, argparse


############
##ARGPARSE##
############
parser = argparse.ArgumentParser(description = "Options for network_backups")
parser.add_argument("-v", "--verbose", help = "Enables verbose output", action="store_true")
parser.add_argument("-l", "--log", help = "Prints most recent log file", action="store_true")

args = parser.parse_args()


########################
##DIRECTORY MANAGEMENT##
########################
date = date.today()
last_date = date.today() - timedelta(days=1)

# SET OUTPUT DIRECTORY HERE
root_dir = "/pynet/test/"

save_dir = os.path.join(root_dir, str(date))
log_dir = (root_dir + "network_backups_" + str(date) + ".log")
last_log_dir = (root_dir + "network_backups_" + str(last_date) + ".log")

if args.log:
        if os.path.isfile(log_dir):
                with open(log_dir) as f:
                        print("Reading from today's logfile.")
                        print(f.read())
                        sys.exit()
        else:
                with open(last_log_dir) as f:
                        print("Reading from yesterday's logfile.")
                        print(f.read())
                        sys.exit()

if not os.path.exists(save_dir):
    os.mkdir(save_dir)


#####################
##CONFIGURE LOGGING##
#####################
# create logger with 'network_backups'
logger = logging.getLogger('network_backups')
logger.setLevel(logging.DEBUG)

# create file handler which logs even debug messages
fh = logging.FileHandler(log_dir)
fh.setLevel(logging.DEBUG)

# create console handler with it's own log level
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

# create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)

# add the handlers to the logger
logger.addHandler(fh)
logger.addHandler(ch)

# set time monitor
start_time = time.time()
current_time = time.strftime("%H:%M:%S", time.localtime())

logger.info("Network configuration backups started at " + current_time + ".")

if args.verbose:
        ch.setLevel(logging.DEBUG)
        logger.info("Verbose mode enabled.")
        loader_visual = False
else:
        ch.setLevel(logging.WARNING)
        loader_visual = True

logger.info("Backup directory set as: " + save_dir)
logger.info("Log file(s) can be found at " + log_dir)


#########################
##CONFIGURE CREDENTIALS##
#########################
# prompt for username
username = input("Enter username: ")

# set hardcoded username if required
#username = "hardcoded_username_here"

# prompt for password
password = getpass("Enter password: ")

# set password using getpass
#password = get_password('passfile', 'username')
#key_file = "/home/gituser/.ssh/test_rsa"

#prompt for command
#command = input("Enter command: ")

# set hardcoded command, default is to show configuration
command = "show configuration"


####################
##CREATE HOSTLISTS##
####################
hostlist_dc1 = ['dc1-test1.example.net', 'dc1-router-1a.example.net', 'dc1-dns-server-1.example.net', 'd1-dns-server-2.example.net']
hostlist_dc2 = ['dc2-test2.example.net', 'dc2-router-1a.example.net']
#hostlist_dc3 = ['dc3-test3.example.net', 'dc3-router-1a.example.net', 'dc3-dns-server-1.example.net']


########################################
##ADD/REMOVE ACTIONABLE HOSTLISTS HERE##
########################################
hostlist_complete = hostlist_dc1 + hostlist_dc2

# initiate progress bar
bar = ShadyBar('Processing', max=(len(hostlist_complete)))

for host in hostlist_complete:

        if loader_visual == True:
                bar.next()

        junos1 = {
                "device_type": "juniper_junos",
                "host": host,
                "username": username,
                #"use_keys": True,
                #"key_file": key_file,
                "password": password,
                "global_delay_factor": 2,
        }

        filename = (save_dir + "/" + host + "_" + str(date) + ".txt")

        #input(filename)

        try:
                net_connect = Netmiko(**junos1)
                #logger.info(net_connect.find_prompt())
        except:
                logger.info(host + " failed to connect, skipping...")
                continue

        output = net_connect.send_command(command)
        with open(filename, "a") as f:
                print(output, file=f)
        net_connect.disconnect()
        logger.info(host + " backed up successfully...")

bar.finish()

# calculate and output run time
logger.info("Task completed in %.2f minutes!" % ((time.time() - start_time)/60))
