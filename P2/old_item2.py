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


fileName = "forwarding_table.txt"
class ArpTableEntry(object):
    """__init__() functions as the class constructor"""
    def __init__(self, ip_addr=None, mac_addr=None, port=None, arrv_time=None):
        self.mac_addr = mac_addr
        self.ip_addr = ip_addr
        self.port = port
        self.arrv_time = arrv_time


class ForwardTableEntry(object):
    """__init__() functions as the class constructor"""
    def __init__(self, prefix=None, mask=None, nextHop=None, interfaceName=None):
        self.prefix= prefix
        self.mask = mask
        self.nextHop = nextHop
        self.interfaceName = interfaceName


#add_interface(name, ethaddr, ipaddr=None, netmask=None)



class Router(object):
    def __init__(self, net):
        self.net = net
        self.arp_table = []
        self.foward_table =[]
        self.my_interfaces = net.interfaces()

        for intf in self.my_interfaces:
            #here the third parameter, intf.ethaddr is actually the nexthop here
            #input format:             172.16.0.0 255.255.255.0 192.168.1.2 router-eth0
            new_entry = ForwardTableEntry(intf.ipaddr, intf.netmask, intf.ethaddr, intf.name)
            self.add_forward_entry(new_entry)

        self.readFile(fileName)
        

    def add_forward_entry(self, new_entry):
        self.foward_table.append(new_entry)

    def readFile(self, file):
        f = open(file, 'r')
        for line in f:
            new_entry = ForwardTableEntry(line[0], line[1], line[2], line[3])
            self.add_forward_entry(new_entry)
        
    def add_arp_entry(self, new_entry):
        tmp_ip = [entry.ip_addr for entry in self.arp_table]
        if new_entry.ip_addr in tmp_ip:
            return

        self.arp_table.append(new_entry)

    def find_pkt_to_me(self, dest):

        for intf in self.my_interfaces:
            if dest == intf.ipaddr:
                return True

        return False

    def look_up(self, dest):
        max_l = 0
        next_intf = None
        dest_addr = IPv4Address(dest)
        for entry in self.foward_table:
            l = IPv4Network(str(entry.prefix) + "/" + str(entry.mask))
            l = l.prefixlen
            # mask = IPv4Address(entry.mask)
            # prefix = IPv4Address(entry.prefix)

            prefixnet = IPv4Network(str(entry.prefix) + "/" + str(l))
            matches = dest_addr in prefixnet

            if (matches) and l > max_l:
                max_l = l
                next_intf = entry.interfaceName
                next_hop = entry.nextHop
        return next_intf, next_hop


    def get_nextHop_ethaddr(self, nextHopIP):
        pass
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
                ipv4 = pkt.get_header(IPv4)
                dev_interface = self.net.interface_by_name(dev_name)                
                if arp is not None:
                    if arp.operation == ArpOperation.Request: 
                        #remember the pair by add_entry to the lookup_table
                        entry = ArpTableEntry(arp.senderprotoaddr, arp.senderhwaddr, \
                                            dev_interface, time.time())
                        self.add_arp_entry(entry)

                        ip_vector = [intf.ipaddr for intf in self.my_interfaces]                        
                        if arp.targetprotoaddr in ip_vector:
                            # I am the target, create arp reply and send back
                            idx = ip_vector.index(arp.targetprotoaddr)
                            targethwaddr = self.my_interfaces[idx].ethaddr
                            rep_pkt = create_ip_arp_reply(targethwaddr, arp.senderhwaddr, self.my_interfaces[idx].ipaddr,  arp.senderprotoaddr)
                            self.net.send_packet(dev_name, rep_pkt)
                        else:
                            pass


                elif ipv4 is not None: # it is an ip forwarding packet
                    pkt_to_me = self.find_pkt_to_me(ipv4.dst)
                    if pkt_to_me == True:
                        pass
                    else:
                        next_intf, nextHop = self.look_up(ipv4.dst)
                        if next_intf == None:
                            pass #not found a match
                        else:
                            pkt[Ethernet].ttl -= 1 #not consider expired for now
                            eth_header = Ethernet() #create new ethernet header
                            nextHop_ethaddr = get_nextHop_ethaddr(nextHop) #get nextHop ethernet address
                            if nextHop_ethaddr == None: # if 5 time failure, give up and drop
                                pass
                            else:
                                eth_header.dst = nextHop_ethaddr
                                pkt += eth_header
                                net.send_packet(next_intf, pkt)

                            #forward it

                else:
                    pass




def switchy_main(net):
    '''
    Main entry point for router.  Just create Router
    object and get it going.
    '''
    r = Router(net)
    r.router_main()
    net.shutdown()