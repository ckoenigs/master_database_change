# -*- coding: utf-8 -*-
import csv
import datetime
import sys
from collections import defaultdict

from py2neo import Graph

'''
create connection to neo4j 
'''


def create_connection_with_neo4j():
    # create connection with neo4j
    global g
    g = Graph("http://localhost:7474/db/data/", auth=("neo4j", "test"))


# generate cypher file
cypherfile = open('chemical_phenotype/cypher.cypher', 'w', encoding='utf-8')

# dictionary with rela name to drug-go/protein pair
dict_rela_to_drug_go_pair = {}


'''
generate csv file with the columns fo a path
'''


def generate_csv(path, head):
    csvfile = open(path, 'w', encoding='utf-8')
    writer = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    writer.writerow(head)
    return writer


'''
search for chemical
'''


def search_for_chemical(chemical_name, chemical_synonyms, interaction_text):
    found_chemical = False
    found_chemical_synonym = ''
    # check also the  name
    if not chemical_name is None and chemical_name != '':
        chemical_synonyms.insert(0, chemical_name)

    # find the used name of the chemical
    for chemical_synonym in chemical_synonyms:
        found_chemical, found_chemical_synonym = search_for_name_in_string(interaction_text, chemical_synonym)
        if found_chemical:
            break
    if not found_chemical:
        print('chemical name not found')
        print(chemical_name)
    found_chemical_synonym = found_chemical_synonym if found_chemical else chemical_name
    return found_chemical_synonym


'''
search for a name in a string and gib back if found and the value
'''


def search_for_name_in_string(interaction_text, name):
    found_name_value = ''
    found_name = False
    interaction_text = interaction_text.lower()
    name = name.lower()
    possible_position = interaction_text.find(name)
    if possible_position != -1:
        found_name_value = name
        found_name = True
    return found_name, found_name_value


# dictionary of chemical id to chemical name used in the interaction text
dict_chemical_id_to_used_name = {}

'''
sort the information into the right dictionary and add the infomation
'''


def sort_into_dictionary_and_add(dict_action, chemical_id, go_id, interaction_text, pubMedIds,
                                 interactions_actions, anatomy_terms, inference_gene_symbols, comentioned_terms):
    if (chemical_id, go_id) in dict_action:
        dict_action[(chemical_id, go_id)][0].append(interaction_text)
        dict_action[(chemical_id, go_id)][1].union(pubMedIds)
        dict_action[(chemical_id, go_id)][2].append(interactions_actions)
        dict_action[(chemical_id, go_id)][3].append(anatomy_terms)
        dict_action[(chemical_id, go_id)][4].append(inference_gene_symbols)
        dict_action[(chemical_id, go_id)][5].append(comentioned_terms)
    else:
        dict_action[(chemical_id, go_id)] = [[interaction_text], set(pubMedIds),
                                             [interactions_actions], [anatomy_terms], [inference_gene_symbols],
                                             [comentioned_terms]]



'''
generate for new rela  a dictionary entry with a dictionary for all chemical-go pairs
all information of the pair are add into the dictionary
'''


def add_pair_to_dict(chemical_id, drugbank_ids, go_id, interaction_text, interactions_actions, pubMedIds,
                     rela_full, label, anatomy_terms, inference_gene_symbols, comentioned_terms):
    # generate for every rela a dictionary with their own drug-go pair
    if not (rela_full, label) in dict_rela_to_drug_go_pair:
        dict_rela_to_drug_go_pair[(rela_full, label)] = defaultdict(dict)

    # add all chemical-go pair into the right dictionary
    if drugbank_ids:
        for drugbank_id in drugbank_ids:
            sort_into_dictionary_and_add(dict_rela_to_drug_go_pair[(rela_full, label)],
                                         drugbank_id, go_id, interaction_text,
                                         pubMedIds, interactions_actions, anatomy_terms, inference_gene_symbols,
                                         comentioned_terms)
    else:
        sort_into_dictionary_and_add(dict_rela_to_drug_go_pair[(rela_full, label)],
                                     chemical_id, go_id, interaction_text,
                                     pubMedIds, interactions_actions, anatomy_terms, inference_gene_symbols,
                                     comentioned_terms)

dict_rela_name_to_text_name={
    'INCREASES':'increased',
    'DECREASES':'decreased'
}


'''
check if it is a type rela or not
'''


