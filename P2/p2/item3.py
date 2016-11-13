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
from switchyard.lib.debug import *


#   error type                              error code
#   not match anyone in fwd table           0
#   TTL -> 0                                1
#   ARP Failure(timeout)                    2
#   pkt to me other than ICMP request       3


err = 0.0001
RETRY_TIME = 5
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
    def __init__(self, pkt=None, sender_ip_addr=None, target_ip_addr = None, interface_to_send=None, push_time=None, retry=0):
        self.pkt = pkt
        self.sender_ip_addr = sender_ip_addr
        self.target_ip_addr = target_ip_addr
        self.interface_to_send = interface_to_send
        self.push_time = push_time
        self.retry = retry



class ForwardTableEntry(object):
    """__init__() functions as the class constructor"""
    def __init__(self, prefix=None, nextHop=None, interfaceName=None):
        self.prefix= prefix
        self.nextHop = nextHop
        self.interfaceName = interfaceName


#add_interface(name, ethaddr, ipaddr=None, netmask=None)



class Router(object):
    def __init__(self, net):
        self.net = net
        self.arp_table = []
        self.forward_table =[]
        self.pkt_queue = []
        self.arp_waiting_cache = []
        self.known_arp_ipaddr = []
        self.arp = 0 
        self.my_interfaces = net.interfaces()

        for intf in self.my_interfaces:
            new_entry = ArpTableEntry(intf.ipaddr, intf.ethaddr, intf.name, time.time())
            self.add_arp_entry(new_entry)

        self.readFile(fileName)
        

    def add_forward_entry(self, new_entry):
        self.forward_table.append(new_entry)


    def readFile(self, file):
        #read forwarding_table.txt and add them into the forwrad_table
        f = open(file, 'r')


        #for my interfaces, add them into the forward table and mark the next hop and IP(0.0.0.0)
        for intf in self.my_interfaces:
            # set nexthop for directly connected network to null (no need to forward)
            prefixnet = IPv4Network(str(intf.ipaddr) + "/" + str(intf.netmask), strict=False)
            new_entry = ForwardTableEntry(prefixnet, IPv4Address(0), intf.name)
            self.add_forward_entry(new_entry)

        #for entry in the txt, add them into the forward_table
        for line in f:
            tmp = re.split("[ \n']+", line)
            prefixnet = IPv4Network(str(tmp[0]) + "/" + str(tmp[1]), strict=False)
            new_entry = ForwardTableEntry(prefixnet, IPv4Address(tmp[2]), tmp[3])
            self.add_forward_entry(new_entry)

    #add arp table pair
    def add_arp_entry(self, new_entry):
        tmp_ip = [entry.ip_addr for entry in self.arp_table]
        if new_entry.ip_addr in tmp_ip:
            return

        self.arp_table.append(new_entry)

    #create icmp echo reply
    def create_icmp_reply(self, echo_request):
        icmp_req_hdr = echo_request.get_header(ICMP)
        ipv4hdr = echo_request.get_header(IPv4)

        icmp = ICMP()
        icmp.icmpcode = 0
        icmp.icmptype = ICMPType.EchoReply
        icmp.icmpdata.identifier = icmp_req_hdr.icmpdata.identifier
        icmp.icmpdata.sequence = icmp_req_hdr.icmpdata.sequence
        icmp.icmpdata.data = icmp_req_hdr.icmpdata.data

        succeed, intf_name, nexthop = self.look_up(ipv4hdr.srcip)
        intf = self.net.interface_by_name(intf_name)
        if succeed == -1:
            report_error(echo_request, 0)
            return 
        eth = Ethernet()
        eth.ethertype = EtherType.IPv4
        eth.src = intf.ethaddr
        
        ip = IPv4()
        ip.dstip = ipv4hdr.srcip
        ip.srcip = ipv4hdr.dstip
        ip.ttl = 65



        icmp_reply = eth + ip + icmp

        return icmp_reply, intf_name, nexthop


    #look up the forward table, return the status, interface and nexthop
    def look_up(self, dest):
        max_l = 0
        next_intf = None
        dest_addr = IPv4Address(dest)
        next_hop = None
        count = 0
        for entry in self.forward_table:
            intf = self.net.interface_by_name(entry.interfaceName)
            if intf.ipaddr == dest_addr:                           # ourselves
                return -2, entry.interfaceName, dest

            prefixnet = entry.prefix
            l = prefixnet.prefixlen
            matches = dest_addr in prefixnet

            if matches and l > max_l:
                max_l = l
                next_intf = entry.interfaceName
                next_hop = entry.nextHop
                if entry.nextHop == IPv4Address(0):
                    next_hop = dest

        if next_hop == None:
            return -1, next_intf, next_hop
        else:
            return 0, next_intf, next_hop


    #be called periodically to resend arp requests
    def check_queue(self, cur_time, arp_waiting_cache):
        already_sent = []
        for entry in self.pkt_queue:
            if entry.target_ip_addr in already_sent:
                entry.retry += 1
                entry.push_time = cur_time
                continue
            if cur_time - entry.push_time - 1 > err:
                if entry.retry < RETRY_TIME:
                    already_sent.append(entry.target_ip_addr)
                    entry.push_time = cur_time
                    entry.retry += 1
                    self.send_arp_request(entry.interface_to_send, entry.target_ip_addr)
                else:
                    self.pkt_queue.remove(entry)
                    self.report_error(entry.pkt, 2)

    #forward pkts
    def forward_ipv4_pkt(self, pkt, known_arp_ipaddr, nextHop, next_intf):
        item_index = known_arp_ipaddr.index(nextHop)
        next_hop_mac_addr = self.arp_table[item_index].mac_addr
        pkt[Ethernet].dst = next_hop_mac_addr
        pkt[Ethernet].src = self.net.interface_by_name(next_intf).ethaddr
        self.net.send_packet(next_intf, pkt)


    #send arp request(could be a resending)
    def send_arp_request(self, sender, nextHopIP):
        res = None

        # debugger()
        sender = self.net.interface_by_name(sender)
        senderhwaddr = sender.ethaddr
        senderprotoaddr = sender.ipaddr

        if sender == None:
            log_debug("this interface is not in the my_interfaces")

        targetprotoaddr = IPv4Address(nextHopIP)
        arp_request = create_ip_arp_request(senderhwaddr, senderprotoaddr, nextHopIP)
        self.net.send_packet(sender, arp_request)


    #check the arp request and if I am the target, then reply
    def check_request_and_reply(self, arp, ip_vector, dev_name):
        if arp.targetprotoaddr in ip_vector:
            # I am the target, create arp reply and send back
            idx = ip_vector.index(arp.targetprotoaddr)
            targethwaddr = self.my_interfaces[idx].ethaddr
            # rep_pkt = create_ip_arp_reply(targethwaddr, arp.senderhwaddr, self.my_interfaces[idx].ipaddr,  arp.senderprotoaddr)
            rep_pkt = create_ip_arp_reply(targethwaddr, arp.senderhwaddr, arp.targetprotoaddr,  arp.senderprotoaddr)
            self.net.send_packet(dev_name, rep_pkt)

    #check the arp response and send the pkts in the queue waiting for this response
    def check_response_and_send(self, arp):
        index = []
        already_add = []

        for i in range(len(self.pkt_queue)):## the pkts that are waiting for this arp
            if self.pkt_queue[i].sender_ip_addr == arp.targetprotoaddr \
            and self.pkt_queue[i].target_ip_addr == arp.senderprotoaddr \
            and (arp.senderprotoaddr, arp.targetprotoaddr) not in already_add:
                index.append(i)
                # already_add.append((arp.senderprotoaddr, arp.targetprotoaddr) )

        if index == []:
            log_debug("although the response is for me, but the queue is clear, weird, isn't it?")
            return

        tmp_count = 0 #becasue we pop it each time, the length - 1, so add offset
        for ele in index:
            #get the corresponding pkt in the queue
            item = self.pkt_queue.pop(ele - tmp_count)
            tmp_count += 1
            pkt_to_send = item.pkt

            pkt_to_send[Ethernet].dst = arp.senderhwaddr
            pkt_to_send[Ethernet].src = arp.targethwaddr

            interface_to_send = item.interface_to_send

            self.net.send_packet(interface_to_send, pkt_to_send)


    #push pkts in the queue, let them wait for the response of arp
    def prepare_pkt(self, pkt, next_intf, nextHop, arp_waiting_cache):

        if nextHop not in arp_waiting_cache:
            self.send_arp_request(next_intf, nextHop) #get nextHop ethernet address
        
        next_intf_ipaddr = self.net.interface_by_name(next_intf).ipaddr
        queue_item = QueueEntry(pkt, next_intf_ipaddr, nextHop, next_intf, time.time(), 1)                    
        self.pkt_queue.append(queue_item)


    #create new pkts containing error message
    def report_error(self, pkt, error_code):
        # debugger()
        i = pkt.get_header_index(Ethernet)
        del pkt[i]

        ipv4 = pkt.get_header(IPv4)

        icmp = ICMP()

        if error_code == 0:      
            icmp.icmptype = ICMPType.DestinationUnreachable
            icmp.icmpcode = ICMPTypeCodeMap[ICMPType.DestinationUnreachable].NetworkUnreachable

        elif error_code == 1:       
            icmp.icmptype = ICMPType.TimeExceeded
            icmp.icmpcode = ICMPTypeCodeMap[ICMPType.TimeExceeded].TTLExpired # TTLExpired: 11

        elif error_code == 2:    
            icmp.icmptype = ICMPType.DestinationUnreachable
            icmp.icmpcode = ICMPTypeCodeMap[ICMPType.DestinationUnreachable].HostUnreachable # HostUnreachable: 1

        else:                        
            icmp.icmptype = ICMPType.DestinationUnreachable
            icmp.icmpcode = ICMPTypeCodeMap[ICMPType.DestinationUnreachable].PortUnreachable # PortUnreachable: 3

        icmp.icmpdata.data = pkt.to_bytes()[:28]

        addr = ipv4.srcip
        succeed, intf_name,  nextHop = self.look_up(addr)
        next_intf = self.net.interface_by_name(intf_name)
        if succeed == -1:
            report_error(pkt, 0)
            return 

        ip = IPv4()
        ip.protocol = IPProtocol.ICMP
        ip.dstip = ipv4.srcip
        ip.srcip = next_intf.ipaddr
        ip.ttl = 65

        
        eth = Ethernet()
        eth.ethertype = EtherType.IPv4
        eth.src = next_intf.ethaddr



        pkt = eth + ip + icmp


        if nextHop in self.known_arp_ipaddr:
            self.forward_ipv4_pkt(pkt, self.known_arp_ipaddr, nextHop, intf_name)
        else:
            self.prepare_pkt(pkt, intf_name, nextHop, self.arp_waiting_cache)


    def router_main(self):    
        '''
        Main method for router; we stay in a loop in this method, receiving
        packets until the end of time.
        '''
        while True:
            gotpkt = True
            try:
                dev_name, pkt = self.net.recv_packet(timeout=1.0)
            except NoPackets:
                log_debug("No packets available in recv_packet")
                gotpkt = False
            except Shutdown:
                log_debug("Got shutdown signal")
                break

            if gotpkt:
                log_debug("Got a packet: {}".format(str(pkt)))

                arp = pkt.get_header(Arp)
                self.arp = arp
                ipv4 = pkt.get_header(IPv4)
                icmp = pkt.get_header(ICMP)

                dev_interface = self.net.interface_by_name(dev_name) 

                arp_waiting_cache = [entry.target_ip_addr for entry in self.pkt_queue]
                known_arp_ipaddr = [entry.ip_addr for entry in self.arp_table]
                ip_vector = [intf.ipaddr for intf in self.my_interfaces]  
                self.known_arp_ipaddr = known_arp_ipaddr
                self.arp_waiting_cache = arp_waiting_cache
                

                if arp is not None:
                    if arp.operation == ArpOperation.Request: 
                        #remember the pair by add_entry to the forward_table
                        entry = ArpTableEntry(arp.senderprotoaddr, arp.senderhwaddr, \
                                            dev_interface, time.time())
                        self.add_arp_entry(entry)

                        self.check_request_and_reply(arp, ip_vector, dev_name)
                    else:
                        # received arp reply
                        if arp.targetprotoaddr in ip_vector: #response back to me

                            self.check_response_and_send(arp)
                            entry = ArpTableEntry(arp.senderprotoaddr, arp.senderhwaddr, \
                                            dev_interface, time.time())

                            self.add_arp_entry(entry)


                elif ipv4 is not None: # it is an ip forwarding packet
                    ipv4.ttl -= 1 
                    if ipv4.ttl <= 0: # timeout, error code 1
                        self.report_error(pkt, 1)
                        continue
                    succeed, next_intf, nextHop = self.look_up(ipv4.dstip)
                    next_intf_ipaddr = 0
                    if succeed ==  -1:   #not found a match, drop
                        self.report_error(pkt, 0)
                        continue
                    elif succeed == 0: # found it
                        #need to forward after getting the nexthop mac address
                        if ipv4.dstip in ip_vector:
                            #if exactly the interafce , forward or not?
                            continue
                      
                        if nextHop in known_arp_ipaddr:
                            #I know the hardware addr of next hop, then forward
                            self.forward_ipv4_pkt(pkt, known_arp_ipaddr, nextHop, next_intf)
                        else:
                            #I do not know the hardware addr of next hop, so send arp request
                            self.prepare_pkt(pkt, next_intf, nextHop, arp_waiting_cache)

                    elif succeed == -2:  # to myself
                        if icmp is not None and icmp.icmptype == ICMPType.EchoRequest:
                            #it's a ping and target is me, reply
                            if icmp.icmptype == ICMPType.EchoRequest:   # is echo request
                                icmp_reply, next_intf, nextHop = self.create_icmp_reply(pkt)

                                if nextHop in known_arp_ipaddr:
                                    self.forward_ipv4_pkt(icmp_reply, known_arp_ipaddr, nextHop, next_intf)
                                else:
                                    self.prepare_pkt(icmp_reply, next_intf, nextHop, arp_waiting_cache)
                        else:
                            # it's not a ping and target is me, error code 3
                            self.report_error(pkt, 3)
                else:
                    log_info("Got packet that is not ARP or IPv4, dropping: {}".format(str(pkt)))
            
            self.check_queue(time.time(), arp_waiting_cache)  #check to resend pkt periodically




def switchy_main(net):
    '''
    Main entry point for router.  Just create Router
    object and get it going.
    '''
    r = Router(net)
    r.router_main()
    net.shutdown()