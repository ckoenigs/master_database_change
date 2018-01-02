# -*- coding: utf-8 -*-
"""
Created on Wed Apr 19 18:07:14 2017

@author: Cassandra
"""

import datetime
import sys

# path to data 
if len(sys.argv) > 1:
    # for windows
    filepath = "file:///" + sys.argv[1]
    # for linux
    filepath= sys.argv[1]
else:
    # filepath="file:///c:/Users/Cassandra/Documents/uni/Master/test/"
    filepath = "c:/Users/Cassandra/Documents/uni/Master/test/"


class SideEffect(object):
    """
    Attribute:
        umlsIDlable: string
        name: string
        meddraType: string (PT= preferred term or LLT= low level term)
        umlsIDmeddra: string (is key id)
        conceptName: string
    """

    def __init__(self, umlsIDlable, meddraType, umlsIDmeddra, name):
        self.umlsIDlable = umlsIDlable
        self.name = name
        self.meddraType = meddraType
        self.umlsIDmeddra = umlsIDmeddra
        self.conceptName = ''

    def set_conceptName(self, conceptName):
        self.conceptName = conceptName


# a dictionary with umlsID is key and the whole side effect is his value.
dict_sideEffects = {}


class Drug(object):
    """
    Attribute:
        stitchIDflat: string
        stitchIDstereo: string (key id)
        PubChemID: int
    """

    def __init__(self, stitchIDflat, stitchIDstereo):
        self.stitchIDflat = stitchIDflat
        self.stitchIDstereo = stitchIDstereo
        self.PubChemID = str(int(stitchIDstereo[3:]))


# a dictionary with stitch stereo ID  as key and whole drug as value
dict_drug = {}


class Edge(object):
    """
    Attribute:
        drugID: stitch stereo iD
        sideEffectID. UMLS ID meddra
        placebo: string ('' or palcebo)
        freq: frequence: string (words or floats or from ... to ...)
        lowerFreq: string (float)
        upperFreq: string (float)
        methodDetection: string
        placeboLowerFreq: string (float)
        placeboUpperFreq: string (float)
        placeboFreq: string (float)
    """

    def __init__(self, drugID, sideEffectID):
        self.drugID = drugID
        self.sideEffectID = sideEffectID
        self.placebo = ''
        self.freq = []
        self.lowerFreq = []
        self.upperFreq = []
        self.placeboFreq = []
        self.placeboLowerFreq = []
        self.placeboUpperFreq = []

    def set_frequence(self, placebo, freq, lowerFreq, upperFreq):
        self.placebo = placebo
        if len(placebo) > 0:
            self.placeboFreq.append(freq)
            self.placeboLowerFreq.append(float(lowerFreq))
            self.placeboUpperFreq.append(float(upperFreq))
        else:
            self.freq.append(freq)
            self.lowerFreq.append(float(lowerFreq))
            self.upperFreq.append(float(upperFreq))

    def set_methodDetection(self, methodDetection):
        self.methodDetection = methodDetection


# a dictionary with (drugID (stitch stereo id), side effect ID (umls cui)) as key and edge as value
dict_edges = {}

# dictionary of umls cuis where the umls id label is used because there was no meddra umls cui
dict_cui_which_use_label_id = {}

# dictionary of stitch flat with all stitch stereo ids as values
dict_flat_to_list_stereo = {}

'''
import meddra_all_se.tsv in dictionary
properties:
# 1/2: STITCH compund IDs (flat/stereo)
# 3: UMLS concept ID (on lable)
# 4: MedDRA concept type
# 5: UMLS concept id (MedDRA term)
# 6: Side effect name
'''


