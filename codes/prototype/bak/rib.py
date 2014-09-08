import libRouteviewReplay
import libParsers

ISP_graph = igraph.Graph ()

sql_script = os.getcwd() + '/sql_files/' + "schema_new.sql"
username = "anduo"

rib_prefixes = os.getcwd() + '/rib_feeds/' + "rib20011204_prefixes.txt"
rib_peerIPs = os.getcwd() + '/rib_feeds/' + "rib20011204_nodes.txt"

ISP_nodes = os.getcwd() + '/ISP_topo/' + "1221_nodes.txt"
ISP_edges = os.getcwd() + '/ISP_topo/' + "1221_edges.txt"

global dbname
global rib_edges
global log

if __name__ == '__main__':

    global rib_edges
    global log
    global dbname

    size_list = []
    size = raw_input('Input RIB size (number of feeds): ')
    while (size != ''):
        size_list.append (int (size))
        size = raw_input('Input RIB size (number of feeds): ')

    for size in size_list:

        rib_edges = os.getcwd() + '/rib_feeds/' + "rib20011204_edges_" + str(size) + ".txt"
        os.system ("head -n " + str(size) + " rib20011204_edges.txt > " + rib_edges)

        dbname = "rib" + str (size)
        
        log = "rib" + str (size) + ".log"

        initialize (sql_script, username, dbname,
                    rib_edges, rib_prefixes, rib_peerIPs,
                    ISP_nodes, ISP_edges,
                    log)
