# -*- coding: utf-8 -*-
"""
Created on Thu Sep 21 08:35:25 2017

@author: Cassandra
"""
import csv, datetime

# dictionary with key rxnorm cui and value unii list
dict_rxcui_to_unii = {}
# dictionary with key unii and value rxnorm cui list
dict_unii_to_rxcui = {}

'''
load unii to rxcui
'''
def load_unii_to_rxcui():
    g = open('results/UNIIs_with_RXCUI.tsv', 'r')
    csv_reader=csv.DictReader(g, delimiter='\t')
    # print(csv_reader.fieldnames)
    for line in csv_reader:
        unii = line['unii']
        rxcui = line['rxcui']
        if rxcui=='':
            continue
        if not rxcui in dict_rxcui_to_unii:
            dict_rxcui_to_unii[rxcui] = [unii]
        else:
            dict_rxcui_to_unii[rxcui].append(unii)
        if not unii in dict_unii_to_rxcui:
            dict_unii_to_rxcui[unii] = [rxcui]
        else:
            dict_unii_to_rxcui[unii].append(rxcui)

    print('number of rxcui:' + str(len(dict_rxcui_to_unii)))
    print('number of unii:' + str(len(dict_unii_to_rxcui)))
    g.close()




'''
load all rxnorm cui and unii from rxnorm in dictionaries
0:rxcui
1:unii
'''
def load_rxcui_to_unii():
    counter_rxcui = 0
    counter_unii = 0
    count_different_unii = 0
    f = open('results/map_rxnorm_to_UNII.tsv', 'r')
    csv_reader=csv.DictReader(f,delimiter='\t')
    for line in csv_reader:
        rxcui = line['rxcui']
        unii = line['unii']
        if unii=='':
            continue
        if not rxcui in dict_rxcui_to_unii:
            counter_rxcui += 1
            dict_rxcui_to_unii[rxcui] = [unii]
        else:
            if not unii in dict_rxcui_to_unii[rxcui]:
                count_different_unii += 1
                dict_rxcui_to_unii[rxcui].append(unii)

        if not unii in dict_unii_to_rxcui:
            dict_unii_to_rxcui[unii] = [rxcui]
            counter_unii += 1
        else:
            dict_unii_to_rxcui[unii].append(rxcui)

    f.close()
    print(counter_rxcui)
    print(count_different_unii)
    print(counter_unii)
    print('number of rxcui:' + str(len(dict_rxcui_to_unii)))
    print('number of unii:' + str(len(dict_unii_to_rxcui)))

dict_unii_to_inchi_key = {}

'''
find for all unii a inchikey in fda-srs
0:UNII	
1:PT	
2:RN	
3:EC	
4:NCIT	
5:RXCUI	
6:ITIS	
7:NCBI	
8:PLANTS	
9:GRIN	
10:MPNS	
11:INN_ID	
12:MF	
13:INCHIKEY	
14:SMILES	
15:UNII_TYPE

'''
def generate_unii_inchikey_connection():
    h = open('unii/unii_data.txt', 'r')
    csv_writer=csv.DictReader(h, delimiter='\t')
    for line in csv_writer:
        unii = line['UNII']
        inchikey = line['INCHIKEY']
        if inchikey != '':
            if unii in dict_unii_to_rxcui:
                if not unii in dict_unii_to_inchi_key:
                    dict_unii_to_inchi_key[unii] = inchikey

    h.close()
    print(len(dict_unii_to_inchi_key))

'''
generate new file with rxcui, uniis, inchikeys
'''
def generate_rxcui_unii_inchikey_file():
    g = open('results/new_rxcui_uniis_inchkeys.tsv', 'w')
    csv_writer=csv.writer(g,delimiter='\t')
    csv_writer.writerow(['rxcui','uniis','inchikeys'])
    for rxcui, uniis in dict_rxcui_to_unii.items():
        if rxcui=='' :
            continue
        uniis = list(set(uniis))
        inchikeys_list = []
        for unii in uniis:
            if unii in dict_unii_to_inchi_key:
                inchikeys_list.append(dict_unii_to_inchi_key[unii])
        inchikeys_list = list(set(inchikeys_list))
        string_uniis = '|'.join(uniis)
        string_inchikeys = '|'.join(inchikeys_list)
        csv_writer.writerow([rxcui , string_uniis , string_inchikeys ])

    g.close()


def main():
    print(
        '###########################################################################################################################')
    print (datetime.datetime.utcnow())
    print('load all information over rxcui and unii in a dictionary')

    load_unii_to_rxcui()

    print(
        '###########################################################################################################################')
    print(datetime.datetime.utcnow())
    print('load all information over rxcui and unii in a dictionary')

    load_rxcui_to_unii()

    print(
        '###########################################################################################################################')
    print(datetime.datetime.utcnow())
    print('load all information over unii to inchikey in a dictionary')

    generate_unii_inchikey_connection()

    print(
        '###########################################################################################################################')
    print(datetime.datetime.utcnow())
    print('generate file rxcui, unii and inchikey')

    generate_rxcui_unii_inchikey_file()

    print(
    '###########################################################################################################################')
    print (datetime.datetime.utcnow())


if __name__ == "__main__":
    # execute only if run as a script
    main()