def import_meddra_all_se():
    fobj = open(filepath + "meddra_all_se.tsv")
    for line in fobj:
        splitted = line.split('\t')
        stitchIDflat = splitted[0]
        stitchIDstereo = splitted[1]
        umlsIDlable = splitted[2]
        meddraType = splitted[3]
        umlsIDmeddra = splitted[4]
        name = splitted[5].replace('\n', '')

        # fill the dictionary with stitch flat id as key and add the different stitch stereo IDs
        if stitchIDflat in dict_flat_to_list_stereo:
            if not stitchIDstereo in dict_flat_to_list_stereo[stitchIDflat]:
                dict_flat_to_list_stereo[stitchIDflat].append(stitchIDstereo)
        else:
            dict_flat_to_list_stereo[stitchIDflat] = [stitchIDstereo]

        # generate drug and add to dictionary
        if not stitchIDstereo in dict_drug:
            drug = Drug(stitchIDflat, stitchIDstereo)
            dict_drug[stitchIDstereo] = drug

        # if the side effect has no UMLS ID for meddera use the UMLS ID for lable
        if len(umlsIDmeddra) == 0:
            if not umlsIDlable in dict_cui_which_use_label_id:
                dict_cui_which_use_label_id[umlsIDlable] = name
            umlsIDmeddra = umlsIDlable

        # generate side effect and add to list of side effects if not existing
        sideEffect = SideEffect(umlsIDlable, meddraType, umlsIDmeddra, name)
        if not umlsIDmeddra in dict_sideEffects:
            dict_sideEffects[umlsIDmeddra] = sideEffect
        else:
            # if the existing SE has not the prefered nam take the prefered name
            if meddraType == 'PT':
                if dict_sideEffects[umlsIDmeddra].meddraType != 'PT':
                    dict_sideEffects[umlsIDmeddra] = sideEffect

        # generate the edge and add to dictionary
        edge = Edge(stitchIDstereo, umlsIDmeddra)
        dict_edges[(stitchIDstereo, umlsIDmeddra)] = edge

    fobj.close()


'''
import meddra_freq.tsv and add information into the dictionaries
# 1/2: STITCH compund IDs (flat/stereo)
# 3: UMLS concept ID (on lable)
# 4: placebo
# 5: frequency description
# 6/7: lower/upper bound on frequency 
# 8: MedDRA concept type
# 9: UMLS concept id (MedDRA term)
# 10: Side effect name 
'''


def import_meddra_freq():
    fobj = open(filepath + "meddra_freq.tsv")
    for line in fobj:
        splitted = line.split('\t')
        stitchIDflat = splitted[0]
        stitchIDstereo = splitted[1]
        umlsIDlable = splitted[2]
        placebo = splitted[3]
        freq = splitted[4]
        lowerFreq = splitted[5]
        upperFreq = splitted[6]
        meddraType = splitted[7]
        umlsIDmeddra = splitted[8]
        name = splitted[9].replace('\n', '')

        # fill the dictionary with stitch flat id as key and add the different stitch stereo IDs
        if stitchIDflat in dict_flat_to_list_stereo:
            if not stitchIDstereo in dict_flat_to_list_stereo[stitchIDflat]:
                dict_flat_to_list_stereo[stitchIDflat].append(stitchIDstereo)
        else:
            dict_flat_to_list_stereo[stitchIDflat] = [stitchIDstereo]

        # generate drug and add to dictionary
        if not stitchIDstereo in dict_drug:
            drug = Drug(stitchIDflat, stitchIDstereo)
            dict_drug[stitchIDstereo] = drug

        # if the side effect has no UMLS ID for meddera use the UMLS ID for lable
        if len(umlsIDmeddra) == 0:
            if not umlsIDlable in dict_cui_which_use_label_id:
                dict_cui_which_use_label_id[umlsIDlable] = name
            umlsIDmeddra = umlsIDlable

        # generate side effect and add to list of side effects if not existing
        sideEffect = SideEffect(umlsIDlable, meddraType, umlsIDmeddra, name)
        if not umlsIDmeddra in dict_sideEffects:
            dict_sideEffects[umlsIDmeddra] = sideEffect
        else:
            # if the existing SE has not the prefered nam take the prefered name
            if meddraType == 'PT':
                if dict_sideEffects[umlsIDmeddra].meddraType != 'PT':
                    dict_sideEffects[umlsIDmeddra] = sideEffect

        # generate the edge and add to dictionary if not existing, also add the properties for frequence
        if not (stitchIDstereo, umlsIDmeddra) in dict_edges:
            edge = Edge(stitchIDstereo, umlsIDmeddra)
            edge.set_frequence(placebo, freq, lowerFreq, upperFreq)
            dict_edges[(stitchIDstereo, umlsIDmeddra)] = edge
        else:
            dict_edges[(stitchIDstereo, umlsIDmeddra)].set_frequence(placebo, freq, lowerFreq, upperFreq)


'''
import meddra_all_lable_indications.tsv and add information into dictionaries
# 1: source labelindication
# 2: STITCH compund IDs (flat)
# 3: STITCH compund IDs (stereo) 
# 4: UMLS concept ID (on lable)
# 5: method of detection: NLP_indication / NLP_precondition / text_mention
# 6: concept name
# 7: MedDRA concept type
# 8: UMLS concept id (MedDRA term)
# 9: MedDRA concept name   
'''


