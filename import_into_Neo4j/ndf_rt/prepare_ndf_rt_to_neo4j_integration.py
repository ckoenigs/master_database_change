# -*- coding: utf-8 -*-
"""
Created on Fri Jul 14 10:34:41 2017

@author: Cassandra
"""

import xml.dom.minidom as dom

import datetime, csv
from collections import defaultdict


# dictionary of all entities with code as key and value is the entity
dict_entities = {}

# dictionary of all properties with code as key and the name as value
dict_properties = {}

# dictionary of all qualifiers with code as key and the name as value
dict_qualifiers = {}

# dictionary of all association with code as key and the name as value
dict_associations = {}

# dictionary with all ndf-rt relationships
dict_relationships = {}

# dictionary with entity as key and and value a list of dictionaries of the different nodes
dict_entity_to_nodes = {}

# dictionary entity to file
dict_entity_to_file = {}

# dictionary relationship to file name
dict_rela_to_file = {}

# dictionary filename to file
dict_rela_file_name_to_file={}

'''
add all information into a given dictionary
'''


def extract_and_add_info_into_dictionary(dictionary, terminology, element):
    element_list = terminology.getElementsByTagName(element)
    for combined_element in element_list:
        name = combined_element.getElementsByTagName('name')[0].childNodes[0].nodeValue
        code = combined_element.getElementsByTagName('code')[0].childNodes[0].nodeValue
        dictionary[code] = name


# cypher file to integrate nodes and relationships
cypher_file = open('cypher_file.cypher', 'w')

# cypher file to delte nodes without relationships
cypher_file_delete = open('cypher_file_delete.cypher', 'w')

# dictionary rela file name to code combination
dict_rela_to_list_of_code_tuples={}

