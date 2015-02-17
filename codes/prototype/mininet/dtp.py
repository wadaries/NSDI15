"""2015-02-17 12:56:59.606513
$ sudo mn --custom ~/sdndb/dtp.py --topo mytopo --test pingall
$ sudo mn --custom ~/sdndb/dtp.py --topo mytopo --mac --switch ovsk --controller remote
"""

from mininet.topo import Topo

class MyTopo( Topo ):
    "Simple topology example."

    def __init__( self ):
        "Create custom topo."

        # Initialize topology
        Topo.__init__( self )
    
        h1 = self.addHost('h1')
        h2 = self.addHost('h2')
        h3 = self.addHost('h3')

        s4 = self.addSwitch('s4')
        s5 = self.addSwitch('s5')
        s6 = self.addSwitch('s6')

        self.addLink(h1,s4)
        self.addLink(h2,s5)
        self.addLink(h3,s6)
        self.addLink(s4,s5)
        self.addLink(s5,s6)
        self.addLink(s6,s4)

topos = { 'mytopo': ( lambda: MyTopo() ) }
    
