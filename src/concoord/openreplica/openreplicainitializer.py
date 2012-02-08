'''
@author: Deniz Altinbuken, Emin Gun Sirer
@note: Initializes an OpenReplica instance
@date: August 1, 2011
@copyright: See COPYING.txt
'''
from optparse import OptionParser
from time import sleep,time
import os, sys, time, shutil
import ast, _ast
import subprocess
from concoord.safetychecker import *
from concoord.proxygenerator import *
from concoord.serversideproxyast import *
from plmanager import *
from openreplicacoordobjproxy import *

parser = OptionParser(usage="usage: %prog -s subdomain -f objectfilepath -c classname -r replicas -a acceptors -n nameservers")
parser.add_option("-s", "--subdomain", action="store", dest="subdomain", help="name for the subdomain to reach openreplica")
parser.add_option("-f", "--objectfilepath", action="store", dest="objectfilepath", help="client object file path")
parser.add_option("-c", "--classname", action="store", dest="classname", help="main class name")
parser.add_option("-r", "--replicas", action="store", dest="replicanum", default=1, help="number of replicas")
parser.add_option("-a", "--acceptors", action="store", dest="acceptornum", default=1, help="number of acceptor")
parser.add_option("-n", "--nameservers", action="store", dest="nameservernum", default=1, help="number of nameservers")
(options, args) = parser.parse_args()

def check_object(clientcode):
    print "Checking object safety"
    astnode = compile(clientcode,"<string>","exec",_ast.PyCF_ONLY_AST)
    v = SafetyVisitor()
    v.visit(astnode)
    return v.safe

# checks if a PL node is suitable for running a nameserver
def check_planetlab_dnsport(plconn, node):
    print "Uploading DNS tester to ", node
    pathtodnstester = os.path.abspath("testdnsport.py")
    plconn.uploadone(node, pathtodnstester)
    print "Trying to bind to DNS port"
    rtv, output = plconn.executecommandone(node, "sudo -A /home/cornell_openreplica/python2.7/bin/python2.7 testdnsport.py")
    if rtv:
        print "DNS Port available on %s" % node
    else:
        print "DNS Port not available on %s" % node
        plconn.executecommandone(node, "rm testdnsport.py")
    return rtv,output

def check_planetlab_pythonversion(plconn, node):
    print "Checking Python version on ", node
    command = '/home/cornell_openreplica/python2.7/bin/python2.7 --version'
    rtv, output = plconn.executecommandone(node, command)
    if rtv:
        for out in output:
            if string.find(out, 'Python 2.7') >= 0:
                print "Python version acceptable!"
                return True,output
    print '\n'.join(output)
    return False,output