def check_for_rela_type(interactions_actions, rela_name, chemical_id, drugbank_ids, go_id, interaction_text, pubMedIds,
                        label, anatomy_terms, inference_gene_symbols, comentioned_terms, found_chemical_synonym, go_name):
    if len(interactions_actions) == 1:
        add_pair_to_dict(chemical_id, drugbank_ids, go_id, interaction_text, interactions_actions, pubMedIds,
                         rela_name, label, anatomy_terms, inference_gene_symbols, comentioned_terms)
    else:
        # to find the exact words and to avoid that not a space is in front or in the end spaces are add
        interaction_text_with_spaces = ' ' + interaction_text.replace('[', '[ ') + ' '
        interaction_text_with_spaces = interaction_text_with_spaces.replace(']', ' ]')
        
        found_together=False

        for part in interaction_text_with_spaces.split('['):
            for smaller_part in part.split(']'):
                # find take every time the first time when the substring appeares, so some times the chemcial appears multiple
                # time so the order for the sub action need to be new classified
                smaller_part = smaller_part.lower()
                position_chemical_new = smaller_part.find(' ' + found_chemical_synonym + ' ')
                position_go_new = smaller_part.find(' ' + go_name + ' ')
                position_rela_new= smaller_part.find(' '+dict_rela_name_to_text_name[rela_name]+' ')

                if position_chemical_new != -1 and position_go_new != -1 and position_rela_new!=-1:
                    if position_chemical_new< position_go_new:
                        found_together=True
                        add_pair_to_dict(chemical_id, drugbank_ids, go_id, interaction_text, interactions_actions,
                                         pubMedIds,
                                         rela_name, label, anatomy_terms, inference_gene_symbols, comentioned_terms)
                    else:
                        print(chemical_id, go_id)
                        print(interaction_text)
                        sys.exit('I have to consider the other direction ;(')
        if not found_together:
            add_pair_to_dict(chemical_id, drugbank_ids, go_id, interaction_text, interactions_actions, pubMedIds,
                             'ASSOCIATES', label, anatomy_terms, inference_gene_symbols, comentioned_terms)
                
                    


'''
get all relationships between go and chemical, take the hetionet identifier an save all important information in a csv
also generate a cypher file to integrate this information 
'''


def take_all_relationships_of_go_chemical():
    counter_all_rela = 0

    #  Where chemical.chemical_id='D000117' and go.go_id='2219'; Where chemical.chemical_id='C057693' and go.go_id='4128' Where chemical.chemical_id='D001564' and go.go_id='9429'  Where chemical.chemical_id='D004976' and go.go_id='2950' Where chemical.chemical_id='D015741' and go.go_id='367'
    query = '''MATCH (chemical:CTDchemical)-[r:phenotype{organismid:'9606'}]->(cgo:CTDGO)-[:equal_to_CTD_go]-(go) RETURN cgo.go_id, cgo.name, labels(go), r, chemical.chemical_id, chemical.name, chemical.synonyms, chemical.drugBankIDs'''
    results = g.run(query)

    for go_id, go_name, go_labels, rela, chemical_id, chemical_name, chemical_synonyms, drugbank_ids, in results:
        go_label = go_labels[0]
        go_name=go_name.lower()
        counter_all_rela += 1
        interaction_text = rela['interaction'] if 'interaction' in rela else ''
        pubMedIds = rela['pubmedids'] if 'pubmedids' in rela else []
        interactions_actions = rela['interactionactions'] if 'interactionactions' in rela else []
        comentioned_terms = rela['comentionedterms'] if 'comentionedterms' in rela else []
        anatomy_terms = rela['anatomyterms'] if 'anatomyterms' in rela else []
        inference_gene_symbols = rela['inferencegenesymbols'] if 'inferencegenesymbols' in rela else []
        drugbank_ids = drugbank_ids if not drugbank_ids is None else []

        chemical_synonyms = chemical_synonyms if not chemical_synonyms is None else []
        chemical_synonyms = list(filter(None, chemical_synonyms))

        # for searching in the interaction text if go and chemical are in the same []

        if chemical_id in dict_chemical_id_to_used_name:
            found_chemical_synonym = dict_chemical_id_to_used_name[chemical_id]
        else:
            found_chemical_synonym = search_for_chemical(chemical_name, chemical_synonyms, interaction_text)
            dict_chemical_id_to_used_name[chemical_id] = found_chemical_synonym

        if "increases^phenotype" in interactions_actions:
            check_for_rela_type(interactions_actions, 'INCREASES', chemical_id, drugbank_ids, go_id, interaction_text,
                                pubMedIds, go_label, anatomy_terms, inference_gene_symbols, comentioned_terms, found_chemical_synonym, go_name)

        elif "decreases^phenotype" in interactions_actions:
            check_for_rela_type(interactions_actions, 'DECREASES', chemical_id, drugbank_ids, go_id, interaction_text,
                                pubMedIds, go_label, anatomy_terms, inference_gene_symbols, comentioned_terms, found_chemical_synonym, go_name)

        else:
            add_pair_to_dict(chemical_id, drugbank_ids, go_id, interaction_text, interactions_actions, pubMedIds,
                             'ASSOCIATES', go_label, anatomy_terms, inference_gene_symbols, comentioned_terms)

    print('number of all rela in human organism:' + str(counter_all_rela))




