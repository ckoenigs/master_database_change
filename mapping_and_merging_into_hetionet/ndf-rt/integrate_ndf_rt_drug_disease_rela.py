import datetime
import sys, csv

sys.path.append("../..")
import create_connection_to_databases

'''
create connection to neo4j and mysql
'''


def create_connection_with_neo4j_mysql():
    global g
    g = create_connection_to_databases.database_connection_neo4j()


# dictionary pair to relatype
dict_pair_to_rela_type = {}

# dictionary_rela type to csv file
dict_rela_type_to_csv_file = {}

# dictionary rela type to rela label
dict_type_to_label = {
    'may_treat': 'TREATS_CtD',
    'may_prevent': 'PREVENTS_CpD',
    'CI_with': 'CONTRAINDICATES_CcD',
    'induces': 'INDUCES_CiD',
    'may_diagnose': 'MAY_DIAGNOSES_CmdD'
}

'''
load all connection types from ndf-rt between drug and disease
and integrate them in different csv files
'''


def integrate_connection_into_hetionet():
    # count of integrated contra-indication relationship
    count_contra_indicate = 0
    # count of integrated induces relationships
    count_induces = 0
    # count all mapped codes
    count_code = 0

    query_start = '''Using Periodic Commit 10000 Load CSV  WITH HEADERS From "file:''' + path_of_directory + '''master_database_change/mapping_and_merging_into_hetionet/ndf-rt/%s" As line FIELDTERMINATOR '\\t' Match (a:Chemical{identifier:line.chemical_id}), (b:Disease{identifier:line.disease_id})  '''

    # cypher file
    cypher_file = open('relationships/cypher.cypher', 'w', encoding='utf-8')

    counter_contraindication_double = 0
    counter_induces_double = 0

    query = '''MATCH (a:Chemical)--(n:NDF_RT_DRUG_KIND)-[r]-(:NDF_RT_DISEASE_KIND)--(b:Disease) RETURN Distinct a.identifier, type(r), r.source, b.identifier'''
    result = g.run(query)

    for chemical_id, rela_type,rela_source, disease_id, in result:
        if rela_type not in dict_rela_type_to_csv_file:
            file = open('relationships/rela_' + rela_type + '.tsv', 'w', encoding='utf-8')
            csv_writer = csv.writer(file, delimiter='\t')
            csv_writer.writerow(['chemical_id', 'disease_id', 'source'])
            dict_rela_type_to_csv_file[rela_type] = csv_writer
            query_check = 'Match p=(:Chemical)-[:%s]-(:Disease) Return p Limit 1' % dict_type_to_label[rela_type]
            results = g.run(query_check)
            result = results.evaluate()
            if result:
                query = query_start + 'Merge (a)-[r:%s]->(b) On Create Set r.source=line.source, r.resource=["NDF-RT"], r.ndf_rt="yes", r.unbiased=false, r.license="" On Match Set r.resource=r.resource+"NDF-RT", r.ndf_rt="yes";\n '
            else:
                query = query_start + "Create (a)-[r:%s{source:line.source, resource:['NDF-RT'], ndf_rt:'yes', unbiased:false, license:''}]->(b);\n"
            query = query % ('relationships/rela_' + rela_type + '.tsv', dict_type_to_label[rela_type])
            cypher_file.write(query)

        count_code += 1
        source= 'NDF-RT' if rela_source=='NDFRT' else rela_source+' via NDF-RT'
        dict_rela_type_to_csv_file[rela_type].writerow([chemical_id, disease_id])

    print('number of contra indications connections:' + str(count_contra_indicate))
    print('number of induces connections:' + str(count_induces))
    print('double of contra indicates connection:' + str(counter_contraindication_double))
    print('double of induces connection:' + str(counter_induces_double))
    print(dict_rela_type_to_csv_file.keys())


def main():
    global path_of_directory
    if len(sys.argv) > 1:
        path_of_directory = sys.argv[1]
    else:
        sys.exit('need a path')

    print(datetime.datetime.utcnow())
    print('Generate connection with neo4j and mysql')

    create_connection_with_neo4j_mysql()

    print(
        '###########################################################################################################################')

    print(datetime.datetime.utcnow())
    print('Load in chemical from hetionet')

    integrate_connection_into_hetionet()
    print(
        '###########################################################################################################################')

    print(datetime.datetime.utcnow())


if __name__ == "__main__":
    # execute only if run as a script
    main()