def start_nodes(subdomain, clientobjectfilepath, classname, configuration):
    # locate the right number of suitable PlanetLab nodes
    clientobjectfilename = os.path.basename(clientobjectfilepath)
    numreplicas, numacceptors, numnameservers = configuration
    if numreplicas < 1 or numacceptors < 1 or numnameservers < 1:
        print "Invalid configuration:"
        print "The configuration requires at least 1 Replica, 1 Acceptor and 1 Nameserver"
        os._exit()
    bootstrap = PLConnection(1, [check_planetlab_pythonversion])
    nameservers = PLConnection(numnameservers, [check_planetlab_dnsport, check_planetlab_pythonversion])
    replicas = PLConnection(numreplicas-1, [check_planetlab_pythonversion])
    acceptors = PLConnection(numacceptors, [check_planetlab_pythonversion])
    allnodes = PLConnection(nodes=nameservers.getHosts() + replicas.getHosts() + acceptors.getHosts() + bootstrap.getHosts())
    print "=== Picked Nodes ==="
    for node in allnodes.getHosts():
        print node
    processnames = []
    nameservernames = []
    ## Fix the server object
    print "Fixing object file for use on the server side.."
    fixedfile = editproxyfile(clientobjectfilepath, classname)
    print "Uploading object file to replicas.."
    allnodes.uploadall(fixedfile.name, "concoord/"+clientobjectfilename)
    print "--> Setting up the environment..."
    # BOOTSTRAP
    print "--- Bootstrap Replica ---"
    port = random.randint(14000, 15000)
    p = bootstrap.executecommandone(bootstrap.getHosts()[0], "nohup /home/cornell_openreplica/python2.7/bin/python2.7 concoord/replica.py -a %s -p %d -f %s -c %s" % (bootstrap.getHosts()[0], port, clientobjectfilename, classname), False)
    while terminated(p):
        port = random.randint(14000, 15000)
        p = bootstrap.executecommandone(bootstrap.getHosts()[0], "nohup /home/cornell_openreplica/python2.7/bin/python2.7 concoord/replica.py -a %s -p %d -f %s -c %s" % (bootstrap.getHosts()[0], port, clientobjectfilename, classname), False)
    bootstrapname = bootstrap.getHosts()[0]+':'+str(port)
    processnames.append(bootstrapname)
    print bootstrapname
    # ACCEPTORS
    print "--- Acceptors ---"
    for acceptor in acceptors.getHosts():
        port = random.randint(14000, 15000)
        p = acceptors.executecommandone(acceptor, "nohup /home/cornell_openreplica/python2.7/bin/python2.7 concoord/acceptor.py -a %s -p %d -f %s -b %s" % (acceptor, port, clientobjectfilename, bootstrapname), False)
        while terminated(p):
            port = random.randint(14000, 15000)
            p = acceptors.executecommandone(acceptor, "nohup /home/cornell_openreplica/python2.7/bin/python2.7 concoord/acceptor.py -a %s -p %d -f %s -b %s" % (acceptor, port, clientobjectfilename, bootstrapname), False)
        acceptorname = acceptor+':'+str(port)
        processnames.append(acceptorname)
        print acceptorname
    # REPLICAS
    if numreplicas-1 > 0:
        print "--- Replicas ---"
    for replica in replicas.getHosts():
        port = random.randint(14000, 15000)
        p = replicas.executecommandone(replica, "nohup /home/cornell_openreplica/python2.7/bin/python2.7 concoord/replica.py -a %s -p %d -f %s -c %s -b %s" % (replica, port, clientobjectfilename, classname, bootstrapname), False)
        while terminated(p):
            port = random.randint(14000, 15000)
            p = replicas.executecommandone(replica, "nohup /home/cornell_openreplica/python2.7/bin/python2.7 concoord/replica.py -a %s -p %d -f %s -c %s -b %s" % (replica, port, clientobjectfilename, classname, bootstrapname), False)
        replicaname = replica+':'+str(port)
        processnames.append(replicaname)
        print replicaname
    # NAMESERVERS
    print "--- Nameservers ---"
    for nameserver in nameservers.getHosts():
        port = random.randint(14000, 15000)
        p = nameservers.executecommandone(nameserver, "sudo -A nohup /home/cornell_openreplica/python2.7/bin/python2.7 concoord/nameserver.py -n %s -a %s -p %d -f %s -c %s -b %s" % (subdomain+'.openreplica.org', nameserver, port, clientobjectfilename, classname, bootstrapname), False)
        while terminated(p):
            port = random.randint(14000, 15000)
            p = nameservers.executecommandone(nameserver, "sudo -A nohup /home/cornell_openreplica/python2.7/bin/python2.7 concoord/nameserver.py -n %s -a %s -p %d -f %s -c %s -b %s" % (subdomain+'.openreplica.org', nameserver, port, clientobjectfilename, classname, bootstrapname), False)
        nameservername = nameserver+':'+str(port)
        processnames.append(nameservername)
        nameservernames.append(nameservername)
        print nameservername
    print "All clear!"
    ## add the nameserver nodes to open replica coordinator object
    openreplicacoordobj = OpenReplicaCoordProxy('128.84.154.110:6668')
    print "Adding Nameserver nodes to OpenReplica Coordination Object:"
    for node in nameservernames:
        print "- ", node
        openreplicacoordobj.addnodetosubdomain(subdomain, node)
    return bootstrapname

def terminated(p):
    i = 5
    done = p.poll() is not None
    while not done and i>0: # Not terminated yet
        sleep(1)
        i -= 1
        done = p.poll() is not None
    return done

def main():
    try:
        with open(options.objectfilepath, 'rU') as fd:
            clientcode = fd.read()
        # Check safety
        if not check_object(clientcode):
            print "Object is not safe for us to execute."
            os._exit(1)
        # Start Nodes
        print "Connecting to Planet Lab"
        configuration = (int(options.replicanum), int(options.acceptornum), int(options.nameservernum))
        start_nodes(options.subdomain, options.objectfilepath, options.classname, configuration)
        # Create Proxy
        print "Creating proxy..."
        clientproxycode = createclientproxy(clientcode, options.classname, None)
        clientproxycode = clientproxycode.replace('\n\n\n', '\n\n')
        print "Proxy Code:"
        print clientproxycode
    except Exception as e:
        print "Error: ", e
    
if __name__=='__main__':
    main()