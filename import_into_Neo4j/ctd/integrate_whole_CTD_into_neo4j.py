from py2neo import Graph, authenticate
import sys
import datetime
import csv


# connect with the neo4j database
def database_connection():
    authenticate("localhost:7474", "neo4j", "test")
    global g
    g = Graph("http://localhost:7474/db/data/")


# node cypher file number
node_file_number = 1

# edges cypher file number
edges_file_number = 1

# cypher file for all nodes
cypher_file_nodes = open('nodes_' + str(node_file_number) + '.cypher', 'w')
node_file_number += 1
cypher_file_nodes.write('begin\n')

# cypher file for all relationships
cypher_file_edges = open('edges_' + str(edges_file_number) + '.cypher', 'w')
edges_file_number += 1
cypher_file_edges.write('begin\n')

# count the number of queries of node generation
counter_nodes_queries = 0
# count the number of queries of node generation
counter_edges_queries = 0
# number of queries in a commit block
constraint_number = 20000
# number of queries in a cypher file
max_queries_for_a_file = 1000000


def check_for_commit_or_file_break(cypher_file_nodes, node_file_number, file_start, counter_nodes_queries):
    # global cypher_file_nodes, node_file_number
    if counter_nodes_queries % constraint_number == 0:
        cypher_file_nodes.write('commit\n')
        if counter_nodes_queries % max_queries_for_a_file == 0:
            cypher_file_nodes.close()
            cypher_file_nodes = open(file_start + str(node_file_number) + '.cypher')
            node_file_number += 1
        cypher_file_nodes.write('begin\n')


'''
load ctd chemical file and generate cypher file for the nodes with properties:
    0:ChemicalName
    1:ChemicalID
    2:CasRN
    3:Definition
    4:ParentIDs
    5:TreeNumbers
    6:ParentTreeNumbers
    7:Synonyms
    8:DrugBankID
furthermore it test if already nodes are in Neo4j and only add the new ones 
'''


def load_chemicals_and_add_to_cypher_file():
    global counter_nodes_queries, cypher_file_nodes
    # say if in neo4j already ctd chemicals exists
    exists_ctd_chemicals_already_in_neo4j = False

    # chck if chemicals are already in neo4j
    query = '''MATCH (n:CTDchemical) RETURN n LIMIT 1 '''
    results = g.run(query)
    result = results.evaluate()
    action_value = ''
    # depending if chemicals are in neo4j or not the nodes need to be merged or created
    if not result is None:
        exists_ctd_chemicals_already_in_neo4j = True
        action_value = 'Merge'
    else:
        action_value = 'Create'

    # add the chemical nodes to cypher file
    with open('ctd_data/CTD_chemicals.csv') as csvfile:
        reader = csv.reader(csvfile)
        i = 0
        for row in reader:

            if i > 28:
                name = row[0]
                chemical_id = row[1]
                casrn = row[2]
                definition = row[3]
                parent_ids = row[4].split('|')
                parent_ids = '","'.join(parent_ids)
                treenumbers = row[5].split('|')
                treenumbers = '","'.join(treenumbers)
                parenttreenumbers = row[6].split('|')
                parenttreenumbers = '","'.join(parenttreenumbers)
                synonyms = row[7].split('|')
                synonyms = '","'.join(synonyms)
                drugbank_ids = row[8].split('|')
                drugbank_ids = '","'.join(drugbank_ids)

                if exists_ctd_chemicals_already_in_neo4j:
                    query = action_value + ''' (c:CTDchemical{ chemical_id:"%s" }) On Create Set c.casRN="%s", c.synonyms=["%s"], c.drugBankIDs=["%s"], c.parentIDs=["%s"], c.parentTreeNumbers=["%s"], c.treeNumbers=["%s"], c.definition="%s", c.name="%s" On Match Set c.casRN="%s", c.synonyms=["%s"], c.drugBankIDs=["%s"], c.parentIDs=["%s"], c.parentTreeNumbers=["%s"], c.treeNumbers=["%s"], c.definition="%s", c.name="%s";\n'''
                    query = query % (
                        chemical_id, casrn, synonyms, drugbank_ids, parent_ids, parenttreenumbers, treenumbers,
                        definition, name, casrn, synonyms, drugbank_ids, parent_ids, parenttreenumbers, treenumbers,
                        definition, name)
                else:
                    query = action_value + ''' (c:CTDchemical{casRN:"%s", chemical_id:"%s", synonyms:["%s"], drugBankIDs:["%s"], parentIDs:["%s"], parentTreeNumbers:["%s"], treeNumbers:["%s"], definition:"%s", name:"%s"  });\n'''
                    query = query % (
                        casrn, chemical_id, synonyms, drugbank_ids, parent_ids, parenttreenumbers, treenumbers,
                        definition, name)
                cypher_file_nodes.write(query)
                counter_nodes_queries += 1
                check_for_commit_or_file_break(cypher_file_nodes, node_file_number, 'nodes_', counter_nodes_queries)

            i += 1

    # if chemicals sre not in neo4j the id need to be unique
    if not exists_ctd_chemicals_already_in_neo4j:
        cypher_file_nodes.write('commit\nbegin\n')
        cypher_file_nodes.write('Create Constraint On (node:CTDchemical) Assert node.chemical_id Is Unique;\n')
    cypher_file_nodes.write('commit\nbegin\n')