def import_meddra_all_lable_indication():
    fobj = open(filepath + "meddra_all_label_indications.tsv")
    for line in fobj:
        splitted = line.split('\t')
        sourceLableIndi = splitted[0]
        stitchIDflat = splitted[1]
        stitchIDstereo = splitted[2]
        umlsIDlable = splitted[3]
        methodDetection = splitted[4]
        meddraType = splitted[6]
        umlsIDmeddra = splitted[7]
        name = splitted[8].replace('\n', '')

        # fill the dictionary with stitch flat id as key and add the different stitch stereo IDs
        if stitchIDflat in dict_flat_to_list_stereo:
            if not stitchIDstereo in dict_flat_to_list_stereo[stitchIDflat]:
                dict_flat_to_list_stereo[stitchIDflat].append(stitchIDstereo)
        else:
            dict_flat_to_list_stereo[stitchIDflat] = [stitchIDstereo]

        # generate drug and add to dictionary
        if not stitchIDstereo in dict_drug:
            drug = Drug(stitchIDflat, stitchIDstereo)
            dict_drug[stitchIDstereo] = drug

        # if the side effect has no UMLS ID for meddera use the UMLS ID for lable
        if len(umlsIDmeddra) == 0:
            if not umlsIDlable in dict_cui_which_use_label_id:
                dict_cui_which_use_label_id[umlsIDlable] = name
            umlsIDmeddra = umlsIDlable

        # generate side effect and add to list of side effects if not existing
        sideEffect = SideEffect(umlsIDlable, meddraType, umlsIDmeddra, name)
        if not umlsIDmeddra in dict_sideEffects:
            dict_sideEffects[umlsIDmeddra] = sideEffect
        else:
            # if the existing SE has not the prefered nam take the prefered name
            if meddraType == 'PT':
                if dict_sideEffects[umlsIDmeddra].meddraType != 'PT':
                    dict_sideEffects[umlsIDmeddra] = sideEffect

        # generate the edge and add to dictionary  if not existing and app property method detection
        if not (stitchIDstereo, umlsIDmeddra) in dict_edges:
            edge = Edge(stitchIDstereo, umlsIDmeddra)
            edge.set_methodDetection(methodDetection)
            dict_edges[(stitchIDstereo, umlsIDmeddra)] = edge

        else:
            dict_edges[(stitchIDstereo, umlsIDmeddra)].set_methodDetection(methodDetection)

        dict_edges[(stitchIDstereo, umlsIDmeddra)].set_methodDetection(sourceLableIndi)  

'''
import meddra_all_indications.tsv and add information into dictionaries
# 1: STITCH compund IDs (flat)
# 2: UMLS concept ID (on lable)
# 3: method of detection: NLP_indication / NLP_precondition / text_mention
# 4: concept name
# 5: MedDRA concept type
# 6: UMLS concept id (MedDRA term)
# 7: MedDRA concept name 
'''
def import_meddra_all_indication():
    fobj = open(filepath + "meddra_all_indications.tsv")
    counter = 0
    for line in fobj:
        splitted = line.split('\t')
        stitchIDflat = splitted[0]
        umlsIDlable = splitted[1]
        conceptName = splitted[3]
        meddraType = splitted[4]
        umlsIDmeddra = splitted[5]
        name = splitted[6].replace('\n', '')


        # if the side effect has no UMLS ID for meddera use the UMLS ID for lable
        if len(umlsIDmeddra) == 0:
            if not umlsIDlable in dict_cui_which_use_label_id:
                dict_cui_which_use_label_id[umlsIDlable] = name
            umlsIDmeddra = umlsIDlable
        se = SideEffect(umlsIDlable, meddraType, umlsIDmeddra, name)

        # generate side effect and add to list of side effects if not existing
        if not umlsIDmeddra in dict_sideEffects:
            se.set_conceptName(conceptName)
            dict_sideEffects[umlsIDmeddra] = se
        else:
            # if the existing SE has not the prefered nam take the prefered name
            if meddraType == 'PT' and dict_sideEffects[umlsIDmeddra].meddraType != 'PT':
                se.set_conceptName(conceptName)
                dict_sideEffects[umlsIDmeddra] = se
            else:
                dict_sideEffects[umlsIDmeddra].set_conceptName(conceptName)

        # for all stitch stereo ID of a stitch flat ID generate the connection
        if stitchIDflat in dict_flat_to_list_stereo:
            list_stereo_ids = dict_flat_to_list_stereo[stitchIDflat]

            for stitchIDstereo in list_stereo_ids:
                # generate the edge and add to dictionary
                if not (stitchIDstereo, umlsIDmeddra) in dict_edges:
                    edge = Edge(stitchIDstereo, umlsIDmeddra)
                    # edge.set_methodDetection(methodDetection)
                    dict_edges[(stitchIDstereo, umlsIDmeddra)] = edge

        else:
            counter += 1
            print('some flat are not in the other files!')
    print(counter)


