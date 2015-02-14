import sys
import os
sys.path.append (os.getcwd ())
sys.path.append('/usr/local/lib/python2.7/site-packages/')

import pxssh
import pexpect
# import Crypto
# import Crypto.Util
# import Crypto.Cipher
# import paramiko

# from pexpect import *
# remote_dir = "mininet@mininet-vm"
# local_dir = '/Users/anduo/Documents/NSDI15/codes/prototype/mininet_topo.py'
# print('scp %s %s' % (remote_dir, local_dir))

from pexpect import *
run ('scp /Users/anduo/Documents/NSDI15/codes/prototype/mininet_topo.py mininet@mininet-vm:~/sdndb', events={'(?i)password': "mininet"})

filename = '/tmp/mininet_topo_new.py'
run ('scp ' + filename + ' mininet@mininet-vm:/home/mininet/sdndb', events={'(?i)password': "mininet"})

# child = spawn('scp /Users/anduo/Documents/NSDI15/codes/prototype/mininet_topo.py mininet@mininet-vm:.')
# child.expect ('(?i)password')
# child.sendline ('mininet')

# child = pexpect.spawn('scp %s %s' % (remote_dir, local_dir))
# # doesn't work, why???
# # child.expect("mininet@mininet-vm's password:")
# child.sendline("mininet")
# child.expect(pexpect.EOF, timeout=10)

mn = 'mininet-vm'
mnu = 'mininet'
mnp = 'mininet'

s = pxssh.pxssh()
if not s.login (mn, mnu, mnp):
    print "SSH session failed on login."
    print str(s)
else:
    print "SSH session login successful"
    s.sendline ('uptime; ls')
    s.prompt()         # match the prompt
    print s.before     # print everything before the prompt.
    # s.sendline ('sudo mn')
    # s.prompt()         # match the prompt
    # print s.before     # print everything before the prompt.
    # s.logout()

s.sendline ('sudo ovs-ofctl dump-flows s1')    

s.sendline('nodes')
s.prompt()         
print s.before     

'sudo ovs-ofctl del-flows s1 in_port=1'
'sudo ovs-ofctl del-flows s1 in_port=2'

s.sendline ('sudo ovs-ofctl add-flow s1 in_port=1,actions=output:2')    
s.sendline ('sudo ovs-ofctl add-flow s1 in_port=2,actions=output:1')
s.prompt()         
print s.before     

s.sendline('pingall')
s.prompt()         
print s.before     

s2 = pxssh.pxssh ()
s2.login (mn, mnu, mnp)
s2.sendline ('uptime')
s2.prompt ()
print s2.before

s.logout ()
s.prompt()         
print s.before     

s2.logout ()
s2.prompt ()
print s2.before
