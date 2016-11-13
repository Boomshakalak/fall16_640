#!/usr/bin/env python

'''
Ethernet switch in Python.
'''
from switchyard.lib.address import *
from switchyard.lib.packet import *
from switchyard.lib.common import *

class TableEntry(object):
    """__init__() functions as the class constructor"""
    def __init__(self, mac_addr=None, port=None, traffic=None):
        self.mac_addr = mac_addr
        self.port = port
        self.traffic = traffic
        

forwarding_table = [] #global forwarding table


def add_entry(new_entry):
    tb_macs = [entry.mac_addr for entry in forwarding_table]
    if new_entry.mac_addr in tb_macs:
        match_idx = tb_macs.index(new_entry.mac_addr)
        new_entry.traffic = new_entry.traffic + forwarding_table[match_idx].traffic
        forwarding_table.pop(match_idx)

    if len(forwarding_table) == 5:
        min_idx = 0
        idx = 0
        for entry in forwarding_table:
            if forwarding_table[min_idx].traffic > entry.traffic:
                min_idx = idx
            idx = idx + 1
        forwarding_table.pop(min_idx)

    forwarding_table.append(new_entry)
    return

def up_entry(mac):
    tb_macs = [entry.mac_addr for entry in forwarding_table]
    if mac in tb_macs:
        match_idx = tb_macs.index(mac)
        forwarding_table[match_idx].traffic = forwarding_table[match_idx].traffic + 1
        old_entry = forwarding_table[match_idx]
        forwarding_table.pop(match_idx)
        forwarding_table.append(old_entry)
    return
    
def switchy_main(net):
    my_interfaces = net.interfaces()
    my_macs = [intf.ethaddr for intf in my_interfaces]
    
    while True:
        try:
            port,packet = net.recv_packet()
        except NoPackets:
            continue
        except Shutdown:
            return
    
        oEntry = TableEntry(packet[0].src, port, 0 )
        add_entry(oEntry)
        up_entry(packet[0].dst)
        
        if packet[0].dst in my_macs:
            log_debug ("Packet intended for me")
            #break
        else:
            tb_macs = [entry.mac_addr for entry in forwarding_table]
            if packet[0].dst in tb_macs:
                match_idx = tb_macs.index(packet[0].dst)
                net.send_packet(forwarding_table[match_idx].port, packet)
            else:
                for intf in my_interfaces:
                    if port != intf.name:
                        net.send_packet(intf.name, packet)
    net.shutdown()








