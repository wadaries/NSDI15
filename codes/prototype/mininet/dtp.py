"""2015-02-14 07:42:22.895739
$ sudo mn --custom ~/sdndb/dtp.py --topo mytopo --test pingall
$ sudo mn --custom ~/mininet/custom/topo-2sw-2host.py --topo mytopo --test pingall
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
        h8 = self.addHost('h8')
        h9 = self.addHost('h9')
        h10 = self.addHost('h10')

        s4 = self.addSwitch('s4')
        s5 = self.addSwitch('s5')
        s6 = self.addSwitch('s6')
        s7 = self.addSwitch('s7')

        self.addLink(h1,h2)
        self.addLink(h2,h1)
        self.addLink(h1,h3)
        self.addLink(h3,h1)
        self.addLink(h2,s4)
        self.addLink(s4,h2)
        self.addLink(h3,s4)
        self.addLink(s4,h3)
        self.addLink(h1,s5)
        self.addLink(s5,h1)
        self.addLink(h1,s6)
        self.addLink(s6,h1)
        self.addLink(h2,s6)
        self.addLink(s6,h2)
        self.addLink(s7,h2)
        self.addLink(h2,s7)
        self.addLink(h3,h8)
        self.addLink(h8,h3)
        self.addLink(h3,h9)
        self.addLink(h9,h3)
        self.addLink(s4,h9)
        self.addLink(h9,s4)
        self.addLink(s4,h10)
        self.addLink(h10,s4)

topos = { 'mytopo': ( lambda: MyTopo() ) }
    