def load_ndf_rt_xml_inferred_in():
    print(datetime.datetime.utcnow())
    tree = dom.parse("NDFRT_Public_2018.02.05_TDE.xml")
    print(datetime.datetime.utcnow())

    terminology = tree.documentElement

    # save all kindDef (Entities) in a dictionary with code and name
    extract_and_add_info_into_dictionary(dict_entities, terminology, 'kindDef')
    properties_of_node = ['code', "name", "id", "properties", "association"]
    for code, entity_name in dict_entities.items():
        file_name = 'results/'+entity_name + '_file.tsv'
        entity_file = open(file_name, 'w', encoding='utf-8')
        csv_writer = csv.writer(entity_file, delimiter='\t', quotechar='"', lineterminator='\n')
        csv_writer.writerow(properties_of_node)
        dict_entity_to_file[code] = csv_writer
        query = '''USING PERIODIC COMMIT 10000 LOAD CSV WITH HEADERS FROM "file:/home/cassandra/Dokumente/Project/master_database_change/import_into_Neo4j/ndf_rt/%s" AS line FIELDTERMINATOR '\\t' Create (n: NDF_RT_''' + entity_name + '{'
        print(query)
        print(file_name)
        query = query % (file_name)
        for propertie in properties_of_node:
            if not propertie in ['properties','association']:
                query += propertie + ':line.' + propertie + ','
            else:
                query += propertie + ':split(line.' + propertie + ',"|"),'
        query = query[:-1] + '});\n'
        cypher_file.write(query)
        #create index on code of all ndf-rt enities
        query='Create Constraint On (node:NDF_RT_' + entity_name+') Assert node.code Is Unique; \n'
        cypher_file.write(query)
        query='''Match (n: NDF_RT_'''+entity_name+''') Where not (n)-[]-() Delete n;\n '''
        cypher_file_delete.write(query)

    # save for all properties the code and name in a dictionary
    extract_and_add_info_into_dictionary(dict_properties, terminology, 'propertyDef')

    # save all qualifier in a dictionary with code and name
    extract_and_add_info_into_dictionary(dict_qualifiers, terminology, 'qualifierDef')

    # save all association in a dictionary
    extract_and_add_info_into_dictionary(dict_associations, terminology, 'associationDef')

    # save all association in a dictionary and generate the different cypher queries for the different relationships
    element_list = terminology.getElementsByTagName('roleDef')
    rela_info_list=['start_node','end_node']
    for combined_element in element_list:
        name = combined_element.getElementsByTagName('name')[0].childNodes[0].nodeValue
        name=name.split(' {')[0]
        code = combined_element.getElementsByTagName('code')[0].childNodes[0].nodeValue
        dict_relationships[code] = name

        # this part is for generating and adding the cypher queries
        start_node_code = combined_element.getElementsByTagName('domain')[0].childNodes[0].nodeValue
        end_node_code = combined_element.getElementsByTagName('range')[0].childNodes[0].nodeValue

        file_name ='results/'+ name + '_file.tsv'
        dict_rela_to_file[code] = file_name
        if file_name not in dict_rela_file_name_to_file:
            dict_rela_to_list_of_code_tuples[file_name]=[]
            entity_file = open(file_name, 'w', encoding='utf-8')
            csv_writer = csv.writer(entity_file, delimiter='\t', quotechar='"',lineterminator='\n')
            csv_writer.writerow(rela_info_list)
            dict_rela_file_name_to_file[file_name]=csv_writer
            query = '''USING PERIODIC COMMIT 10000 LOAD CSV WITH HEADERS FROM "file:/home/cassandra/Dokumente/Project/master_database_change/import_into_Neo4j/ndf_rt/%s" AS line FIELDTERMINATOR '\\t' Match (start: NDF_RT_''' + dict_entities[start_node_code] + '''{code:line.'''+ rela_info_list[0]+ '''}), (end: NDF_RT_''' + dict_entities[end_node_code] + '''{code:line.'''+rela_info_list[1]+'''}) Create (start)-[:%s]->(end);\n'''
            print(query)
            query=query% (file_name, name)

            cypher_file.write(query)

    # get all important concepts
    concepts = terminology.getElementsByTagName('conceptDef')
    for concept in concepts:
        # gete information about node
        entity_code=concept.getElementsByTagName('kind')[0].childNodes[0].nodeValue
        name = concept.getElementsByTagName('name')[0].childNodes[0].nodeValue
        code = concept.getElementsByTagName('code')[0].childNodes[0].nodeValue
        ndf_rt_id = concept.getElementsByTagName('id')[0].childNodes[0].nodeValue

        # go through all possible Role (Relationships) and add the to the different csv files
        definitionRoles = concept.getElementsByTagName('definingRoles')[0]
        if definitionRoles.hasChildNodes() == True:
            roles = definitionRoles.getElementsByTagName('role')
            for role in roles:
                rela_code=role.getElementsByTagName('name')[0].childNodes[0].nodeValue
                to_code=role.getElementsByTagName('value')[0].childNodes[0].nodeValue
                if (code,to_code) not in dict_rela_to_list_of_code_tuples[dict_rela_to_file[rela_code]]:
                    dict_rela_file_name_to_file[dict_rela_to_file[rela_code]].writerow([code,to_code])
                    dict_rela_to_list_of_code_tuples[dict_rela_to_file[rela_code]].append((code,to_code))

        # go through all properties of this drug and generate a list of string
        prop = concept.getElementsByTagName('properties')[0]
        properties = prop.getElementsByTagName('property')
        properties_list = []
        for proper in properties:
            name_property = proper.getElementsByTagName('name')[0].childNodes[0].nodeValue
            value = proper.getElementsByTagName('value')[0].childNodes[0].nodeValue
            value = value.replace('"', '\'')
            text = dict_properties[name_property] + ':' + value
            properties_list.append(text)

        properties_string='|'.join(properties_list)
        # properties_string=properties_string.encode("utf-8")

        # go through association of this drug and generate a list of string
        association_list = []
        if len(concept.getElementsByTagName('associations')) > 0:
            associat = concept.getElementsByTagName('associations')[0]
            associations = associat.getElementsByTagName('association')

            if len(associations) > 0:

                for association in associations:
                    name_association = association.getElementsByTagName('name')[0].childNodes[0].nodeValue
                    value = association.getElementsByTagName('value')[0].childNodes[0].nodeValue
                    text = dict_associations[name_association] + ':' + value
                    association_list.append(text)
        association_string='|'.join(association_list)

        dict_entity_to_file[entity_code].writerow([code, name, ndf_rt_id, properties_string, association_string])


def main():
    # start the function to load in the xml file and save the importen values in list and dictionaries
    print('#############################################################')
    print(datetime.datetime.utcnow())
    print('load in the xml data')
    load_ndf_rt_xml_inferred_in()


    print('#############################################################')
    print(datetime.datetime.utcnow())


if __name__ == "__main__":
    # execute only if run as a script
    main()