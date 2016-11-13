#!/usr/bin/env python3

'''
Basic IPv4 router (static routing) in Python.
'''


import sys
import os
import time
from switchyard.lib.packet import *
from switchyard.lib.address import *
from switchyard.lib.common import *

class ArpTableEntry(object):
    """__init__() functions as the class constructor"""
    def __init__(self, ip_addr=None, mac_addr=None, port=None, arrv_time=None):
        self.mac_addr = mac_addr
        self.ip_addr = ip_addr
        self.port = port
        self.arrv_time = arrv_time


class Router(object):
    def __init__(self, net):
        self.net = net
        self.lookup_table = []
        self.my_interfaces = net.interfaces()


    def add_entry(self, new_entry):
        tmp_ip = [entry.ip_addr for entry in self.lookup_table]
        if new_entry.ip_addr in tmp_ip:
            return

        self.lookup_table.append(new_entry)

    def router_main(self):    
        '''
        Main method for router; we stay in a loop in this method, receiving
        packets until the end of time.
        '''
        while True:
            gotpkt = True
            try:
                dev_name,pkt = self.net.recv_packet(timeout=1.0)
            except NoPackets:
                log_debug("No packets available in recv_packet")
                gotpkt = False
            except Shutdown:
                log_debug("Got shutdown signal")
                break

            if gotpkt:
                log_debug("Got a packet: {}".format(str(pkt)))

                arp = pkt.get_header(Arp)
                dev = self.net.interface_by_name(dev_name)                
                if arp is not None:
                    if arp.targetprotoaddr == dev.ipaddr:
                        if arp.operation == ArpOperation.Request: #request, 2 for reply
                            entry = ArpTableEntry(arp.senderprotoaddr, arp.senderhwaddr, \
                                                dev, time.time())
                            self.add_entry(entry)

                            arp_reply = create_ip_arp_reply(dev.ethaddr, arp.senderhwaddr, \
                                                            dev.ipaddr, arp.senderprotoaddr)
                            self.net.send_packet(dev_name, arp_reply)

                        # ip_vector = [entry.ipaddr for intf in self.my_interfaces]

                        
                        # if arp.targetprotoaddr in ip_vector:
                        #     # I am the target, create arp reply and send back
                        #     idx = ip_vector.index(arp.targetprotoaddr)
                        #     targethwaddr = self.my_interfaces[idx].ethaddr
                        #     rep_pkt = create_ip_arp_reply(arp.senderhwaddr, targethwaddr, arp.senderprotoaddr, arp.targetprotoaddr)
                        #     outgoing_port = self.net.interface_by_name(dev)
                        #     net.send_packet(outgoing_port, rep_pkt)
                        else:
                            #I am not the target, forward it.
                            #what if I have the information of the dest?

                            # for intf in self.my_interfaces:
                            #     if dev != intf.name:
                            #         net.send_packet(intf.name, pkt)

                            pass




def switchy_main(net):
    '''
    Main entry point for router.  Just create Router
    object and get it going.
    '''
    r = Router(net)
    r.router_main()
    net.shutdown()