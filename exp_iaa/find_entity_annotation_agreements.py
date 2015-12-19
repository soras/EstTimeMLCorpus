# -*- coding: utf-8 -*- 
#
#    Script for calculating agreements on entity (EVENT, TIMEX) annotations.
#
#    Developed and tested under Python's version: 3.4.1
#
#

import sys, os, re

import data_import
import ia_agreements


def calcEntityAnnotationAgreementsOnFile(fileName, annotators, eventAnnotationsByLoc, \
                                         eventAnnotationsByIds, tmxAnnotationsByLoc, \
                                         tmxAnnotationsByIds, totalCounter):
    ''' Calculates entity annotation agreements (on both extent + specific attributes) 
        between all pairs of annotators that have annotated given file.
        Reports agreements in terms of precision, recall and F-score, and 
        records the results (into totalCounter) for aggregation.
    '''
    print ()
    print ('='*70)
    print (' '*10, fileName)
    print ('='*70)
    print()
    pairs = []
    if (len(annotators) == 2):
        pairs = [ [annotators[0], annotators[1]] ]
    elif (len(annotators) == 3):
        pairs = [ [annotators[0], annotators[1]], \
                  [annotators[1], annotators[2]], \
                  [annotators[0], annotators[2]] ]
    else:
        raise Exception(" Unexpected number of annotators:", len(annotators))
    # Find agreements on entity extents
    allRes = dict()
    for pair in pairs:
        [a, b] = sorted(pair, reverse=('j' in pair))
        eveA = eventAnnotationsByIds[a][fileName] if fileName in eventAnnotationsByIds[a] else {}
        eveB = eventAnnotationsByIds[b][fileName] if fileName in eventAnnotationsByIds[b] else {}
        (res, pairName) = \
            ia_agreements.compAnnotationExtents("EVENT", a, b, eveA, eveB, totalCounter)
        for k in res.keys():
            if (k not in allRes):
               allRes[k] = dict()
            allRes[k][pairName] = res[k]
        tmxA = tmxAnnotationsByIds[a][fileName] if fileName in tmxAnnotationsByIds[a] else {}
        tmxB = tmxAnnotationsByIds[b][fileName] if fileName in tmxAnnotationsByIds[b] else {}
        (res, pairName) = \
            ia_agreements.compAnnotationExtents("TIMEX", a, b, tmxA, tmxB, totalCounter)
        for k in res.keys():
            if (k not in allRes):
               allRes[k] = dict()
            allRes[k][pairName] = res[k]
        
    for k in sorted(allRes.keys()):
        for m in sorted(allRes[k].keys()):
            print (allRes[k][m])
        print()
    # Find agreements on entity attributes
    allRes = dict()
    for pair in pairs:
        [a, b] = sorted(pair, reverse=('j' in pair))
        eveA = eventAnnotationsByIds[a][fileName] if fileName in eventAnnotationsByIds[a] else {}
        eveB = eventAnnotationsByIds[b][fileName] if fileName in eventAnnotationsByIds[b] else {}
        (res, pairName) = \
            ia_agreements.compAnnotationAttribsFscore("EVENT", a, b, eveA, eveB, totalCounter, countOnlyAligned = True)
        for k in res.keys():
            if (k not in allRes):
               allRes[k] = dict()
            allRes[k][pairName] = res[k]
        tmxA = tmxAnnotationsByIds[a][fileName] if fileName in tmxAnnotationsByIds[a] else {}
        tmxB = tmxAnnotationsByIds[b][fileName] if fileName in tmxAnnotationsByIds[b] else {}
        (res, pairName) = \
            ia_agreements.compAnnotationAttribsFscore("TIMEX", a, b, tmxA, tmxB, totalCounter, countOnlyAligned = True)
        for k in res.keys():
            if (k not in allRes):
               allRes[k] = dict()
            allRes[k][pairName] = res[k]
    for k in sorted(allRes.keys()):
        for m in sorted(allRes[k].keys()):
            print (allRes[k][m])
        print()
    print()


# =========================================================================
#    Main program : loading corpus from files and finding agreements
# =========================================================================

if len(sys.argv) > 1 and os.path.isdir(sys.argv[1]):
    corpusDir = sys.argv[1]

    # Load base segmentation, morphological and syntactic annotations
    baseSegmentationFile = os.path.join(corpusDir, data_import.baseAnnotationFile)
    baseAnnotations = data_import.load_base_segmentation(baseSegmentationFile)

    #  Load EVENT and TIMEX annotations of all annotators ...
    eventAnnotationsByLoc, eventAnnotationsByIds, tmxAnnotationsByLoc, \
    tmxAnnotationsByIds = data_import.loadAllEntityAnnotations(corpusDir)
    
    # Names of all corpus files
    allFiles = list(eventAnnotationsByIds['j'].keys())
    # Iterate over all files, calculate IA agreements
    counter = ia_agreements.AggregateCounter()
    for file in sorted(allFiles):
        annotators = [annotator for annotator in eventAnnotationsByIds if file in eventAnnotationsByIds[annotator]]
        if (len(annotators) < 2):
            raise Exception(" Too few annotators for the file "+file+" "+str(len(annotators)))
        #print (file, annotators)
        calcEntityAnnotationAgreementsOnFile(file, annotators, eventAnnotationsByLoc, \
                                             eventAnnotationsByIds, tmxAnnotationsByLoc, \
                                             tmxAnnotationsByIds, counter)
    
    ia_agreements.printAggregateResults(counter, details=True, judge='j', findGroupAvgs=True)

else:
    print(" Please give argument: <annotated_corpus_dir> ")
    print(" Example:\n     python  "+sys.argv[0]+"  corpus")
