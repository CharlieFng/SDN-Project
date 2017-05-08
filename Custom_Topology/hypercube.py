from mininet.topo import Topo
from mininet.net import Mininet
from mininet.log import setLogLevel, info
from mininet.util import dumpNodeConnections
from mininet.node import RemoteController, CPULimitedHost
from mininet.cli import CLI
from mininet.link import TCLink
import time


class HypercubeTopo( Topo ):
    """ hypercude topo example """

    def __init__(self, n=2):
        """ constructor for hypercude"""
        if n < 1:
            raise Exception( 'Dimension of hypercude must greater than 1 ')
                 
        # Initialize topology
        Topo.__init__( self )

        num = 2**n
        hosts, switches = [None] * num, [None] * num

        for i in range(0, num):
            loc = '%d' % (i + 1)
            switch = switches[i] = self.addSwitch('s' + loc )
            host = hosts[i] =  self.addHost('h' + loc)
            self.addLink(switch,host)


        self.addLinks(switches,n)


    def addLinks(self,switches,k):

        if k == 1 :
            self.addLink(switches[0],switches[1])

        else:

            interval = 2 ** (k-1)
            for i in range(0, interval):
               self.addLink(switches[i], switches[i+interval])

            left = switches[:interval]
            right = switches[interval:]

            self.addLinks(left,k-1)
            self.addLinks(right,k-1)


topos = { 'hypercube': ( lambda n : HypercubeTopo(n) ) }


def run():   
    "Create and test a simple network"

    c = RemoteController('c','118.138.235.213',6633)
    topo = HypercubeTopo(n=3)
    net = Mininet(topo=topo, controller=None)
    net.addController(c)
    net.start()
    print "Testing network connectivity"

    for _ in range(2):
        net.pingAll()

    (first,last) = net.get('h1', 'h'+str(len(net.hosts)) )
    net.iperf((first, last))

    CLI(net)

    time.sleep(120)

    node1 = net.get('s1')
    node2 = net.get('s2')
    net.delLinkBetween(node1,node2)    

    for _ in range(2):
        net.pingAll()

    (first,last) = net.get('h1', 'h'+str(len(net.hosts)) )
    net.iperf((first, last))

    CLI(net)

    net.stop()

if __name__ == '__main__':
 # Tell mininet to print useful information
    setLogLevel('info')
    run()
