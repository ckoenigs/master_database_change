#!/bin/bash

#define path to neo4j bin
path_neo4j=$1

#path to project
path_to_project=$2

#download go
wget  -O ./go-basic.obo "purl.obolibrary.org/obo/go/go-basic.obo"

python3 ../EFO/transform_obo_to_csv_and_cypher_file.py go-basic.obo GO go $path_to_project > output_generate_integration_file.txt

now=$(date +"%F %T")
echo "Current time: $now"

echo integrate go into neo4j

$path_neo4j/cypher-shell -u neo4j -p test -f cypher.cypher > output_cypher_integration.txt 2>&1

sleep 120

$path_neo4j/neo4j restart


sleep 120