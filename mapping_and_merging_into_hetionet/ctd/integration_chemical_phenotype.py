# -*- coding: utf-8 -*-
import csv
import datetime
import sys
from collections import defaultdict
import re
from typing import List

sys.path.append("../..")
import create_connection_to_databases

'''
create connection to neo4j 
'''


def create_connection_with_neo4j():
    # create connection with neo4j
    global g
    g = create_connection_to_databases.database_connection_neo4j()


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
        dict_action[(chemical_id, go_id)][1] = dict_action[(chemical_id, go_id)][1].union(pubMedIds)
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
                     rela_full, label, anatomy_terms, inference_gene_symbols, comentioned_terms, from_chemical):
    # generate for every rela a dictionary with their own drug-go pair
    if not (rela_full, label, from_chemical) in dict_rela_to_drug_go_pair:
        dict_rela_to_drug_go_pair[(rela_full, label, from_chemical)] = defaultdict(dict)

    # add all chemical-go pair into the right dictionary
    if drugbank_ids:
        for drugbank_id in drugbank_ids:
            sort_into_dictionary_and_add(dict_rela_to_drug_go_pair[(rela_full, label, from_chemical)],
                                         drugbank_id, go_id, interaction_text,
                                         pubMedIds, interactions_actions, anatomy_terms, inference_gene_symbols,
                                         comentioned_terms)
    else:
        sort_into_dictionary_and_add(dict_rela_to_drug_go_pair[(rela_full, label, from_chemical)],
                                     chemical_id, go_id, interaction_text,
                                     pubMedIds, interactions_actions, anatomy_terms, inference_gene_symbols,
                                     comentioned_terms)


dict_rela_name_to_text_name = {
    'INCREASES': 'increased',
    'DECREASES': 'decreased'
}


def find_multiple_occurrences(substring: str, string: str) -> List[int]:
    """
    search for all start indices of the substring in a string
    :param substring: string
    :param string: string
    :return: list of indices
    """
    return [i for i in range(len(string)) if string.startswith(substring, i)]


def check_for_go_and_chemical_in_string(string, found_chemical_synonym, go_name, rela_name, chemical_id, drugbank_ids,
                                        go_id, interaction_text, interactions_actions,
                                        pubMedIds, label, anatomy_terms, inference_gene_symbols, comentioned_terms):
    """
    check for the position of chemical and go in the string
    :param string: string
    :param found_chemical_synonym:the name of the chemical which is used
    :param go_name: the name of go which is used
    :return: if they are found together
    """
    found_together = False
    part = string.lower()
    positions_chemical_new = find_multiple_occurrences(' ' + found_chemical_synonym + ' ', part)
    position_go_new = part.find(' ' + go_name + ' ')
    position_rela_new = part.find(' ' + dict_rela_name_to_text_name[rela_name] + ' ')
    length_of_phenotyp_string = len(go_name)

    # check if all values appear in the string (go name, chemical name and relationships name
    # however, many phenotypes include the chemical name in the name to avoid to have phenotype and chemical in the same
    # check if the position of the chemical is not between the start  and the end of the phenotype string
    for position_chemical_new in positions_chemical_new:
        if position_chemical_new != -1 and position_go_new != -1 and position_rela_new != -1 and not (
                position_go_new <= position_chemical_new <= position_go_new + length_of_phenotyp_string):
            if position_chemical_new < position_go_new:
                found_together = True
                add_pair_to_dict(chemical_id, drugbank_ids, go_id, interaction_text, interactions_actions,
                                 pubMedIds,
                                 rela_name, label, anatomy_terms, inference_gene_symbols, comentioned_terms, True)
            else:
                found_together = True
                add_pair_to_dict(chemical_id, drugbank_ids, go_id, interaction_text, interactions_actions,
                                 pubMedIds,
                                 rela_name, label, anatomy_terms, inference_gene_symbols, comentioned_terms,
                                 False)
    return found_together


'''
check if it is a type rela or not
'''