'''
load ctd disease file and generate cypher file for the nodes with properties:
    0:DiseaseName
    1:DiseaseID
    2:AltDiseaseIDs
    3:Definition
    4:ParentIDs
    5:TreeNumbers
    6:ParentTreeNumbers
    7:Synonyms
    8:SlimMappings
furthermore it test if already nodes are in Neo4j and only add the new ones 
'''


def load_disease_and_add_to_cypher_file():
    global counter_nodes_queries, cypher_file_nodes
    # say if in neo4j already ctd chemicals exists
    exists_ctd_disease_already_in_neo4j = False

    # chck if chemicals are already in neo4j
    query = '''MATCH (n:CTDdisease) RETURN n LIMIT 1 '''
    results = g.run(query)
    result = results.evaluate()
    action_value = ''
    # depending if chemicals are in neo4j or not the nodes need to be merged or created
    if not result is None:
        exists_ctd_disease_already_in_neo4j = True
        action_value = 'Merge'
    else:
        action_value = 'Create'

    # add the chemical nodes to cypher file
    with open('ctd_data/CTD_diseases.csv') as csvfile:
        reader = csv.reader(csvfile)
        i = 0
        for row in reader:

            if i > 28:
                name = row[0]
                disease_id = row[1].split(':')
                id_type = disease_id[0]
                disease_id = disease_id[1]
                alt_disease_ids = row[2].split('|')
                alt_disease_ids = '","'.join(alt_disease_ids)
                definition = row[3]
                parent_ids = row[4].split('|')
                parent_ids = '","'.join(parent_ids)
                treenumbers = row[5].split('|')
                treenumbers = '","'.join(treenumbers)
                parenttreenumbers = row[6].split('|')
                parenttreenumbers = '","'.join(parenttreenumbers)
                synonyms = row[7].split('|')
                synonyms = '","'.join(synonyms)
                slimmappings = row[8].split('|')
                slimmappings = '","'.join(slimmappings)

                if exists_ctd_disease_already_in_neo4j:
                    query = action_value + ''' (c:CTDdisease{ disease_id:"%s"}) On Create Set c.altDiseaseIDs=["%s"], c.idType="%s" , c.synonyms=["%s"], c.slimMappings=["%s"], c.parentIDs=["%s"], c.parentTreeNumbers=["%s"], c.treeNumbers=["%s"], c.definition="%s", c.name="%s"  On Match Set c.altDiseaseIDs=["%s"] , c.synonyms=["%s"], c.slimMappings=["%s"], c.parentIDs=["%s"], c.parentTreeNumbers=["%s"], c.treeNumbers=["%s"], c.definition="%s", c.name="%s";\n'''
                    query = query % (
                        disease_id, alt_disease_ids, id_type, synonyms, slimmappings, parent_ids, parenttreenumbers,
                        treenumbers, definition, name, alt_disease_ids, synonyms, slimmappings, parent_ids,
                        parenttreenumbers,
                        treenumbers, definition, name)
                else:
                    query = action_value + ''' (c:CTDdisease{altDiseaseIDs:["%s"], idType:"%s", disease_id:"%s", synonyms:["%s"], slimMappings:["%s"], parentIDs:["%s"], parentTreeNumbers:["%s"], treeNumbers:["%s"], definition:"%s", name:"%s"  });\n'''
                    query = query % (
                        alt_disease_ids, id_type, disease_id, synonyms, slimmappings, parent_ids, parenttreenumbers,
                        treenumbers, definition, name)
                cypher_file_nodes.write(query)
                counter_nodes_queries += 1
                check_for_commit_or_file_break(cypher_file_nodes, node_file_number, 'nodes_', counter_nodes_queries)
            i += 1

    # if chemicals sre not in neo4j the id need to be unique
    if not exists_ctd_disease_already_in_neo4j:
        cypher_file_nodes.write('commit\nbegin\n')
        cypher_file_nodes.write('Create Constraint On (node:CTDdisease) Assert node.disease_id Is Unique;\n')
    cypher_file_nodes.write('commit\nbegin\n')


