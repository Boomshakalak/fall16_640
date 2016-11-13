#!/usr/bin/env python

'''
Ethernet switch in Python.
'''
from switchyard.lib.address import *
from switchyard.lib.packet import *
from switchyard.lib.common import *
from collections import deque
import time

class TableEntry(object):
    """__init__() functions as the class constructor"""
    def __init__(self, mac_addr=None, port=None, arrv_time=None):
        self.mac_addr = mac_addr
        self.port = port
        self.arrv_time = arrv_time
        

forwarding_table = [] #global forwarding table


def add_entry(new_entry):
    tb_macs = [entry.mac_addr for entry in forwarding_table]
    if new_entry.mac_addr in tb_macs:
        match_idx = tb_macs.index(new_entry.mac_addr)
        forwarding_table.pop(match_idx)
    forwarding_table.append(new_entry)
    return

        
def refresh_tb():
    cur_time = time.time()
    if len(forwarding_table) > 0:
        durtion = cur_time - forwarding_table[0].arrv_time
        if durtion >= 10:
            forwarding_table.pop(0)
            refresh_tb()
    return
    

def switchy_main(net):
    my_interfaces = net.interfaces()
    my_macs = [intf.ethaddr for intf in my_interfaces]
    
    #i = 1
    while True:
        try:
            port,packet = net.recv_packet()
        except NoPackets:
            #i = i - 1
            continue
        except Shutdown:
            return
    
        oEntry = TableEntry(packet[0].src, port, time.time() )
        add_entry(oEntry)
        refresh_tb()
        
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
        #i = i + 1
        #if i == 6:
        #    time.sleep(10)
    net.shutdown()




