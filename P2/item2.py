#!/usr/bin/env python3

'''
Basic IPv4 router (static routing) in Python.
'''


import sys
import os
import re
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

class QueueEntry(object):
    """__init__() functions as the class constructor"""
    def __init__(self, pkt=None, waiting_ip_addr=None, interface_to_send=None, push_time=None):
        self.pkt = pkt
        self.waiting_ip_addr = waiting_ip_addr
        self.interface_to_send = interface_to_send
        self.push_time = push_time



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
        self.forward_table =[]
        self.my_interfaces = net.interfaces()

        for intf in self.my_interfaces:
            new_entry = ArpTableEntry(intf.ipaddr, intf.ethaddr, intf.name, time.time())
            self.add_arp_entry(new_entry)

        self.readFile(fileName)
        

    def add_forward_entry(self, new_entry):
        self.forward_table.append(new_entry)

    def readFile(self, file):
        f = open(file, 'r')
        for line in f:
            tmp = re.split("[ \n']+", line)
            new_entry = ForwardTableEntry(tmp[0], tmp[1], tmp[2], tmp[3])
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
        next_hop = None
        for entry in self.forward_table:
            l = IPv4Network(str(entry.prefix) + "/" + str(entry.mask))
            l = l.prefixlen

            prefixnet = IPv4Network(str(entry.prefix) + "/" + str(l))
            matches = dest_addr in prefixnet

            if (matches) and l > max_l:
                max_l = l
                next_intf = entry.interfaceName
                next_hop = entry.nextHop

        # next_intf ="eth2"
        # return "eth5", "0.0.0.0"
        return next_intf, next_hop


    def get_nextHop_ethaddr(self, sender, nextHopIP):
        res = None
        isInterface = False

        senderhwaddr = None
        senderprotoaddr = None
        for intf in self.my_interfaces:
            if intf.name == sender:
                senderhwaddr = intf.ethaddr
                senderprotoaddr = intf.ipaddr
                break
        if senderhwaddr == None:
            log_debug("this interface is not in the my_interfaces")

        targetprotoaddr = nextHopIP
        arp_request = create_ip_arp_request(senderhwaddr, senderprotoaddr, targetprotoaddr)
        self.net.send_packet(sender, arp_request)

        return res, isInterface
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
                    ip_vector = [intf.ipaddr for intf in self.my_interfaces]                        
                    if arp.operation == ArpOperation.Request: 
                        #remember the pair by add_entry to the lookup_table
                        entry = ArpTableEntry(arp.senderprotoaddr, arp.senderhwaddr, \
                                            dev_interface, time.time())
                        self.add_arp_entry(entry)

                        if arp.targetprotoaddr in ip_vector:
                            # I am the target, create arp reply and send back
                            idx = ip_vector.index(arp.targetprotoaddr)
                            targethwaddr = self.my_interfaces[idx].ethaddr
                            rep_pkt = create_ip_arp_reply(targethwaddr, arp.senderhwaddr, self.my_interfaces[idx].ipaddr,  arp.senderprotoaddr)
                            self.net.send_packet(dev_name, rep_pkt)
                        else:
                            pass
                    else:
                        if arp.targetprotoaddr in ip_vector: #response back to me
                            # take the corresponding ipv4 from queue and construct arp, then send 
                            # if 5 time failure, give up and drop
                            index = -1
                            for i in range(len(pkt_queue)):
                                if self.pkt_queue[i].waiting_ip_addr == arp.senderprotoaddr:# the ip I am waiting
                                    index = i
                                    break
                            if index == -1:
                                log_debug("although the response is for me, but the queue is clear")
                            
                            eth_header = Ethernet() #create new ethernet header
                            eth_header.dst = arp.targethwaddr
                            eth_header.src = arp.senderhwaddr

                            #get the corresponding pkt in the queue
                            item = pkt_queue.pop(index)
                            pkt_to_send = item.pkt
                            interface_to_send = item.interface_to_send

                            pkt_to_send += eth_header
                            net.send_packet(interface_to_send, pkt_to_send)

                elif ipv4 is not None: # it is an ip forwarding packet
                    pkt_to_me = self.find_pkt_to_me(ipv4.dst)
                    if pkt_to_me == True:
                        pass
                    else:
                        next_intf, nextHop = self.look_up(ipv4.dst)
                        if next_intf == None:
                            pass #not found a match
                        else:
                            pkt[IPv4].ttl -= 1 #not consider expired for now
                            self.get_nextHop_ethaddr(next_intf, nextHop) #get nextHop ethernet address
                            queue_item = QueueEntry(pkt, ipv4.dst, next_intf, time.time())
                            self.pkt_queue.append(queue_item)
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