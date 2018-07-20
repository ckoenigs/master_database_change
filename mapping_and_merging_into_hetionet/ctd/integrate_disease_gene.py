# -*- coding: utf-8 -*-
"""
Created on Fri Sep 15 11:41:20 2017

@author: ckoenigs
"""

from py2neo import Graph, authenticate
import datetime, time
import csv, sys
import  numpy as np
from py2neo.packages.httpstream import http

# change socket time out
# http.socket_timeout = 9999

'''
create connection to neo4j 
'''


def create_connection_with_neo4j_mysql():
    # create connection with neo4j
    # authenticate("localhost:7474", "neo4j", "test")
    # global g
    # g = Graph("http://localhost:7474/db/data/")

    authenticate("bimi:7475", "ckoenigs", "test")
    global g
    g = Graph("http://bimi:7475/db/data/",bolt=False)


# dictionary with all pairs and properties as value
dict_disease_gene = {}

# list time all disease finding
list_time_all_finding_disease=[]


# list time generate mondo ctd id dict
list_time_dict_mondo=[]

# list time dict association
list_time_dict_association=[]

# list time find association
list_time_find_association=[]

# list time add to file
list_time_add_to_file=[]

'''
get all relationships between gene and pathway, take the hetionet identifier an save all important information in a csv
also generate a cypher file to integrate this information 
'''


