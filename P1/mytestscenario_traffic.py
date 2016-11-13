#!/usr/bin/env python

import sys
import time
from switchyard.lib.address import *
from switchyard.lib.packet import *
from switchyard.lib.common import *
from switchyard.lib.testing import *

def mk_pkt(hwsrc, hwdst, ipsrc, ipdst, reply=False):
    ether = Ethernet()
    ether.src = EthAddr(hwsrc)
    ether.dst = EthAddr(hwdst)
    ether.ethertype = EtherType.IP
    
    ippkt = IPv4()
    ippkt.srcip = IPAddr(ipsrc)
    ippkt.dstip = IPAddr(ipdst)
    ippkt.protocol = IPProtocol.ICMP
    ippkt.ttl = 32
    
    icmppkt = ICMP()
    if reply:
        icmppkt.icmptype = ICMPType.EchoReply
    else:
        icmppkt.icmptype = ICMPType.EchoRequest
    
    return ether + ippkt + icmppkt

def switch_tests():
    s = Scenario("switch tests")
    s.add_interface('eth1', '10:00:00:00:00:01')
    s.add_interface('eth2', '10:00:00:00:00:02')
    s.add_interface('eth3', '10:00:00:00:00:03')
    
    # test case 1: A -> switch
    reqpkt = mk_pkt("20:00:00:00:00:01", "10:00:00:00:00:02", '192.168.1.100','172.16.42.2')
    s.expect(PacketInputEvent("eth2", reqpkt, display=Ethernet), "An Ethernet frame from 20:00:00:00:00:01 to 10:00:00:00:00:02 should arrive on eth2")
    s.expect(PacketInputTimeoutEvent(1.0), "The hub should not do anything in response to a frame arriving with a destination address referring to itself.")
    
    
    # test case 1: A -> broadcast
    testpkt = mk_pkt("30:00:00:00:00:01", "ff:ff:ff:ff:ff:ff", "172.16.42.2", "255.255.255.255")
    s.expect(PacketInputEvent("eth1", testpkt, display=Ethernet), "An Ethernet frame with a broadcast destination address should arrive on eth1")
    s.expect(PacketOutputEvent("eth2", testpkt, "eth3", testpkt, display=Ethernet), "The Ethernet frame with a broadcast destination address should be forwarded out ports eth2 and eth3")
    
    
    # test case 1: A -> B
    reqpkt = mk_pkt("20:00:00:00:00:01", "20:00:00:00:00:02", '192.168.1.100','172.16.42.2')
    s.expect(PacketInputEvent("eth1", reqpkt, display=Ethernet), "An Ethernet frame from 20:00:00:00:00:01 to 20:00:00:00:00:02 should arrive on eth1")
    s.expect(PacketOutputEvent("eth2", reqpkt, "eth3", reqpkt, display=Ethernet), "Should be flooded out eth2 and eth3")
    
    for i in range(4):
        # test case 2: B -> A
        reqpkt = mk_pkt("20:00:00:00:00:02", "20:00:00:00:00:01", '172.16.42.2','192.168.1.100')
        s.expect(PacketInputEvent("eth2", reqpkt, display=Ethernet), "An Ethernet frame from 20:00:00:00:00:02 to 20:00:00:00:00:01 should arrive on eth2")
        s.expect(PacketOutputEvent("eth1", reqpkt, display=Ethernet), "Ethernet frame destined for 20:00:00:00:00:01 should be forwarded to eth1")
        
    for i in range(2):
        # test case 1: A -> B
        reqpkt = mk_pkt("20:00:00:00:00:01", "20:00:00:00:00:02", '192.168.1.100','172.16.42.2')
        s.expect(PacketInputEvent("eth1", reqpkt, display=Ethernet), "An Ethernet frame from 20:00:00:00:00:01 to 20:00:00:00:00:02 should arrive on eth1")
        s.expect(PacketOutputEvent("eth2", reqpkt, display=Ethernet), "Ethernet frame destined for 20:00:00:00:00:02 should be forwarded to eth2")
    
    # test case 1: A -> C
    reqpkt = mk_pkt("40:00:00:00:00:01", "20:00:00:00:00:03", '192.168.1.100','172.16.42.2')
    s.expect(PacketInputEvent("eth1", reqpkt, display=Ethernet), "An Ethernet frame from 40:00:00:00:00:01 to 20:00:00:00:00:03 should arrive on eth1")
    s.expect(PacketOutputEvent("eth2", reqpkt, "eth3", reqpkt, display=Ethernet), "Should be flooded out eth2 and eth3")
    
    for i in range(6):
        # test case 2: C -> A
        reqpkt = mk_pkt("20:00:00:00:00:03", "40:00:00:00:00:01", '172.16.42.2','192.168.1.100')
        s.expect(PacketInputEvent("eth3", reqpkt, display=Ethernet), "An Ethernet frame from 20:00:00:00:00:03 to 40:00:00:00:00:01 should arrive on eth3")
        s.expect(PacketOutputEvent("eth1", reqpkt, display=Ethernet), "Ethernet frame destined for 40:00:00:00:00:01 should be forwarded to eth1")
    
    for i in range(8):
        # test case 1: A -> C
        reqpkt = mk_pkt("40:00:00:00:00:01", "20:00:00:00:00:03", '192.168.1.100','172.16.42.2')
        s.expect(PacketInputEvent("eth1", reqpkt, display=Ethernet), "An Ethernet frame from 40:00:00:00:00:01 to 20:00:00:00:00:03 should arrive on eth1")
        s.expect(PacketOutputEvent("eth3", reqpkt, display=Ethernet), "Ethernet frame destined for 20:00:00:00:00:03 should be forwarded to eth3")
    
    # test case 2: C -> A
    reqpkt = mk_pkt("30:00:00:00:00:03", "30:00:00:00:00:01", '172.16.42.2','192.168.1.100')
    s.expect(PacketInputEvent("eth3", reqpkt, display=Ethernet), "An Ethernet frame from 30:00:00:00:00:03 to 30:00:00:00:00:01 should arrive on eth3")
    s.expect(PacketOutputEvent("eth1", reqpkt, "eth2", reqpkt, display=Ethernet), "Should be flooded out eth1 and eth2")
    
    # test case 1: A -> C
    reqpkt = mk_pkt("30:00:00:00:00:01", "30:00:00:00:00:03", '192.168.1.100','172.16.42.2') 
    s.expect(PacketInputEvent("eth1", reqpkt, display=Ethernet), "An Ethernet frame from 30:00:00:00:00:01 to 30:00:00:00:00:03 should arrive on eth1")
    s.expect(PacketOutputEvent("eth2", reqpkt, "eth3", reqpkt, display=Ethernet), "Should be flooded out eth2 and eth3")

    for i in range(10):
        # test case 1: A -> C
        reqpkt = mk_pkt("40:00:00:00:00:01", "30:00:00:00:00:01", '192.168.1.100','172.16.42.2')
        s.expect(PacketInputEvent("eth1", reqpkt, display=Ethernet), "An Ethernet frame from 40:00:00:00:00:01 to 30:00:00:00:00:01 should arrive on eth1")
        s.expect(PacketOutputEvent("eth1", reqpkt, display=Ethernet), "Ethernet frame destined for 30:00:00:00:00:01 should be forwarded to eth1")
        
    # test case 1: A -> C
    reqpkt = mk_pkt("60:00:00:00:00:01", "30:00:00:00:00:03", '192.168.1.100','172.16.42.2')
    s.expect(PacketInputEvent("eth1", reqpkt, display=Ethernet), "An Ethernet frame from 60:00:00:00:00:01 to 30:00:00:00:00:03 should arrive on eth1")
    s.expect(PacketOutputEvent("eth2", reqpkt, "eth3", reqpkt, display=Ethernet), "Should be flooded out eth2 and eth3")

    # test case 1: A -> B
    reqpkt = mk_pkt("20:00:00:00:00:01", "20:00:00:00:00:02", '192.168.1.100','172.16.42.2')
    s.expect(PacketInputEvent("eth1", reqpkt, display=Ethernet), "An Ethernet frame from 20:00:00:00:00:01 to 20:00:00:00:00:02 should arrive on eth1")
    s.expect(PacketOutputEvent("eth2", reqpkt, "eth3", reqpkt, display=Ethernet), "Should be flooded out eth2 and eth3")
    #time.sleep(15)
    
    return s

scenario = switch_tests()





