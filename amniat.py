#!/usr/bin/env python3

# -*- coding:utf-8 -*-
import os,sys,socket,ipaddress,argparse,textwrap,logging
from scapy.all import *
from ctypes import *
from time import sleep
from threading import Thread
from modules import service_detection,os_detection
from progress.bar import ChargingBar
from colorama import Fore
import rpycolors
# import plotly.graph_objects as go

import networkx as nx

old_print = print
print = rpycolors.Console().print
white   = Fore.WHITE
black   = Fore.BLACK
red     = Fore.RED
reset   = Fore.RESET
blue    = Fore.BLUE
cyan    = Fore.CYAN
yellow  = Fore.YELLOW
green   = Fore.GREEN
magenta = Fore.MAGENTA

OPEN_PORT = 80

logging.getLogger("scapy.runtime").setLevel(logging.ERROR)


clear = lambda:os.system('cls' if os.name == 'nt' else 'clear')
class Scanner:
    def __init__(self,target=None,my_ip=None):
        self.target = target
        self.my_ip = my_ip
        self.protocol = None
        self.timeout = 5
        self.interface = None

    def send_icmp(self,target, result, index):
        target = str(target)
        host_found = []
        pkg = IP(dst=target)/ICMP()
        answers, unanswered = sr(pkg,timeout=3, retry=2,verbose=0,iface=self.interface if self.interface else None)
        answers.summary(lambda r : host_found.append(target))

        if host_found: result[index] = host_found[0]

    def discover_net(self,ip_range=24):
        protocol = self.protocol
        base_ip = self.my_ip

        # print_figlet()

        if not protocol:
            protocol = "ICMP"
        else:
            if protocol != "ICMP":
                logging.warning(f"Warning: {protocol} is not supported by discover_net function! Changed to ICMP")

        if protocol == "ICMP":
            logging.info("Starting - Discover Hosts Scan")

            base_ip = base_ip.split('.')
            base_ip = f"{str(base_ip[0])}.{str(base_ip[1])}.{str(base_ip[2])}.0/{str(ip_range)}"

            hosts = list(ipaddress.ip_network(base_ip))
            bar = ChargingBar("Scanning...", max=len(hosts))

            sys.stdout = None
            bar.start()

            threads = [None] * len(hosts)
            results = [None] * len(hosts)

            for i in range(len(threads)):
                threads[i] = Thread(target=self.send_icmp,args=(hosts[i], results, i))
                threads[i].start()

            for i in range(len(threads)):
                threads[i].join()
                bar.next()

            bar.finish()
            sys.stdout = sys.__stdout__

            hosts_found = [i for i in results if i is not None]

            if not hosts_found:
                logging.warn('[[red]-[/red]]Not found any host')
            else:
                print("")
                logging.info(f'{len(hosts_found)} hosts founded')
                for host in hosts_found:
                    logging.info(f'Host found: {host}')
                G = nx.Graph()
                G.add_node("Server")
                for nodes in hosts_found:
                    G.add_node(nodes)
                    G.add_edge(nodes, "Server")
                logging.info(G)
                nx.draw(G, with_labels=True)
                plt.savefig('graph.png')

            return True
        else:
            logging.critical("[[red]-[/red]]Invalid protocol for this scan")

            return False

def arguments():
    parser = argparse.ArgumentParser(description="",usage="")
    parser.add_argument('Target',nargs='?',default=None)

    args = parser.parse_args()

    return (args, parser)

if __name__ == '__main__':
    args, parser = arguments() 

    del logging.root.handlers[:]
  
    logging.addLevelName(logging.CRITICAL, f"[{red}!!{reset}]")
    logging.addLevelName(logging.WARNING, f"[{red}!{reset}]")
    logging.addLevelName(logging.INFO, f"[{cyan}*{reset}]")
    logging.addLevelName(logging.DEBUG, f"[{cyan}**{reset}]")


    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8",80))
    ip = s.getsockname()[0]
    s.close()

    scanner = Scanner(target=args.Target,my_ip=ip)

    scanner.discover_net()
