#!/bin/bash

#define path to neo4j bin
path_neo4j=$1

#path to project
path_to_project=$2

echo ndf-rt


now=$(date +"%F %T")
echo "Current time: $now"
echo disease

python3 map_NDF-RT_disease_final.py $path_to_project > output_map_ndf_rt_disease.txt


now=$(date +"%F %T")
echo "Current time: $now"

$path_neo4j/cypher-shell -u neo4j -p test -f disease/cypher.cypher > disease/output_cypher_integration_se.txt

sleep 180
$path_neo4j/neo4j restart
sleep 120



now=$(date +"%F %T")
echo "Current time: $now"
echo drugs

python3  map_NDF_RT_drug.py $path_to_project > output_map_ndf_rt_drugs.txt


now=$(date +"%F %T")
echo "Current time: $now"
echo integration of ndf-rt connection into hetionet

$path_neo4j/cypher-shell -u neo4j -p test -f drug/cypher.cypher > output_ndf_rt_drug_cypher.txt

sleep 180
$path_neo4j/neo4j restart
sleep 120



now=$(date +"%F %T")
echo "Current time: $now"
echo drugs-disease rela

python3  integrate_ndf_rt_drug_disease_rela.py $path_to_project > output_map_ndf_rt_rela.txt


now=$(date +"%F %T")
echo "Current time: $now"
echo integration of ndf-rt connection into hetionet

$path_neo4j/cypher-shell -u neo4j -p test -f relationships/cypher.cypher > output_ndf_rt_rela_cypher.txt

sleep 180
$path_neo4j/neo4j restart
sleep 120


now=$(date +"%F %T")
echo "Current time: $now"
echo ingredient

python3  mapping_ingredient_to_chemical.py $path_to_project > ingredient/output_map_ndf_rt.txt


now=$(date +"%F %T")
echo "Current time: $now"
echo integration of ndf-rt connection into hetionet

$path_neo4j/cypher-shell -u neo4j -p test -f ingredient/cypher.cypher > ingredient/output.txt

sleep 180
$path_neo4j/neo4j restart
sleep 120

now=$(date +"%F %T")
echo "Current time: $now"
echo pharmacologic class mapping

python3  mapping_mechanism_of_action_and_physiologic_effect.py $path_to_project > pharmacologicClass/output_map_ndf_rt.txt


now=$(date +"%F %T")
echo "Current time: $now"
echo integration of ndf-rt connection into hetionet

$path_neo4j/cypher-shell -u neo4j -p test -f pharmacologicClass/cypher.cypher > pharmacologicClass/output.txt

sleep 180
$path_neo4j/neo4j restart
sleep 120

now=$(date +"%F %T")
echo "Current time: $now"
echo pharmacologic class chemical rela

python3  integrate_rela_between_chemical_and_pharmacologicalClass.py $path_to_project > chemical_pharmacological/output_map_ndf_rt.txt


now=$(date +"%F %T")
echo "Current time: $now"
echo integration of ndf-rt connection into hetionet

$path_neo4j/cypher-shell -u neo4j -p test -f chemical_pharmacological/cypher.cypher 

sleep 180
$path_neo4j/neo4j restart
sleep 120