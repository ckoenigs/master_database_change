# -*- coding: utf-8 -*-
"""
Created on Mon Jan 15 12:49:17 2018

@author: Cassandra
"""
from py2neo import Graph, authenticate
import datetime
import sys

# dictionary for every drug with all information about this:name, inchikey, inchi, food interaction, alternative ids
dict_drug_info = {}

# dictionary for every drug interaction: with def as value
dict_drug_interaction_info = {}

'''
This takes all information from Drugbank and sort them in the different dictionaries 
0: drugbank_id	
1: alternative drugbank ids
2: name	
3: type	
4: groups	
5: atc_codes	
6: categories	
7: inchikey	
8: inchi	
9: inchikeys	
10: synonyms	
11:unii	
12:uniis	
13:external_identifiers	
14:extra_names	
15:brands	
16:molecular_forula	
17:molecular_formular_experimental	
18:gene_sequence	
19:amino_acid_sequence	
20:sequence	
21:drug_interaction	
22:drug_interaction_description	
23:food_interaction	
24:description
'''


def get_drugbank_information():
    i = 0
    f = open('data/drugbank_with_infos_and_interactions_alternative_ids.tsv', 'r')
    next(f)
    for line in f:
        # print(line)
        splitted = line.split('\t')
        drugbank_id = splitted[0]
        alternative_ids = splitted[1].split('|') if splitted[1] != '' else []
        alternative_ids.remove(drugbank_id)
        alternative_ids = '|'.join(alternative_ids)
        name = splitted[2]
        inchikey = splitted[7]
        inchi = splitted[8]
        drug_interaction = splitted[21]
        drug_interaction_describtion = splitted[22]

        food_interaction = splitted[23].replace('"', "'")
        # print(drugbank_id)
        # print(food_interaction)
        dict_drug_info[drugbank_id] = [name, inchikey, inchi, food_interaction, alternative_ids]

        counter = 0
        splitted_definition = drug_interaction_describtion.split('|')
        for drug in drug_interaction.split('|'):
            # it is enough to check on direction, because if it is already in the dictionary then this drug must be on position 2
            if ((drug, drugbank_id) not in dict_drug_interaction_info):
                dict_drug_interaction_info[(drugbank_id, drug)] = splitted_definition[counter]
            counter += 1
        # if i==10:
        #     break
        i += 1


'''
Generate cypher file for drugbank information
'''


def generate_cypher_file():
    i = 1
    # number of queries for a commit block
    constrain_number = 20000

    # number of quereies in a file
    creation_max_in_file = 1000000

    f = open('DrugBank_database_' + str(i) + '.cypher', 'w')
    f.write('begin \n')
    i += 1

    #    h=open('Sider_update_edges.cypher','w',encoding="utf-8")
    #    h.write('begin \n')

    # first add all queries with sider drugs
    counter_create = 0
    print('drug Create')
    print (datetime.datetime.utcnow())
    for identifier, info_list in dict_drug_info.items():
        url = 'http://www.drugbank.ca/drugs/' + identifier
        creat_text = 'Create (:DrugBankdrug{id: "%s" , name: "%s", inchikey: "%s", inchi: "%s",  food_interaction: "%s", url: "%s", license:"CC BY-NC 4.0", alternative_ids: "%s"} ); \n' % (
            identifier, info_list[0], info_list[1], info_list[2], info_list[3], url, info_list[4])
        # print(creat_text)
        counter_create += 1
        f.write(creat_text)
        #        if counter_create>2:
        #            break
        if counter_create % constrain_number == 0:
            f.write('commit \n')
            if counter_create % creation_max_in_file == 0:
                f.close()
                f = open('DrugBank_database_' + str(i) + '.cypher', 'w', encoding="utf-8")
                f.write('begin \n')
                i += 1
            else:
                f.write('begin \n')
    f.write('commit \n begin \n')
    # set stitch stereo ID as key and unique
    f.write('Create Constraint On (node:DrugBankdrug) Assert node.id Is Unique; \n')
    f.write('commit \n schema await \n begin \n')

    # make statistics and add querey for relationship to file
    print('edges Create')
    print (datetime.datetime.utcnow())
    # fileter out all frequecies with floats and compoute average, if no falues exist take a word
    for (drug_id1, drug_id2), describtion in dict_drug_interaction_info.items():
        url = 'http://www.drugbank.ca/drugs/' + drug_id1

        creat_text = ''' Match (drug1:DrugBankdrug{id: "%s"}), (drug2:DrugBankdrug{id: "%s"})
        Create (drug1)-[:interacts{url: "%s" , describtion: "%s"}] ->(drug2); \n''' % (
            drug_id1, drug_id2, url, describtion)
        # print(creat_text)
        #        print(query)
        counter_create += 1
        f.write(creat_text)
        #        if counter_create>2:
        #            break
        if counter_create % constrain_number == 0:
            f.write('commit \n')
            if counter_create % creation_max_in_file == 0:
                f.close()
                f = open('DrugBank_database_' + str(i) + '.cypher', 'w', encoding="utf-8")
                f.write('begin \n')
                i += 1
            else:
                f.write('begin \n')
    f.write('commit')


def main():
    print (datetime.datetime.utcnow())
    print('import drugbank information')

    #    create_connection_with_neo4j()

    get_drugbank_information()

    print('#############################################################')
    print (datetime.datetime.utcnow())
    print('generate cypher file')

    generate_cypher_file()

    print('#############################################################')
    print (datetime.datetime.utcnow())


if __name__ == "__main__":
    # execute only if run as a script
    main()