'''
find the shortest list and all list with the same length but different value
'''


def find_shortest_list_and_indeces(list_of_lists):
    shortest = min(list_of_lists, key=len)
    all_with_the_same_length = [shortest]
    shortest_length = len(shortest)
    indices = [list_of_lists.index(shortest)]
    counter = 0
    for list_of_list in list_of_lists:
        if len(list_of_list) == shortest_length:
            if not list_of_list in all_with_the_same_length:
                all_with_the_same_length.append(list_of_list)
                indices.append(counter)
        counter += 1

    return indices, all_with_the_same_length

'''
generate cypher queries
'''
def generate_cypher_queries(file_name,label, rela):
    #todo rela with additional CiBp or so
    query_first_part = '''Using Periodic Commit 10000 Load CSV  WITH HEADERS From "file:''' + path_of_directory + '''master_database_change/mapping_and_merging_into_hetionet/ctd/''' + file_name + '''" As line Match (b:Chemical{identifier:line.chemical_id}), (go:%s{identifier:line.go_id}) Create (b)-[:%s '''
    query_first_part=query_first_part %(label,rela)
    query_end=']->(go);\n'
    for property in header:
        if property in ['chemical_id','go_id']:
            continue
        if property not in ['interaction_text','unbiased']:
            query_first_part+= property+':split(line.'+property+',"|"), '
        else:
            query_first_part += property + ':line.' + property + ', '
    query=query_first_part[:-2]+query_end
    cypherfile.write(query)



#header for csv files
header=['chemical_id','go_id', 'interaction_text', 'pubmed_ids', 'interaction_actions','unbiased']

'''
now go through all rela types and add every pair to the right csv
but only take the shortest interaction text and the associated intereaction actions and go forms
'ChemicalID', 'goID', 'interaction_text', 'go_forms', 'pubMedIds', 'interactions_actions', 'unbiased'
'''


def fill_the_csv_files():
    for (rela_full,label), dict_chemical_go_pair in dict_rela_to_drug_go_pair.items():
        file_name='chemical_phenotype/chemical_'+label+'_'+rela_full+'.tsv'
        file=open(file_name,'w',encoding='utf-8')
        csv_writer=csv.writer(file,delimiter='\t')
        csv_writer.writerow(header)
        generate_cypher_queries(file_name,label,rela)
        for (chemical_id, go_id), list_of_information in dict_chemical_go_pair.items():
            pubMedIds = list_of_information[1]
            pubMedIds = '|'.join(pubMedIds)
            interactions_actions = list_of_information[2]
            indices, shortest_interaction_actions = find_shortest_list_and_indeces(interactions_actions)
            shortest_interaction_actions = [';'.join(x) for x in shortest_interaction_actions]
            shortest_interaction_actions = '|'.join(shortest_interaction_actions)

            interaction_texts = list_of_information[0]
            shortest_interaction_text = [interaction_texts[x] for x in indices]

            unbiased = True if len(pubMedIds) > 0 else False
            shortest_interaction_text = '|'.join(shortest_interaction_text)
            csv_writer.writerow(
                [chemical_id, go_id, shortest_interaction_text,  pubMedIds,
                 shortest_interaction_actions
                    , unbiased])


def main():
    global path_of_directory
    if len(sys.argv) > 1:
        path_of_directory = sys.argv[1]
    else:
        sys.exit('need a path')

    print(datetime.datetime.utcnow())
    print('generate connection with neo4j and mysql')

    create_connection_with_neo4j()

    print(
        '###########################################################################################################################')

    print(datetime.datetime.utcnow())
    print('Take all go-pathway relationships and generate csv and cypher file')

    take_all_relationships_of_go_chemical()

    print(
        '###########################################################################################################################')

    print(datetime.datetime.utcnow())
    print('write into csv files')

    fill_the_csv_files()

    print(
        '###########################################################################################################################')

    print(datetime.datetime.utcnow())


if __name__ == "__main__":
    # execute only if run as a script
    main()