def check_for_rela_type(interactions_actions, rela_name, chemical_id, drugbank_ids, go_id, interaction_text, pubMedIds,
                        label, anatomy_terms, inference_gene_symbols, comentioned_terms, found_chemical_synonym,
                        go_name):
    # to find the exact words and to avoid that not a space is in front or in the end spaces are add
    interaction_text_with_spaces = ' ' + interaction_text.replace('[', '[ ') + ' '
    interaction_text_with_spaces = interaction_text_with_spaces.replace(']', ' ]')

    if len(interactions_actions) == 1:
        found_together = found_together = check_for_go_and_chemical_in_string(interaction_text_with_spaces,
                                                                              found_chemical_synonym, go_name,
                                                                              rela_name, chemical_id,
                                                                              drugbank_ids, go_id, interaction_text,
                                                                              interactions_actions,
                                                                              pubMedIds, label, anatomy_terms,
                                                                              inference_gene_symbols,
                                                                              comentioned_terms)

        if not found_together:
            print('something went really wrong')
            print(chemical_id)
            print(go_id)
            print(interaction_text_with_spaces)
            add_pair_to_dict(chemical_id, drugbank_ids, go_id, interaction_text, interactions_actions, pubMedIds,
                             rela_name, label, anatomy_terms, inference_gene_symbols, comentioned_terms, True)
            sys.exit('ctd chemical phenotype error')
    else:

        found_together = False

        for part in interaction_text_with_spaces.split('['):
            for smaller_part in part.split(']'):
                # find take every time the first time when the substring appeares, so some times the chemcial appears multiple
                # time so the order for the sub action need to be new classified

                found_together_here = check_for_go_and_chemical_in_string(smaller_part, found_chemical_synonym, go_name,
                                                                          rela_name, chemical_id,
                                                                          drugbank_ids, go_id, interaction_text,
                                                                          interactions_actions,
                                                                          pubMedIds, label, anatomy_terms,
                                                                          inference_gene_symbols,
                                                                          comentioned_terms)
                if found_together_here:
                    found_together = True

        if not found_together:
            add_pair_to_dict(chemical_id, drugbank_ids, go_id, interaction_text, interactions_actions, pubMedIds,
                             'ASSOCIATES', label, anatomy_terms, inference_gene_symbols, comentioned_terms, True)


'''
get all relationships between go and chemical, take the hetionet identifier an save all important information in a csv
also generate a cypher file to integrate this information 
'''


def take_all_relationships_of_go_chemical():
    counter_all_rela = 0

    #  Where chemical.chemical_id='D000077212' and go.go_id='0006915'; Where chemical.chemical_id='C057693' and go.go_id='4128' Where chemical.chemical_id='D001564' and go.go_id='9429'  Where chemical.chemical_id='D004976' and go.go_id='2950' Where chemical.chemical_id='D015741' and go.go_id='367'
    query = '''MATCH (chemical:CTDchemical)-[r:phenotype{organismid:'9606'}]->(cgo:CTDGO)-[:equal_to_CTD_go]-(go) RETURN cgo.go_id, cgo.name, labels(go), r, chemical.chemical_id, chemical.name, chemical.synonyms, chemical.drugBankIDs'''
    results = g.run(query)

    for go_id, go_name, go_labels, rela, chemical_id, chemical_name, chemical_synonyms, drugbank_ids, in results:
        go_label = go_labels[0]
        go_name = go_name.lower()
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
                                pubMedIds, go_label, anatomy_terms, inference_gene_symbols, comentioned_terms,
                                found_chemical_synonym, go_name)

        elif "decreases^phenotype" in interactions_actions:
            check_for_rela_type(interactions_actions, 'DECREASES', chemical_id, drugbank_ids, go_id, interaction_text,
                                pubMedIds, go_label, anatomy_terms, inference_gene_symbols, comentioned_terms,
                                found_chemical_synonym, go_name)

        else:
            add_pair_to_dict(chemical_id, drugbank_ids, go_id, interaction_text, interactions_actions, pubMedIds,
                             'ASSOCIATES', go_label, anatomy_terms, inference_gene_symbols, comentioned_terms, True)

    print('number of all rela in human organism:' + str(counter_all_rela))


'''
find the shortest list and all list with the same length but different value
'''


def find_shortest_list_and_indices(list_of_lists):
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


