from mininet.topo import Topo
from mininet.net import Mininet
from mininet.log import setLogLevel
from mininet.util import dumpNodeConnections

class TorusTopo( Topo ):
    """2-D Torus topology
       WARNING: this topology has LOOPS and WILL NOT WORK
       with the default controller or any Ethernet bridge
       without STP turned on! It can be used with STP, e.g.:
       # mn --topo torus,3,3 --switch lxbr,stp=1 --test pingall"""

    def __init__(self, x=3, y=3):
        if x < 3 or y < 3:
            raise Exception( 'Please use 3x3 or greater for compatibility '
                             'with 2.1' )
        hosts, switches, dpid = {}, {}, 0
        # Create and wire interior
        for i in range( 0, x ):
            for j in range( 0, y ):
                loc = '%dx%d' % ( i + 1, j + 1 )
                # dpid cannot be zero for OVS
                dpid = ( i + 1 ) * 256 + ( j + 1 )
                switch = switches[ i, j ] = self.addSwitch(
                    's' + loc, dpid='%016x' % dpid )
                host = hosts[ i, j ] = self.addHost( 'h' + loc )
                self.addLink( host, switch )



        # Connect switches
        for i in range( 0, x ):
            for j in range( 0, y ):
                sw1 = switches[ i, j ]
                sw2 = switches[ i, ( j + 1 ) % y ]
                sw3 = switches[ ( i + 1 ) % x, j ]
                self.addLink( sw1, sw2 )
                self.addLink( sw1, sw3 )


topos = { 'torus': ( lambda x,y : TorusTopo(x,y) ) }



def simpleTest():   
    "Create and test a simple network"
    topo = TorusTopo(x=4,y=4)
    net = Mininet(topo)
    net.start()
    print "Dumping host connections"
    dumpNodeConnections(net.hosts)
    print "Testing network connectivity"
    net.pingAll()
    net.stop()

if __name__ == '__main__':
 # Tell mininet to print useful information
    setLogLevel('info')
    simpleTest()