'''
generate a file with all side effects which has no umls id meddra and use the umls id label
'''


def generate_file_umls_id_label():
    g = open('Sider_cuis_which_are_from_umlsIdLabel.tsv', 'w')
    g.write('umlsIdLabel \t name \n')
    for cui, name in dict_cui_which_use_label_id.items():
        g.write(cui + '\t' + name + '\n')


'''
Generate cypher file for import in neo4j
'''


def generate_cypher_file():
    i = 1
    # number of queries for a commit block
    constrain_number = 20000

    # number of quereies in a file
    creation_max_in_file = 1000000

    f = open('Sider_database_' + str(i) + '.cypher', 'w', encoding="utf-8")
    f.write('begin \n')
    i += 1

    # first add all queries with sider drugs
    counter_create = 0
    print('drug Create')
    print (datetime.datetime.utcnow())
    for key, value in dict_drug.items():
        create_text = 'Create (:drugSider{stitchIDflat: "%s" , stitchIDstereo: "%s", PubChem_Coupound_ID: "%s"} ); \n' % (
            value.stitchIDflat, value.stitchIDstereo, value.PubChemID)
        counter_create += 1
        f.write(create_text)
        if counter_create % constrain_number == 0:
            f.write('commit \n')
            if counter_create % creation_max_in_file == 0:
                f.close()
                f = open('Sider_database_' + str(i) + '.cypher', 'w', encoding="utf-8")
                f.write('begin \n')
                i += 1
            else:
                f.write('begin \n')
    f.write('commit \n begin \n')
    # set stitch stereo ID as key and unique
    f.write('Create Constraint On (node:drugSider) Assert node.stitchIDstereo Is Unique; \n')
    f.write('commit \n schema await \n begin \n')

    # add queries for side effect
    print('side effect Create')
    print (datetime.datetime.utcnow())
    for key, value in dict_sideEffects.items():
        create_text = 'Create (:seSider{meddraType: "%s" , conceptName: "%s", umlsIDmeddra: "%s", name: "%s", umls_concept_id: "%s"} ); \n' % (
            value.meddraType, value.conceptName, value.umlsIDmeddra, value.name, value.umlsIDlable)
        counter_create += 1
        f.write(create_text)
        if counter_create % constrain_number == 0:
            f.write('commit \n')
            if counter_create % creation_max_in_file == 0:
                f.close()
                f = open('Sider_database_' + str(i) + '.cypher', 'w', encoding="utf-8")
                f.write('begin \n')
                i += 1
            else:
                f.write('begin \n')

    f.write('commit \n begin \n')
    # set umlsIDmeddera as key and unique
    f.write('Create Constraint On (node:seSider) Assert node.umlsIDmeddra Is Unique; \n')
    f.write('commit \n schema await \n begin \n')

    # make statistics and add query for relationship to file
    print('edges Create')
    print (datetime.datetime.utcnow())
    # filter out all frequencies with floats and compute average, if no value exist take a word
    for key, value in dict_edges.items():
        freqs = value.freq
        freqs_word = ''
        freqs_value = 0
        # count how often the frequency has a float as value
        counter_values = 0
        for freq in freqs:
            if '<' in freq:
                freqs_word = freq
            elif '%' in freq:
                counter_values += 1
                freq = freq.replace('%', '')
                # all values with from .. to.. and take the average
                if '-' in freq:
                    freq = freq.split('-')
                    freq = (float(freq[0]) + float(freq[1])) / 2
                elif 'to' in freq:
                    freq = freq.split('to')
                    freq = (float(freq[0]) + float(freq[1])) / 2
                # only value
                else:
                    freq = float(freq)
                freqs_value += freq
            # is a word
            else:
                freqs_word = freq
        # take the average if one ore more frequencies exist with a float
        if counter_values > 0:
            freq = str(freqs_value / counter_values) + '%'
        # take the word
        else:
            freq = freqs_word

        # placebo
        # same for palcebo:
        # filter out all frequencies with floats and compute average, if no value exist take a word
        placeboFreqs = value.placeboFreq
        placeboFreqs_word = ''
        placeboFreqs_value = 0
        # count how often the frequency has a float as value
        counter_values = 0
        for pfreq in placeboFreqs:
            if '<' in pfreq:
                placeboFreqs_word = pfreq
            elif '%' in pfreq:
                counter_values += 1
                pfreq = pfreq.replace('%', '')
                # all values with from .. to.. and take the average
                if '-' in pfreq:
                    pfreq = pfreq.split('-')
                    pfreq = (float(pfreq[0]) + float(pfreq[1])) / 2
                elif 'to' in pfreq:
                    pfreq = pfreq.split('to')
                    pfreq = (float(pfreq[0]) + float(pfreq[1])) / 2
                # only word
                else:
                    pfreq = float(pfreq)
                placeboFreqs_value += pfreq
            else:
                placeboFreqs_word = pfreq
        # take the average if one ore more frequencies exist with a float
        if counter_values > 0:
            placeboFreq = str(placeboFreqs_value / counter_values) + '%'
        # take the word
        else:
            placeboFreq = placeboFreqs_word

        # take the min or max of the different frequencies
        lowerFreq = str(min(value.lowerFreq)) if len(value.lowerFreq) > 0 else ''
        upperFreq = str(max(value.upperFreq)) if len(value.upperFreq) > 0 else ''
        placeboLowerFreq = str(min(value.placeboLowerFreq)) if len(value.placeboLowerFreq) > 0 else ''
        placeboUpperFreq = str(max(value.placeboUpperFreq)) if len(value.placeboUpperFreq) > 0 else ''

        create_text = ''' Match (drug:drugSider{stitchIDstereo: "%s"}), (se:seSider{umlsIDmeddra: "%s"})
        Create (drug)-[:Causes{placebo: "%s" , freq: "%s", lowerFreq: "%s", upperFreq: "%s", placeboFreq: "%s", placeboLowerFreq: "%s", placeboUpperFreq: "%s"}] ->(se); \n''' % (
            value.drugID, value.sideEffectID, value.placebo, freq, lowerFreq, upperFreq, placeboFreq, placeboLowerFreq,
            placeboUpperFreq)
        counter_create += 1
        f.write(create_text)
        if counter_create % constrain_number == 0:
            f.write('commit \n')
            if counter_create % creation_max_in_file == 0:
                f.close()
                f = open('Sider_database_' + str(i) + '.cypher', 'w', encoding="utf-8")
                f.write('begin \n')
                i += 1
            else:
                f.write('begin \n')
    f.write('commit')


