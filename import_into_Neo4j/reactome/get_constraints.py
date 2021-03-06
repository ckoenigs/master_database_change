import sys
import datetime
import shelve

sys.path.append("../..")
import create_connection_to_databases

'''
create a connection with neo4j
'''


def create_connection_with_neo4j():
    # set up authentication parameters and connection
    # authenticate("localhost:7474", "neo4j", "test")
    global g
    g = create_connection_to_databases.database_connection_neo4j()


def get_the_constraints_and_write_into_file():
    """
    get all constraint and check if the node exists
    if so write constraint into file
    :return:
    """
    query = '''CALL db.constraints'''

    file_with_constraints = open('constraint.txt', 'w', encoding='utf-8')
    results = g.run(query)
    for index_name, description, in results:
        splitted = description.split(':')
        label = splitted[1].split(' )')[0]
        query = "Match (n:%s) Return n Limit 1;" % (label)
        count_result = g.run(query)
        has_result = count_result.evaluate()
        if has_result is not None:
            print(label)
            print(has_result)
            file_with_constraints.write(description+'\n')
    file_with_constraints.close()


def main():
    print(datetime.datetime.utcnow())

    print('##########################################################################')

    print(datetime.datetime.utcnow())
    print('create connection')

    create_connection_with_neo4j()

    print('##########################################################################')

    print(datetime.datetime.utcnow())
    print('get constraints')

    get_the_constraints_and_write_into_file()

    print('##########################################################################')

    print(datetime.datetime.utcnow())


if __name__ == "__main__":
    # execute only if run as a script
    main()
