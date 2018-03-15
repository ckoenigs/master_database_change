# -*- coding: utf-8 -*-
"""
Created on Wed Feb 14 09:31:43 2018

@author: ckoenigs
"""

from py2neo import Graph, authenticate
import sys
import datetime
reload(sys)
sys.setdefaultencoding("utf-8")

# connect with the neo4j database
def database_connection():

    authenticate("localhost:7474", "neo4j", "test")
    global g
    g = Graph("http://localhost:7474/db/data/")

'''
Generate cypher file with APOC
'''
def generate_cypher_file_with_apoc(save_path):
    # generate cypher file for the most of the mondo nodes with their relationships
    query='''call apoc.export.cypher.query("MATCH (n:disease)-[r]->(b:disease) Where n.`http://www.geneontology.org/formats/oboInOwl#id` contains 'MONDO' and b.`http://www.geneontology.org/formats/oboInOwl#id` contains 'MONDO RETURN n,r,b",'''+save_path+'''mondo.cypher, {batchSize:10000}); '''

    # the only nod that has no connection to another disease node with a mondo id (MONDO:0013239)
    query= '''call apoc.export.cypher.query("MATCH (n:disease) Where n.`http://www.geneontology.org/formats/oboInOwl#id`='MONDO:0013239' Return n",'''+save_path+'''single_node_without_connection.cypher, {batchSize:10}); '''
    g.run(query)


def main():
    print(datetime.datetime.utcnow())

    print('##########################################################################')

    print(datetime.datetime.utcnow())
    print('connection to db')
    database_connection()

    print('##########################################################################')

    print(datetime.datetime.utcnow())
    print('generate cypher file')

    if len(sys.argv)==1:
        generate_cypher_file_with_apoc(sys.argv[1])
    else:
        print('Need a path as argument to save the cypher file')

    print('##########################################################################')

    print(datetime.datetime.utcnow())



if __name__ == "__main__":
    # execute only if run as a script
    main()