'''
load ctd pathway file and generate cypher file for the nodes with properties:
    0:PathwayName
    1:PathwayID
furthermore it test if already nodes are in Neo4j and only add the new ones 
'''


def load_pathway_and_add_to_cypher_file():
    global counter_nodes_queries, cypher_file_nodes
    # say if in neo4j already ctd chemicals exists
    exists_ctd_pathway_already_in_neo4j = False

    # chck if chemicals are already in neo4j
    query = '''MATCH (n:CTDpathway) RETURN n LIMIT 1 '''
    results = g.run(query)
    result = results.evaluate()
    action_value = ''
    # depending if chemicals are in neo4j or not the nodes need to be merged or created
    if not result is None:
        exists_ctd_pathway_already_in_neo4j = True
        action_value = 'Merge'
    else:
        action_value = 'Create'

    # add the chemical nodes to cypher file
    with open('ctd_data/CTD_pathways.csv') as csvfile:
        reader = csv.reader(csvfile)
        i = 0
        for row in reader:

            if i > 28:
                name = row[0]
                pathway_id = row[1].split(':')
                id_type = pathway_id[0]
                pathway_id = pathway_id[1]
                if exists_ctd_pathway_already_in_neo4j:
                    query = action_value + ''' (c:CTDpathway{ pathway_id:"%s"  }) On Create Set c.idType="%s",c.name="%s" On Match Set c.name="%s" ;\n'''
                    query = query % (pathway_id, id_type, name, name)
                else:
                    query = action_value + ''' (c:CTDpathway{idType:"%s", pathway_id:"%s", name:"%s"  });\n'''
                    query = query % (id_type, pathway_id, name)
                cypher_file_nodes.write(query)
                counter_nodes_queries += 1
                check_for_commit_or_file_break(cypher_file_nodes, node_file_number, 'nodes_', counter_nodes_queries)
            i += 1

    # if chemicals sre not in neo4j the id need to be unique
    if not exists_ctd_pathway_already_in_neo4j:
        cypher_file_nodes.write('commit\nbegin\n')
        cypher_file_nodes.write('Create Constraint On (node:CTDpathway) Assert node.pathway_id Is Unique;\n')
    cypher_file_nodes.write('commit\nbegin\n')


# dictionary for genesymbol to gene id
dict_gene_symbol_to_gene_id = {}

'''
load ctd genes file and generate cypher file for the nodes with properties:
    0:GeneSymbol
    1:GeneName
    2:GeneID: NCBI-ID
    3:AltGeneIDs
    4:Synonyms
    5:BioGRIDIDs
    6:PharmGKBIDs
    7:UniProtIDs
furthermore it test if already nodes are in Neo4j and only add the new ones 
'''