def generate_cypher_queries(file_name, label, rela, start_node, end_node):
    query_first_part = '''Using Periodic Commit 10000 Load CSV  WITH HEADERS From "file:''' + path_of_directory + '''master_database_change/mapping_and_merging_into_hetionet/ctd/''' + file_name + '''" As line Fieldterminator '\\t' Match (b:Chemical{identifier:line.chemical_id}), (go:%s{identifier:line.go_id}) Create (%s)-[:%s {'''
    query_first_part = query_first_part % (label, start_node, rela)
    query_end = 'ctd:"yes", source:"CTD", ctd_url:"http://ctdbase.org/detail.go?type=chem&acc="+line.chemical_id ,resource:["CTD"], license:"© 2002–2012 MDI Biological Laboratory. © 2012–2018 MDI Biological Laboratory & NC State University. All rights reserved"}]->(%s);\n'
    for property in header:
        if property in ['chemical_id', 'go_id']:
            continue
        if property not in ['interaction_text', 'unbiased']:
            query_first_part += property + ':split(line.' + property + ',"|"), '
        else:
            if  property=='unbiased':
                query_first_part += property + ':toBoolean(line.' + property + '), '
                continue
            query_first_part += property + ':line.' + property + ', '
    query = query_first_part + query_end % end_node
    cypherfile.write(query)


# header for csv files
header = ['chemical_id', 'go_id', 'interaction_text', 'pubmed_ids', 'interaction_actions', 'unbiased', 'anatomy_terms',
          'comentioned_terms']

# dictionary from go term to shor form
dict_go_term_to_short_form = {
    'BiologicalProcess': 'BP',
    'CellularComponent': 'CC',
    'MolecularFunction': 'MF'
}


def prepare_list_of_list(list_of_information, index, indices):
    """
    get only the element from the shortest interaction_actions and change in the strings the ^ to :
    :param list_of_information: list of lists
    :param index: int
    :param indices: list of ints
    :return: string
    """
    list_of_shortest_list = [list_of_information[index][x] for x in indices]
    shortest_list = []
    for list_part in list_of_shortest_list:
        list_part = [x.replace('^', ':') for x in list_part]
        shortest_list.append(';'.join(list_part))
    shortest_list = '|'.join(shortest_list)
    return shortest_list


'''
now go through all rela types and add every pair to the right csv
but only take the shortest interaction text and the associated intereaction actions and go forms
'ChemicalID', 'goID', 'interaction_text', 'go_forms', 'pubMedIds', 'interactions_actions', 'unbiased'
'''


def fill_the_csv_files():
    for (rela_full, label, from_chemical), dict_chemical_go_pair in dict_rela_to_drug_go_pair.items():
        short_form_label = dict_go_term_to_short_form[label]
        if from_chemical:
            file_name = 'chemical_phenotype/chemical_' + label + '_' + rela_full + '.tsv'
            generate_cypher_queries(file_name, label, rela_full + '_C' + rela_full[0].lower() + short_form_label, 'b',
                                    'go')
        else:
            file_name = 'chemical_phenotype/' + label + '_chemical_' + rela_full + '.tsv'
            generate_cypher_queries(file_name, label, rela_full + '_' + short_form_label + rela_full[0].lower() + 'C',
                                    'go', 'b')
        file = open(file_name, 'w', encoding='utf-8')
        csv_writer = csv.writer(file, delimiter='\t')
        csv_writer.writerow(header)
        for (chemical_id, go_id), list_of_information in dict_chemical_go_pair.items():
            pubMedIds = list_of_information[1]
            pubMedIds = '|'.join(pubMedIds)
            interactions_actions = list_of_information[2]
            indices, shortest_interaction_actions = find_shortest_list_and_indices(interactions_actions)
            shortest_interaction_actions = [';'.join(x) for x in shortest_interaction_actions]
            shortest_interaction_actions = '|'.join(shortest_interaction_actions)

            interaction_texts = list_of_information[0]
            shortest_interaction_text = [interaction_texts[x] for x in indices]

            shortest_anatomy = prepare_list_of_list(list_of_information, 3, indices)
            shortest_conditional = prepare_list_of_list(list_of_information, 5, indices)

            unbiased = True if len(pubMedIds) > 0 else False
            shortest_interaction_text = '|'.join(shortest_interaction_text)
            csv_writer.writerow(
                [chemical_id, go_id, shortest_interaction_text, pubMedIds,
                 shortest_interaction_actions
                    , unbiased, shortest_anatomy, shortest_conditional])


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
    print('Take all go-chemical relationships and generate csv and cypher file')

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