# DatabaseError: At c:\Users\Cassandra\Documents\uni\Master\test\meddra.tsv:21724 -  there's a field starting with a quote and whereas it ends that quote there seems to be characters in that field after that ending quote. That isn't supported. This is what I read: 'Ventilation"'
# That's why I change "Ventilation" to 'Ventilation'

def main():
    print (datetime.datetime.utcnow())
    print('import meddra_all_se.tsv')


    import_meddra_all_se()

    print('number of drug afte the first file:' + str(len(dict_drug)))

    print('#############################################################')
    print (datetime.datetime.utcnow())
    print('import meddra_freq.tsv')

    import_meddra_freq()

    print(len(dict_drug))

    print('number of drug afte the second file:' + str(len(dict_drug)))

    print('#############################################################')
    print (datetime.datetime.utcnow())
    print('import meddra_all_lable_indication.tsv')

    import_meddra_all_lable_indication()

    print('#############################################################')
    print (datetime.datetime.utcnow())
    print('import meddra_all_indication.tsv')

    import_meddra_all_indication()

    print('number of se in the end' + str(len(dict_sideEffects)))
    print('number of drug in the end:' + str(len(dict_drug)))
    print('number of relationships in the end' + str(len(dict_edges)))

    print('#############################################################')
    print (datetime.datetime.utcnow())
    print('generate file where are cuis use form umlsIdLabel')

    generate_file_umls_id_label()

    print('#############################################################')
    print (datetime.datetime.utcnow())
    print('generate cypher file')
    generate_cypher_file()

    print('#############################################################')
    print (datetime.datetime.utcnow())


if __name__ == "__main__":
    # execute only if run as a script
    main()