def load_gene_and_add_to_cypher_file():
    global counter_nodes_queries, cypher_file_nodes
    # say if in neo4j already ctd chemicals exists
    exists_ctd_gene_already_in_neo4j = False

    # chck if chemicals are already in neo4j
    query = '''MATCH (n:CTDgene) RETURN n LIMIT 1 '''
    results = g.run(query)
    result = results.evaluate()
    action_value = ''
    # depending if chemicals are in neo4j or not the nodes need to be merged or created
    if not result is None:
        exists_ctd_gene_already_in_neo4j = True
        action_value = 'Merge'
    else:
        action_value = 'Create'

    # add the chemical nodes to cypher file
    with open('ctd_data/CTD_genes.csv') as csvfile:
        reader = csv.reader(csvfile)
        i = 0
        for row in reader:

            if i > 28:
                gene_symbol = row[0]
                name = row[1]
                gene_id = row[2]
                alt_gene_ids = row[3].split('|')
                alt_gene_ids = '","'.join(alt_gene_ids)
                synonyms = row[4].split('|')
                synonyms = '","'.join(synonyms)
                biogrid_ids = row[5].split('|')
                biogrid_ids = '","'.join(biogrid_ids)
                pharmgkb_ids = row[6].split('|')
                pharmgkb_ids = '","'.join(pharmgkb_ids)
                uniprot_ids = row[7].split('|')
                uniprot_ids = '","'.join(uniprot_ids)

                dict_gene_symbol_to_gene_id[gene_symbol] = gene_id

                if exists_ctd_gene_already_in_neo4j:
                    query = action_value + ''' (c:CTDgene{ gene_id:"%s" }) On Create Set c.altGeneIDs=["%s"], c.synonyms=["%s"], c.bioGRIDIDs=["%s"], c.pharmGKBIDs=["%s"], c.uniProtIDs=["%s"],  c.geneSymbol="%s", c.name="%s" On Match Set c.altGeneIDs=["%s"], c.synonyms=["%s"], c.bioGRIDIDs=["%s"], c.pharmGKBIDs=["%s"], c.uniProtIDs=["%s"],  c.geneSymbol="%s", c.name="%s" ;\n'''
                    query = query % (
                        gene_id, alt_gene_ids, synonyms, biogrid_ids, pharmgkb_ids, uniprot_ids, gene_symbol, name,
                        alt_gene_ids, synonyms, biogrid_ids, pharmgkb_ids, uniprot_ids, gene_symbol, name)
                else:
                    query = action_value + ''' (c:CTDgene{altGeneIDs:["%s"],  gene_id:"%s", synonyms:["%s"], bioGRIDIDs:["%s"], pharmGKBIDs:["%s"], uniProtIDs:["%s"],  geneSymbol:"%s", name:"%s"  });\n'''
                    query = query % (
                        alt_gene_ids, gene_id, synonyms, biogrid_ids, pharmgkb_ids, uniprot_ids, gene_symbol, name)
                cypher_file_nodes.write(query)
                counter_nodes_queries += 1
                check_for_commit_or_file_break(cypher_file_nodes, node_file_number, 'nodes_', counter_nodes_queries)
            i += 1

    # if chemicals sre not in neo4j the id need to be unique
    if not exists_ctd_gene_already_in_neo4j:
        cypher_file_nodes.write('commit\nbegin\n')
        cypher_file_nodes.write('Create Constraint On (node:CTDgene) Assert node.gene_id Is Unique;\n')
    cypher_file_nodes.write('commit\nbegin\n')

    print(len(dict_gene_symbol_to_gene_id))


# dictionary for GO with values 0:name,  1:ontology, 2:HighestGOLevel
dict_Go_properties = {}

# dictionary with (chemical_id, go_id) and properties as value PValue,CorrectedPValue,TargetMatchQty,TargetTotalQty,BackgroundMatchQty,BackgroundTotalQty
dict_chemical_go = {}

'''
load ctd chemicals-go enriched file:
    0:ChemicalName
    1:ChemicalID
    2:CasRN
    3:Ontology
    4:GOTermName
    5:GOTermID
    6:HighestGOLevel
    7:PValue
    8:CorrectedPValue
    9:TargetMatchQty
    10:TargetTotalQty
    11:BackgroundMatchQty
    12:BackgroundTotalQty
and gather the information
'''


def load_chemical_go_enriched():
    # gather information from CTD chemical-go enriched
    with open('ctd_data/CTD_chem_go_enriched.csv') as csvfile:
        reader = csv.reader(csvfile)
        i = 0
        for row in reader:

            if i > 28:
                chemical_id = row[0]
                ontology = row[3]
                goTermName = row[4]
                goTermId = row[5]
                highestGOLevel = row[6]
                pValue = row[7]
                correctedPValue = row[8]
                targetMatchQty = row[9]
                targetTotalQty = row[10]
                backgroundMatchQty = row[11]
                backgroundTotalQty = row[12]

                if not goTermId in dict_Go_properties:
                    dict_Go_properties[goTermId] = [goTermName, ontology, highestGOLevel]

                dict_chemical_go[(chemical_id, goTermId)] = [pValue, correctedPValue, targetMatchQty,
                                                             targetTotalQty, backgroundMatchQty, backgroundTotalQty]

            i += 1

    print(len(dict_Go_properties))


# dictionary with (disease_id, go_id) and properties as value inferenceGeneSymbol, inference GeneQty
dict_disease_go = {}

# list of gene-go pairs
list_gene_go = []

