#!/bin/bash

#define path to neo4j bin
path_neo4j=$1

#path to project
path_to_project=$2

echo aeolus outcome mapping
python3 map_aeolus_outcome_final.py $path_to_project > output/output_map_aeolus_outcome.txt



echo Aeolus drugs

now=$(date +"%F %T")
echo "Current time: $now"


python3  map_aeolus_drugs_final.py $path_to_project > output/output_aeolus_drug.txt


now=$(date +"%F %T")
echo "Current time: $now"
echo integrate map drug and outcome

$path_neo4j/cypher-shell -u neo4j -p test -f output/cypher.cypher > output/output_cypher_integration_drug.txt

sleep 120
$path_neo4j/neo4j restart
sleep 120

echo relationships
python3  integrate_aeolus_relationships.py $path_to_project > output/output_aeolus_rela.txt


now=$(date +"%F %T")
echo "Current time: $now"

$path_neo4j/cypher-shell -u neo4j -p test -f output/cypher_rela.cypher > output/output_cypher_integration_rela.txt

sleep 120
$path_neo4j/neo4j restart
sleep 120