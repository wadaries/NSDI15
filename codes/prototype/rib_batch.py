import libUtility
import libRouteviewReplay
import libParsers
import subprocess

ISP_graph = igraph.Graph ()

def sort_as ():

    asfile = open (os.getcwd() + '/ISP_topo/' + "stat", "r")
    asl = []
    for af in asfile:
        if af[0] != "#":
            items = [int (i) for i in af.split ()]
            asl.append ([items[0], items[1], items[2]])

    asl.sort(key = lambda row: row[2])
    return asl

if __name__ == '__main__':

    sql_script = os.getcwd() + '/sql_files/' + "schema_new.sql"
    username = "anduo"

    # Set RIB parameters
    rib_prefixes = os.getcwd() + '/rib_feeds/' + "rib20011204_prefixes.txt"
    rib_peerIPs = os.getcwd() + '/rib_feeds/' + "rib20011204_nodes.txt"
    rib_feeds_all = os.getcwd() + '/rib20011204_edges.txt'

    max_num = subprocess.check_output(["wc", "-l", rib_feeds_all])
    size = raw_input('Input RIB size: d for default number (all), or the number of feeds: ')
    if size == 'd':
        rib_edges = rib_feeds_all
    elif (int(size) >= 0) and (int(size) < max_num):
        rib_edges = os.getcwd() + '/rib_feeds/rib20011204_edges_' + str (size) + '.txt'
        os.system ("head -n " + str(size) + " rib20011204_edges.txt > " + rib_edges)

    # Set AS parameters    
    asl = sort_as ()

    asls = []
    as_n = int (raw_input ('Input the x-th largest AS: '))
    while (as_n != 'e'):
        if (int(as_n) >= 0) and (int(as_n) < len (asl)):
            asls.append (asl[int(as_n)][0])
        as_n = raw_input ('Input the x-th largest AS: (enter e to exit)')

    # initialize    
    for AS in asls:
        ISP_nodes = os.getcwd() + '/ISP_topo/' + str(AS) + "_nodes.txt"
        ISP_edges = os.getcwd() + '/ISP_topo/' + str(AS) + "_edges.txt"
        log = "as" + str(AS) + "rib" + str (size) + ".log"
        dbname = "as" + str(AS) + "rib" + str (size)

        initialize (sql_script, username, dbname,
                    rib_edges, rib_prefixes, rib_peerIPs,
                    ISP_nodes, ISP_edges,
                    log)

    # flag = int(raw_input('Select: (1) Input RIB size, (2) Select ASN, (3) Select AS for initialization, (4) Exit:  '))

    # for each ISP topology (indexed by AS number), (1) create
    # daatbase and (2) initialize with RIB
    # if flag == 1:

    # elif flag == 2:

    #     print asl

    # # selected = [asl[0], asl[4], asl[9]]
    # # return selected

    # else:
    #     print "wrong"
    #     print "flag is " + str(flag)
    

    # gather AS numbers
    # path = os.getcwd() + '/ISP_topo/'
    # ASN = []
    # for filename in glob.glob(os.path.join(path, '*_nodes.txt')):
    #     ASN.append (filename.split ('/')[-1].split ('_')[0])