'''
gather information from disease-go infernce
'''


def gather_information_from_disease_go_inferencen(file, ontology):
    with open('ctd_data/' + file) as csvfile:
        reader = csv.reader(csvfile)
        i = 0
        for row in reader:

            if i > 28:
                disease_id = row[1]
                goName = row[2]
                goId = row[3]
                inferenceGeneQty = row[4]
                inferenceGeneSymbols = row[5].split('|')

                if not goId in dict_Go_properties:
                    dict_Go_properties[goId] = [goName, ontology, '']

                dict_disease_go[(disease_id, goId)] = [inferenceGeneSymbols, inferenceGeneQty]

                for gene_symbol in inferenceGeneSymbols:
                    gene_id = dict_gene_symbol_to_gene_id[gene_symbol]
                    if (gene_id, goId) not in list_gene_go:
                        list_gene_go.append((gene_id, goId))
                if i % 20000 == 0:
                    print(i)

            i += 1


'''
load ctd disease-go enriched files for biological process, molecular function and cellular componenet
    0:DiseaseName
    1:DiseaseID
    2:GOName
    3:GOID
    4:InferenceGeneQty
    5:InferenceGeneSymbols
gather the information
'''


def load_disease_go_inference():
    print('start Cellular Component')
    print(datetime.datetime.utcnow())
    gather_information_from_disease_go_inferencen('CTD_Disease-GO_cellular_component_associations.csv',
                                                  'Cellular Component')
    print('start Molecular Function')
    print(datetime.datetime.utcnow())
    gather_information_from_disease_go_inferencen('CTD_Disease-GO_molecular_function_associations.csv',
                                                  'Molecular Function')
    print('start Biological Process')
    print(datetime.datetime.utcnow())
    gather_information_from_disease_go_inferencen('CTD_Disease-GO_biological_process_associations.csv',
                                                  'Biological Process')

    print(len(dict_Go_properties))


'''
Add GO to the node cypher file
'''


def add_go_to_cypher_file():
    global counter_nodes_queries, cypher_file_nodes
    # say if in neo4j already ctd chemicals exists
    exists_ctd_go_already_in_neo4j = False

    # chck if chemicals are already in neo4j
    query = '''MATCH (n:CTDGO) RETURN n LIMIT 1 '''
    results = g.run(query)
    result = results.evaluate()
    action_value = ''
    # depending if chemicals are in neo4j or not the nodes need to be merged or created
    if not result is None:
        exists_ctd_gene_already_in_neo4j = True
        action_value = 'Merge'
    else:
        action_value = 'Create'

    # add the go nodes to cypher file
    for go_id, [name, ontology, highestGOLevel] in dict_Go_properties.items():

        if exists_ctd_go_already_in_neo4j:
            query = action_value + ''' (c:CTDGO{ go_id:"%s" }) On Create Set c.ontology="%s", c.highestGOLevel="%s", c.name="%s" On Match Set c.ontology="%s", c.highestGOLevel="%s", c.name="%s" ;\n'''
            query = query % (
                go_id, ontology, highestGOLevel, name, ontology, highestGOLevel, name)
        else:
            query = action_value + ''' (c:CTDGO{ go_id:"%s", ontology:"%s", highestGOLevel:"%s", name:"%s"});\n'''
            query = query % (go_id, ontology, highestGOLevel, name)
        cypher_file_nodes.write(query)
        counter_nodes_queries += 1
        check_for_commit_or_file_break(cypher_file_nodes, node_file_number, 'nodes_', counter_nodes_queries)

    # if chemicals sre not in neo4j the id need to be unique
    if not exists_ctd_go_already_in_neo4j:
        cypher_file_nodes.write('commit\nbegin\n')
        cypher_file_nodes.write('Create Constraint On (node:CTDGO) Assert node.go_id Is Unique;\n')
    cypher_file_nodes.write('commit\nbegin\n')


'''
add chemical-go relationship to cypher file
'''


