# -*- coding: utf-8 -*-
"""
Created on Wed Apr 18 12:41:20 2018

@author: ckoenigs
"""

from py2neo import Graph
import datetime
import csv
import sys

sys.path.append("../..")
import create_connection_to_databases

'''
create a connection with neo4j
'''


def create_connection_with_neo4j():
    # set up authentication parameters and connection
    global graph_database
    graph_database = create_connection_to_databases.database_connection_neo4j()


# dictionary with hetionet failedReaction with identifier as key and value the name
dict_compound_hetionet_node_hetionet = {}

'''
load in all Compounds from hetionet in a dictionary
'''


def load_hetionet_compound_hetionet_node_in(csv_file, dict_compound_hetionet_node_hetionet,
                                                  new_relationship,
                                                  node_reactome_label, rela_equal_name, node_hetionet_label, direction1, direction2):
    query = '''MATCH (p:Chemical)-[:equal_to_reactome_drug]-(r:ReferenceTherapeutic_reactome)<-[:referenceEntity]-(z:Drug_reactome)%s[v:%s]%s(n:%s)-[:%s]-(b:%s) RETURN p.identifier, b.identifier, v.order, v.stoichiometry, z.displayName'''
    query = query % (direction1, new_relationship, direction2, node_reactome_label, rela_equal_name, node_hetionet_label)
    print(query)
    results = graph_database.run(query)
    # for id1, id2, order, stoichiometry, in results:
    for compound_id, node_id, order, stoichiometry, displayName, in results:
        if (compound_id, node_id) in dict_compound_hetionet_node_hetionet:
            print(compound_id, node_id)
            displayName = displayName.split("[")
            compartment = displayName[1]
            compartment = compartment.replace("]", "")
            print(compartment)
            dict_compound_hetionet_node_hetionet[(compound_id, node_id)] = [stoichiometry, order, compartment]
            #Afatinib [cytosol] --> cytosol
            #sys.exit("Doppelte Drug-Disease Kombination")
            continue
        dict_compound_hetionet_node_hetionet[(compound_id, node_id)] = [stoichiometry, order]
        csv_file.writerow([compound_id, node_id, order, stoichiometry])
    print('number of reaction-'+node_reactome_label+' relationships in hetionet:' + str(
        len(dict_compound_hetionet_node_hetionet)))


'''
generate new relationships between Compound of hetionet and Drug of hetionet nodes that mapped to reactome
'''


def create_cypher_file(directory, file_path, node_label, rela_name, direction1, direction2):
    query = '''Using Periodic Commit 10000 LOAD CSV  WITH HEADERS FROM "file:%smaster_database_change/mapping_and_merging_into_hetionet/reactome/%s" As line FIELDTERMINATOR "\\t" MATCH (d:Chemical{identifier:line.id_hetionet_Compound}),(c:%s{identifier:line.id_hetionet_node}) CREATE (d)%s[: %s{order:line.order, stoichiometry:line.stoichiometry, resource: ['Reactome'], reactome: "yes"}]%s(c);\n'''
    query = query % (path_of_directory, file_path, node_label, direction1, rela_name, direction2)
    cypher_file.write(query)


def check_relationships_and_generate_file(new_relationship, node_reactome_label, rela_equal_name, node_hetionet_label,
                                          directory, rela_name, direction1, direction2):
    print(
        '###########################################################################################################################')

    print(datetime.datetime.utcnow())
    print('Load all relationships from hetionet_Compound and hetionet_nodes into a dictionary')
    # file for mapped or not mapped identifier
    file_name= directory + '/mapped_Compound_to_'+node_reactome_label+'_'+rela_name+'.tsv'

    file_mapped_drug_to_node = open(file_name,'w', encoding="utf-8")
    csv_mapped = csv.writer(file_mapped_drug_to_node, delimiter='\t', lineterminator='\n')
    csv_mapped.writerow(['id_hetionet_Compound', 'id_hetionet_node', 'order', 'stoichiometry'])

    dict_compound_node = {}

    load_hetionet_compound_hetionet_node_in(csv_mapped, dict_compound_node, new_relationship,
                                                  node_reactome_label,
                                                  rela_equal_name, node_hetionet_label, direction1, direction2)

    print(
        '###########################################################################################################################')

    print(datetime.datetime.utcnow())

    print('Integrate new relationships and connect them ')

    create_cypher_file(directory, file_name, node_hetionet_label, rela_name, direction1, direction2)


def main():
    global path_of_directory
    if len(sys.argv) > 1:
        path_of_directory = sys.argv[1]
    else:
        sys.exit('need a path reactome reaction')

    global cypher_file
    print(datetime.datetime.utcnow())
    print('Generate connection with neo4j and mysql')

    create_connection_with_neo4j()

    # 0: old relationship;           1: name of node in Reactome;        2: relationship equal to Hetionet-node
    # 3: name of node in Hetionet;   4: name of directory                5: name of new relationship
    list_of_combinations = [
        ['input', 'Reaction_reactome', 'equal_to_reactome_reaction', 'Reaction',
         'INPUT_RiD', '<-', '-'],
        ['input', 'FailedReaction_reactome', 'equal_to_reactome_failedreaction', 'FailedReaction',
         'INPUT_FiD', '<-', '-'],
        ['input', 'BlackBoxEvent_reactome', 'equal_to_reactome_blackBoxEvent', 'BlackBoxEvent',
         'INPUT_BiD', '<-', '-'],
        ['output', 'Reaction_reactome', 'equal_to_reactome_reaction', 'Reaction',
         'OUTPUT_RoD', '<-', '-']
    ]

    directory = 'DrugEdges'
    cypher_file = open('output/cypher_drug_edge.cypher', 'a', encoding="utf-8")

    for list_element in list_of_combinations:
        new_relationship = list_element[0]
        node_reactome_label = list_element[1]
        rela_equal_name = list_element[2]
        node_hetionet_label = list_element[3]
        rela_name = list_element[4]
        direction1 = list_element[5]
        direction2 = list_element[6]
        check_relationships_and_generate_file(new_relationship, node_reactome_label, rela_equal_name,
                                              node_hetionet_label, directory,
                                              rela_name, direction1, direction2)
    cypher_file.close()

    print(
        '###########################################################################################################################')

    print(datetime.datetime.utcnow())


if __name__ == "__main__":
    # execute only if run as a script
    main()