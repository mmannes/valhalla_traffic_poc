import sys
import csv
import os
import subprocess

'''
# Update routing tiles with traffic information
# Create hierarchy of directories for traffic tiles with the same structure as the graph tiles
RUN cd /valhalla_tiles; mkdir traffic; cd valhalla_tiles; find . -type d -exec mkdir -p -- ../traffic/{} \;

# Generate osm ways to valhalla edges mapping:
RUN cd valhalla_tiles; valhalla_ways_to_edges --config valhalla.json
# ^ This generates a file with mappings at valhalla_tiles/way_edges.txt. The warning about traffic can be safely ignored.

# In order to find the osm id of a way, go to osm editor, edit, click on road, view on openstreetmap.org, check URL
# Let's update the traffic for openstreetmap.org/way/257559973
# Generate a csv with speeds for all edges
COPY update_traffic.py valhalla_tiles/traffic/update_traffic.py
RUN cd /valhalla_tiles/traffic; python3 update_traffic.py 114749206 /valhalla_tiles/valhalla_tiles/way_edges.txt

# Move the csv file to the expected location in the tile hierarchy
# All valhalla edges for this osm way id have the same tile id, so just get the first one from the mapping
RUN cd /valhalla_tiles/traffic; \
    edge_id=`grep 114749206 /valhalla_tiles/valhalla_tiles/way_edges.txt | cut -d ',' -f3`; \
    mv traffic.csv `valhalla_traffic_demo_utils --get-traffic-dir $edge_id`

# Add traffic information to the routing tiles
RUN cd /valhalla_tiles; valhalla_add_predicted_traffic -t traffic --config valhalla.json
'''

FREE_FLOW_SPEED = 50
CONSTRAINED_FLOW_SPEED = 40
PREDICTED_SPEED = 6 # Simulate congestions in predicted traffic


if len(sys.argv) != 2:
    print(f"Usage: {sys.argv[0]} <way_edges_path>")
    sys.exit(1)

way_edges_path = sys.argv[1]

mapping = ""

osm_way_ids = [
    114749206, # joão picolli
    289469476, # joão picolli
    1060382078,# dona francisca 
    1060382109,# dona francisca
    1060382108,# dona francisca
    1060382107,# dona francisca
    1060382106,# dona francisca
    1060382105,# dona francisca
    1060382104,# dona francisca
    1060382103,# dona francisca
    1060382101,# dona francisca
    1060382100,# dona francisca
    1060382099,# dona francisca
    1060382098,# dona francisca
    1060382097,# dona francisca
    480072828, # dona francisca
    1060382079,# dona francisca
    1060382080,# dona francisca

    # cidade universitária, ilha do governador, rio de janeiro-rj
    # ff~pj@tccnqAvIgHtDkDbEoEjD_E`LwMpAy@`Ao@bAcAr@w@b@u@dAcC^kAb@aBVkBNgCDwD?a@|@eCvAgCpBuB|x@cg@bDsBhi@g^te@k[zfAws@fLqIlCgAp@WlAa@bAOhAOfA?lAR|@p@fAjAxGrLxAbAbBf@|D|HrTx_@r`@xu@jK|LhDfCbFxCxFbBpGpAhHb@pG?hFQpFo@xMcCxZoTh^wV~AeA`JuFfXqPj[ySpvAo~@ROr@e@fq@mc@h_@qVri@}]tKeHpC~@~At@jA`Az@`AbQ`ZpLrSbf@f~@`[jl@|J`S|@tAhA`AtAd@tANvAArAa@hcAwr@ndA_o@xS_NrQaMv^_VlI_Gza@{Y
    297286290,
    794526575,
    462223375,
    462223375,
    462223375,
    25475931,
    25475931,
    734011311,
    734011311,
    25473053,
    25473053,
    25473053,
    25473053,
    25473053,
    25473053,
    799463836,
    972948130,
    785228934,
    734011310,
    952037577,
    952037577,
    952071914,
    952071914,
    952071914,
    25464903,
    25464903,
    25464903,
    25464903,
    1342216224,
    25464827,
    25464827,
    25464827,
    1342231971,
    1342231971,
    91658324,
    91658324,
    25464828,
    25464824,
    25464824,
    25464824,
    25464824,
]

qty_osm_way_ids = len(osm_way_ids)

osm_ways_with_valhalla_edges = {}
qty_osm_ways_with_valhalla_edges = 0;

for line in open(way_edges_path):
    for osm_way_id in osm_way_ids:
        if str(osm_way_id) in line:
            mapping = line.strip()
            # First get its mapping to edge ids from ways_edges.txt
            # Format is <osm_way_id>,[<direction: 0 | 1>, <valhalla_edge_id>]. An OSM way can be mapped to multiple valhalla edges, like in this case.
            # We are interested in the valhalla edge ids
            edges = mapping.split(",")[1:]
            edge_ids = [edges[i] for i in range(len(edges)) if i % 2 == 1]
            osm_ways_with_valhalla_edges[osm_way_id] = edge_ids
            qty_osm_ways_with_valhalla_edges += 1

            # Create the traffic.csv file. Format is:
            # edge_id, free flow speed (night), constrained flow speed (day), predicted traffic speeds.
            traffic_encoded_values = subprocess.run(['valhalla_traffic_demo_utils', '--generate-predicted-traffic', str(PREDICTED_SPEED)], stdout=subprocess.PIPE).stdout.decode('utf-8').strip()

            # TODO: instead of writting traffic.csv inside current directory, create it inside its final destination with the right tile ID

            for edge_id in edge_ids:
                csv_destination = subprocess.run(['valhalla_traffic_demo_utils', '--get-traffic-dir', str(edge_id)], stdout=subprocess.PIPE).stdout.decode('utf-8').strip()
                print(f"Preparing to create ./{csv_destination} edge_id {edge_id}...");

                with open ("./" + csv_destination, "a", newline='') as csvfile:
                    csv_writer = csv.writer(csvfile, delimiter=',', lineterminator='\n')
                    tile_id = subprocess.run(['valhalla_traffic_demo_utils', '--get-tile-id', edge_id], stdout=subprocess.PIPE).stdout.decode('utf-8').strip()
                    csv_writer.writerow([tile_id, FREE_FLOW_SPEED, CONSTRAINED_FLOW_SPEED, traffic_encoded_values])
                    print(f"Wrote tile_id={tile_id}, FREE_FLOW_SPEED={FREE_FLOW_SPEED}, CONSTRAINED_FLOW_SPEED={CONSTRAINED_FLOW_SPEED}, traffic_encoded_values={traffic_encoded_values} to ./{csv_destination}");

    if qty_osm_way_ids == qty_osm_ways_with_valhalla_edges:
        print(f"Stopping reading way_edges because all of the {qty_osm_way_ids} have been read. ")
        break

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
print(subprocess.run(['valhalla_add_predicted_traffic', '-t', 'traffic', '--config', 'valhalla.json'], cwd=parent_dir, stdout=subprocess.PIPE).stdout.decode('utf-8').strip())