def chemical_go_into_cypher_file():
    global counter_edges_queries, cypher_file_edges, edges_file_number
    for (chemical_id, go_id), [pValue, correctedPValue, targetMatchQty, targetTotalQty, backgroundMatchQty,
                               backgroundTotalQty] in dict_chemical_go.items():
        # check if unbiased true or false
        query = '''Match (c:CTDchemical{ chemical_id:"%s" }), (g:CTDGO{ go_id:"%s" }) Merge (c)-[a:affects]->(g) On Create Set a.unbiased=True, a.pValue="%s", a.correctedPValue="%s", a.targetMatchQty="%s", a.targetTotalQty="%s", a.backgroundMatchQty="%s", c.backgroundTotalQty="%s" On Match Set a.unbiased=True, a.pValue="%s", a.correctedPValue="%s", a.targetMatchQty="%s", a.targetTotalQty="%s", a.backgroundMatchQty="%s", c.backgroundTotalQty="%s";\n'''
        query = query % (chemical_id, go_id, pValue, correctedPValue, targetMatchQty, targetTotalQty, backgroundMatchQty,
                         backgroundTotalQty)

        cypher_file_edges.write(query)
        counter_edges_queries += 1
        check_for_commit_or_file_break(cypher_file_edges, edges_file_number, 'edges_', counter_edges_queries)

'''
add disease-go relationship to cypher file
'''


def disease_go_into_cypher_file():
    global counter_edges_queries, cypher_file_edges, edges_file_number
    for (disease_id, go_id), [inferenceGeneSymbols, inferenceGeneQty] in dict_disease_go.items():
        # check if unbiased true or false
        query = '''Match (d:CTDdisease{ disease_id:"%s"}), (g:CTDGO{ go_id:"%s" }) Merge (d)-[a:associates]->(g) On Create Set a.unbiased=True, a.inferenceGeneSymbols="%s", a.inferenceGeneQty="%s" On Match Set a.unbiased=True, a.inferenceGeneSymbols="%s", a.inferenceGeneQty="%s";\n'''
        query = query % (disease_id, go_id, inferenceGeneSymbols, inferenceGeneQty, inferenceGeneSymbols, inferenceGeneQty)

        cypher_file_edges.write(query)
        counter_edges_queries += 1
        check_for_commit_or_file_break(cypher_file_edges, edges_file_number, 'edges_', counter_edges_queries)

'''
add gene-go relationship to cypher file
'''


def gene_go_into_cypher_file():
    global counter_edges_queries, cypher_file_edges, edges_file_number
    for (gene_id, go_id)in list_gene_go:
        # check if unbiased true or false
        query = '''Match (c:CTDgene{ gene_id:"%s" }), (g:CTDGO{ go_id:"%s" }) Merge (d)-[a:associates]->(g) ;\n'''
        query = query % (gene_id, go_id)

        cypher_file_edges.write(query)
        counter_edges_queries += 1
        check_for_commit_or_file_break(cypher_file_edges, edges_file_number, 'edges_', counter_edges_queries)

def main():
    print(datetime.datetime.utcnow())

    print('##########################################################################')

    print(datetime.datetime.utcnow())
    print('connection to db')
    database_connection()

    print('##########################################################################')

    print(datetime.datetime.utcnow())
    print('load in ctd chemical and add to cypher file')

    load_chemicals_and_add_to_cypher_file()

    print('##########################################################################')

    print(datetime.datetime.utcnow())
    print('load in ctd disease and add to cypher file')

    load_disease_and_add_to_cypher_file()

    print('##########################################################################')

    print(datetime.datetime.utcnow())
    print('load in ctd pathway and add to cypher file')

    load_pathway_and_add_to_cypher_file()

    print('##########################################################################')

    print(datetime.datetime.utcnow())
    print('load in ctd gene and add to cypher file')

    load_gene_and_add_to_cypher_file()

    print('##########################################################################')

    print(datetime.datetime.utcnow())
    print('load in ctd chemical-go and gather the information')

    load_chemical_go_enriched()

    print('##########################################################################')

    print(datetime.datetime.utcnow())
    print('load in ctd disease-go and gather the information')

    load_disease_go_inference()

    print('##########################################################################')

    print(datetime.datetime.utcnow())
    print('add go to node cypher file')

    add_go_to_cypher_file()

    print('##########################################################################')

    print(datetime.datetime.utcnow())
    print('add chemical-go relationship to cypher file')

    chemical_go_into_cypher_file()

    print('##########################################################################')

    print(datetime.datetime.utcnow())
    print('add disease-go relationship to cypher file')

    disease_go_into_cypher_file()

    print('##########################################################################')

    print(datetime.datetime.utcnow())
    print('add gene-go relationship to cypher file')

    gene_go_into_cypher_file()

    print('##########################################################################')

    print(datetime.datetime.utcnow())


if __name__ == "__main__":
    # execute only if run as a script
    main()