#!/usr/bin/pythonLinearTopo
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.util import irange
from mininet.log import setLogLevel
from mininet.node import RemoteController, CPULimitedHost
from mininet.cli import CLI
from mininet.link import TCLink
import time



class LinearTopo(Topo):

 
 	def __init__(self, k=2, **opts):

 		super(LinearTopo, self).__init__(**opts)
    		self.k = k

    		lastSwitch = None
 		for i in irange(1, k):
 			host = self.addHost('h%s' % i)
			switch = self.addSwitch('s%s' % i)
			self.addLink( host, switch)
			if lastSwitch:
 				self.addLink( switch, lastSwitch)
			lastSwitch = switch



def run():   
    "Create and test a simple network"

    c = RemoteController('c','118.138.235.213',6633)
    topo = LinearTopo(k=4)
    net = Mininet(topo=topo, controller=None)
    net.addController(c)
    net.start()
    print "Testing network connectivity"

    for _ in range(1):
        net.pingAll()

    
    for i in irange(1, len(net.hosts) ):
        for j in irange(i+1, len(net.hosts)):
            (hi,hj) = net.get('h'+str(i), 'h'+str(j) )
            try:
                res = net.iperf((hi,hj))
            except:
                print('Connection between host%d and host%d blocked' % (i,j))
            else:
                print('Bandwidth between host%d and host%d is %s' % (i,j,str(res)) )


    CLI(net)

    time.sleep(10)

    node1 = net.get('s1')
    node2 = net.get('s2')
    net.delLinkBetween(node1,node2)    

    for _ in range(1):
        net.pingAll()

    for i in reversed(irange(1, len(net.hosts))):
        for j in reversed(irange(1,i-1)):
            (hi,hj) = net.get( 'h'+str(i), 'h'+str(j) )
            try:
                res = net.iperf((hi,hj))
            except:
                print('Connection between host%d and host%d blocked' % (i,j))
            else:
                print('Bandwidth between host%d and host%d is %s' % (i,j,str(res)) )


    CLI(net)

    net.stop()

if __name__ == '__main__':
 # Tell mininet to print useful information
    setLogLevel('info')
    run()