def take_all_relationships_of_gene_disease():
    # generate cypher file
    cypherfile = open('gene_disease/cypher.cypher', 'w')
    cypherfile.write('begin\n')
    cypherfile.write(
        'Match (n:Disease)-[r:ASSOCIATES_DaG]->(b:Gene) Where not exists(r.hetionet) Set r.hetionet="yes", r.resource=["Hetionet"];\n')
    cypherfile.write('commit\n')
    query = '''Using Periodic Commit 10000 Load CSV  WITH HEADERS From "file:/home/cassandra/Dokumente/Project/master_database_change/mapping_and_merging_into_hetionet/ctd/gene_disease/relationships.csv" As line Match (n:Gene{identifier:toInteger(line.GeneID)}), (b:Disease{identifier:line.DiseaseID}) Merge (b)-[r:ASSOCIATES_DaG]->(n) On Create Set r.hetionet='no', r.ctd='yes', r.url_ctd="http://ctdbase.org/detail.go?type=gene&acc="+line.GeneID , r.resource=["CTD"], r.source="CTD", r.inferences=split('|',line.inferences), r.pubMedIDs=split('|',line.pubMedIDs), r.directEvidence=split('|',line.directEvidence) ,r.omimIDs=split('|',line.omimIDs), r.license="© 2002–2012 MDI Biological Laboratory. © 2012–2018 MDI Biological Laboratory & NC State University. All rights reserved.", r.unbiased=line.unbiased On Match SET r.ctd='yes', r.url_ctd="http://ctdbase.org/detail.go?type=gene&acc="+line.GeneID, r.unbiased=line.unbiased, r.inferences=split('|',line.inferences), r.pubMedIDs=split('|',line.pubMedIDs), r.directEvidence=split('|',line.directEvidence) ,r.omimIDs=split('|',line.omimIDs), r.resource=r.resource+'CTD' ;\n '''
    cypherfile.write(query)
    cypherfile.write('begin\n')
    cypherfile.write('Match (n:Disease)-[r:ASSOCIATES_DaG]->(b:Gene) Where not exists(r.ctd) Set r.ctd="no";\n')
    cypherfile.write('commit')

    csvfile = open('gene_disease/relationships.csv', 'wb')
    writer = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    writer.writerow(['GeneID', 'DiseaseID','inferences','pubMedIDs','directEvidence','omimIDs','unbiased'])
    query='''Match (n:Disease) Return count(n)'''
    results=g.run(query)
    number_of_disease=int(results.evaluate())
    # number_of_disease=500

    # counter directEvidence
    counter_directEvidence=0

    # counter inferences
    counter_inferences=0

    print(int(number_of_disease))
    # sys.exit()
    number_of_compound_to_work_with=10

    counter_of_used_disease=0
    count_multiple_pathways = 0
    count_possible_relas = 0
    counter_all = 0
    count_blu = 0

    while counter_of_used_disease< number_of_disease:

        start = time.time()
        # and a.identifier='MONDO:0013604'
        query = '''MATCH p=(a)-[r:equal_to_D_Disease_CTD]->(b)  Where not exists(a.integrated)   With  a, collect(b.disease_id) As ctd Limit '''+str(
            number_of_compound_to_work_with) + ''' Set a.integrated='yes'  RETURN a.identifier , ctd '''

        print(query)
        # sys.exit()
        results = g.run(query)
        time_measurement = time.time() - start
        print('\tTake '+str(number_of_compound_to_work_with)+' disease: %.4f seconds' % (time_measurement))
        list_time_all_finding_disease.append(time_measurement)
        all_disease_id=[]
        dict_disease_id_mondo={}
        start = time.time()
        for mondo, ctd_diseases, in results:
            all_disease_id.extend(ctd_diseases)
            for disease in ctd_diseases:
                if disease in dict_disease_id_mondo:
                    dict_disease_id_mondo[disease].append(mondo)
                else:
                    dict_disease_id_mondo[disease]=[mondo]
        time_measurement = time.time() - start
        print('\t Generate dictionary: %.4f seconds' % (time_measurement))
        list_time_dict_mondo.append(time_measurement)
        start = time.time()

        print(dict_disease_id_mondo)

        all_disease_id='","'.join(all_disease_id)
        query = '''MATCH (disease)<-[r:associates_GD]-(gene) Where ()-[:equal_to_CTD_gene]->(gene) and disease.disease_id in ["''' + all_disease_id+ '''"] RETURN gene.gene_id, r, disease.mondos, disease.disease_id Order by disease.disease_id '''
        results = g.run(query)

        time_measurement = time.time() - start
        print('\t Find all association: %.4f seconds' % (time_measurement))
        list_time_find_association.append(time_measurement)
        start = time.time()
        # dictionary with all pairs and properties as value
        dict_disease_gene = {}

        for gene_id, rela, disease_mondos, disease_id, in results:
            counter_all+=1
            rela = dict(rela)
            inferenceChemicalName = rela['inferenceChemicalName'] if 'inferenceChemicalName' in rela else ''
            inferenceScore = rela['inferenceScore'] if 'inferenceScore' in rela else ''
            directEvidence = rela['directEvidence'] if 'directEvidence' in rela else ''
            pubMedIDs = '|'.join(rela['pubMedIDs']) if 'pubMedIDs' in rela else ''
            omimIDs='|'.join(rela['omimIDs']) if 'omimIDs' in rela else ''

            if inferenceScore!='' and float(inferenceScore)>=100:
                if directEvidence!='':
                    print('ohje direct evidence')
                if pubMedIDs=='':
                    print('some has not a pubmed id')
                continue
            blu=False
            for mondo in dict_disease_id_mondo[disease_id]:
                if not blu:
                    count_blu+=1
                if not (gene_id, mondo) in dict_disease_gene:
                    if inferenceChemicalName=='':
                        dict_disease_gene[(gene_id, mondo)] = [[],[directEvidence],[pubMedIDs],[omimIDs]]
                    else:
                        dict_disease_gene[(gene_id, mondo)] = [[inferenceChemicalName+':'+inferenceScore], [], [pubMedIDs], [omimIDs]]
                    count_possible_relas += 1
                else:

                    if inferenceChemicalName=='':
                        dict_disease_gene[(gene_id, mondo)][1].append(directEvidence)
                        dict_disease_gene[(gene_id, mondo)][2].append(pubMedIDs)
                        dict_disease_gene[(gene_id, mondo)][3].append(omimIDs)

                    else:
                        dict_disease_gene[(gene_id, mondo)][0].append(inferenceChemicalName+':'+inferenceScore)
                        dict_disease_gene[(gene_id, mondo)][2].append(pubMedIDs)
                        dict_disease_gene[(gene_id, mondo)][3].append(omimIDs)
                    count_multiple_pathways += 1




                blu=True
            if counter_all%10000==0:
                print(counter_all)
            if not blu:
                print(disease_mondos)
        time_measurement = time.time() - start
        print('\t Generate dictionary disease gene: %.4f seconds' % (time_measurement))
        list_time_dict_association.append(time_measurement)
        start = time.time()
        for (gene_id, mondo), [inferences, directEvidence, pubMedIDs, omimIDs] in dict_disease_gene.items():
            inferences=list(set(filter(bool,inferences)))
            directEvidence = list(set(filter(bool, directEvidence)))
            pubMedIDs = list(set(filter(bool, pubMedIDs)))
            omimIDs = list(set(filter(bool, omimIDs)))
            inferences_string='|'.join(inferences)
            directEvidence_string = '|'.join(directEvidence)
            pubMedIDs_string = '|'.join(pubMedIDs)
            omimIDs_string = '|'.join(omimIDs)

            if len(directEvidence)==0:
                counter_inferences+=1
                writer.writerow(
                    [gene_id, mondo, inferences_string, pubMedIDs_string, directEvidence_string, omimIDs_string, 'false'])
            else:
                counter_directEvidence += 1
                writer.writerow(
                [gene_id, mondo, inferences_string, pubMedIDs_string, directEvidence_string, omimIDs_string, 'true'])

        time_measurement = time.time() - start
        print('\t Add information to file: %.4f seconds' % (time_measurement))
        list_time_add_to_file.append(time_measurement)


        counter_of_used_disease+=number_of_compound_to_work_with

    print('Average finding disease:'+str(np.mean(list_time_all_finding_disease)))
    print('Average dict monde:' + str(np.mean(list_time_dict_mondo)))
    print('Average finding association:' + str(np.mean(list_time_find_association)))
    print('Min finding association:' + str(min(list_time_find_association)))
    print('Max finding association:' + str(max(list_time_find_association)))
    print('Average dict association:' + str(np.mean(list_time_dict_association)))
    print('Average add to file:' + str(np.mean(list_time_add_to_file)))

    query='''MATCH (n:Disease) REMOVE n.integrated'''
    g.run(query)
    print('number of direct evidence rela:'+str(counter_directEvidence))
    print('number of inferences rela:' + str(counter_inferences))
    print(counter_all)
    print(count_blu)
    print('number of new rela:'+str(count_possible_relas))
    print('number of relationships which appears multiple time:'+str(count_multiple_pathways))




def main():
    print (datetime.datetime.utcnow())
    print('Generate connection with neo4j and mysql')

    create_connection_with_neo4j_mysql()

    print(
        '###########################################################################################################################')

    print (datetime.datetime.utcnow())
    print('Take all gene-pathway relationships and generate csv and cypher file')

    take_all_relationships_of_gene_disease()

    print(
        '###########################################################################################################################')

    print (datetime.datetime.utcnow())


if __name__ == "__main__":
    # execute only if run as a script
    main()