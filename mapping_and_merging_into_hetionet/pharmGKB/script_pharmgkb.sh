#!/usr/bin/env bash

#define path to neo4j bin
path_neo4j=$1

#path to project
path_to_project=$2

now=$(date +"%F %T")
echo "Current time: $now"
echo 'map pahrmgkb gene'

python3 map_gene.py $path_to_project > gene/output.txt


now=$(date +"%F %T")
echo "Current time: $now"
echo 'map chemical'

python3 map_drug_chemical.py $path_to_project > chemical/output.txt

now=$(date +"%F %T")
echo "Current time: $now"
echo 'map variant and haplotypes'

python3 map_haplotype_and_variant.py $path_to_project > variant/output.txt

now=$(date +"%F %T")
echo "Current time: $now"
echo 'map phenotypes'

python3 map_phenotype.py $path_to_project > disease/output.txt


now=$(date +"%F %T")
echo "Current time: $now"

$path_neo4j/cypher-shell -u neo4j -p test -f output/cypher.cypher 

sleep 180
$path_neo4j/neo4j restart
sleep 120
