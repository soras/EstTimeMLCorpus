# -*- coding: utf-8 -*- 
#
#     Script for calculating combined (EVENT, TLINK) annotation agreements.
#    Also allows to filter EVENT (and associated TLINK) annotations based 
#    on linguistic constraints, using filtering methods implemented in 
#    'filtering_utils.py';
#
#    Required input arguments:
#       <corpus_dir> <experimentID>
#
#    Developed and tested under Python's version: 3.4.1
#

import sys, os, re

import data_import
import ia_agreements
import dependency_trees
import sol_format_tools
import filtering_utils

filterKey = '2a'
judge = 'j'

# =========================================================================
#    Recording the counts and agreements
# =========================================================================

#  Records the count of events by considering the number of tokens covered
#  by events with unique ids
def recordEventCounts(eventAnnotationsByLocs, countingPhase, totalCounter, file, judge):
    headerTag = re.compile('^(EVENT|TIMEX)\s+([A-Z_]+)\s*')
    allUniqAnnotatorEvents = dict()
    for annotator in eventAnnotationsByLocs:
        idsCounted = dict()
        if file in eventAnnotationsByLocs[annotator]:
            for (sentID, wordID) in sorted(eventAnnotationsByLocs[annotator][file]):
                for ann in sorted(eventAnnotationsByLocs[annotator][file][(sentID, wordID)]):
                    [entityID, expression, annotation] = ann
                    if (entityID not in idsCounted):
                        totalCounter.addToCount(countingPhase, annotator, "_", 1)
                        totalCounter.addToCount(countingPhase, "_all", "_", 1)
                        idsCounted[entityID] = 1
                        if (annotator != judge):
                            allUniqAnnotatorEvents[(sentID, wordID)] = 1
    totalCounter.addToCount(countingPhase, "_all_uniq_anns", "_", len( allUniqAnnotatorEvents.keys() ))


# Records TLINK counts (over all layers)
def recordTLINKCounts(eventTimexLinks, eventDCTLinks, mainEventLinks, subEventLinks, \
                      relCountKey, totalCounter, judge):
    for annotator in ['a', 'b', 'c', 'j']:
        tlinks1 = data_import.get_relation_annotations_as_list(eventTimexLinks[annotator])
        tlinks2 = data_import.get_relation_annotations_as_list(eventDCTLinks[annotator])
        tlinks3 = data_import.get_relation_annotations_as_list(mainEventLinks[annotator])
        tlinks4 = data_import.get_relation_annotations_as_list(subEventLinks[annotator])
        if (relCountKey == "_all"):
            #  Fills the initial counts section
            totalCounter.addToCount("total-count-tlinks", annotator, "_", len(tlinks1))
            totalCounter.addToCount("total-count-tlinks", annotator, "_", len(tlinks2))
            totalCounter.addToCount("total-count-tlinks", annotator, "_", len(tlinks3))
            totalCounter.addToCount("total-count-tlinks", annotator, "_", len(tlinks4))
            if annotator != judge:
                totalCounter.addToCount("total-count-tlinks", "_all", "_", len(tlinks1))
                totalCounter.addToCount("total-count-tlinks", "_all", "_", len(tlinks2))
                totalCounter.addToCount("total-count-tlinks", "_all", "_", len(tlinks3))
                totalCounter.addToCount("total-count-tlinks", "_all", "_", len(tlinks4))
            if annotator == judge:
                # Record annotations of the judge, phase by phase
                totalCounter.addToCount( "total-count-tlinks", judge, "tlink_layer_1", len(tlinks1) )
                totalCounter.addToCount( "total-count-tlinks", judge, "tlink_layer_2", len(tlinks2) )
                totalCounter.addToCount( "total-count-tlinks", judge, "tlink_layer_3", len(tlinks3) )
                totalCounter.addToCount( "total-count-tlinks", judge, "tlink_layer_4", len(tlinks4) )
        elif (relCountKey == "_remain"):
            #  Fills the remaining counts section
            layers = ["1-event_timex", "2-event_dct", "3-main_events", "4-event_event"]
            links  = [tlinks1, tlinks2, tlinks3, tlinks4]
            for l in range(len(layers)):
                #
                # Data format:
                #  [file, entityA, relation, entityB, comment]
                #
                for [file, entityA, rel, entityB, comment] in links[l]:
                    totalCounter.addToCount("total-count-remaining-tlinks", annotator, "_", 1)
                    totalCounter.addToCount("total-count-remaining-tlinks", "_all", layers[l], 1)
                    totalCounter.addToCount("total-count-remaining-tlinks", "_all", "_all", 1)
                    if rel == 'VAGUE':
                        totalCounter.addToCount("total-count-remaining-tlinks", "_all", "_vague", 1)
                        totalCounter.addToCount("total-count-remaining-tlinks", annotator, "_vague", 1)
        else:
            raise Exception (" Unexpected relCountKey: "+relCountKey)


def recordEventAnnotationAgreementsOnFile(fileName, annotators, eventAnnotationsByLoc, \
                                          eventAnnotationsByIds, totalCounter):
    ''' Calculates event annotation agreements (on both extent + specific attributes) 
        between all pairs of annotators that have annotated given file.
        Records agreements in terms of precision, recall and F-score into the 
        totalCounter for aggregation.
    '''
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


def recordTlinkAnnotationAgreements(eventTimexLinks, eventDCTLinks, mainEventLinks, \
                                    subEventLinks, judge, totalCounter, fileToAnnotators):
    ''' Records relation annotation agreements (matching and mismatching annotations)
        over all relation layers and between all annotator pairs.
    '''
    # ============================================
    #    1-tlinks-event-timex
    # ============================================
    allAnnotations = dict()
    for annotator in ['a', 'b', 'c', 'j']:
        allAnnotations[annotator] = \
            data_import.get_relation_annotations_as_list(eventTimexLinks[annotator])
    ia_agreements.record_tlinks_matches(allAnnotations, "event_timex", "base", totalCounter, fileToAnnotators)
    ia_agreements.record_tlinks_matches(allAnnotations, "event_timex", "rel_3_1", totalCounter, fileToAnnotators)
    ia_agreements.record_tlinks_matches(allAnnotations, "event_timex", "rel_3_2", totalCounter, fileToAnnotators)
    ia_agreements.record_tlinks_matches(allAnnotations, "event_timex", "rel_ovrl", totalCounter, fileToAnnotators)

    # ============================================
    #    2-tlinks-event-dct
    # ============================================
    allAnnotations = dict()
    for annotator in ['a', 'b', 'c', 'j']:
        allAnnotations[annotator] = \
            data_import.get_relation_annotations_as_list(eventDCTLinks[annotator])
    ia_agreements.record_tlinks_matches(allAnnotations, "event_dct", "base", totalCounter, fileToAnnotators)
    ia_agreements.record_tlinks_matches(allAnnotations, "event_dct", "rel_3_1", totalCounter, fileToAnnotators)
    ia_agreements.record_tlinks_matches(allAnnotations, "event_dct", "rel_3_2", totalCounter, fileToAnnotators)
    ia_agreements.record_tlinks_matches(allAnnotations, "event_dct", "rel_ovrl", totalCounter, fileToAnnotators)
    
    # ============================================
    #    3-tlinks-main-events
    # ============================================ 
    allAnnotations = dict()
    for annotator in ['a', 'b', 'c', 'j']:
        allAnnotations[annotator] = \
            data_import.get_relation_annotations_as_list(mainEventLinks[annotator])
    ia_agreements.record_tlinks_matches(allAnnotations, "main_events", "base", totalCounter, fileToAnnotators)
    ia_agreements.record_tlinks_matches(allAnnotations, "main_events", "rel_3_1", totalCounter, fileToAnnotators)
    ia_agreements.record_tlinks_matches(allAnnotations, "main_events", "rel_3_2", totalCounter, fileToAnnotators)
    ia_agreements.record_tlinks_matches(allAnnotations, "main_events", "rel_ovrl", totalCounter, fileToAnnotators)
    
    # ============================================
    #    4-tlinks-main-events
    # ============================================
    allAnnotations = dict()
    for annotator in ['a', 'b', 'c', 'j']:
        allAnnotations[annotator] = \
            data_import.get_relation_annotations_as_list(subEventLinks[annotator])
    ia_agreements.record_tlinks_matches(allAnnotations, "event_event", "base", totalCounter, fileToAnnotators)
    ia_agreements.record_tlinks_matches(allAnnotations, "event_event", "rel_3_1", totalCounter, fileToAnnotators)
    ia_agreements.record_tlinks_matches(allAnnotations, "event_event", "rel_3_2", totalCounter, fileToAnnotators)
    ia_agreements.record_tlinks_matches(allAnnotations, "event_event", "rel_ovrl", totalCounter, fileToAnnotators)


# =========================================================================
#    Main program : load corpus from files, apply the filtering method, 
#    find agreements on remaining annotations, aggregate and display the 
#    results 
# =========================================================================

if len(sys.argv) > 1 and os.path.isdir(sys.argv[1]):
    corpusDir = sys.argv[1]
    if (len(sys.argv) > 2):
        for i in range(2, len(sys.argv)):
            if (re.match("^[0-9]+\*?[a-z]$", sys.argv[i])):
                filterKey = sys.argv[i]
                print (" Using the filtering method: "+filterKey)

    # Load base segmentation, morphological and syntactic annotations
    baseSegmentationFile = os.path.join(corpusDir, data_import.baseAnnotationFile)
    baseAnnotations = data_import.load_base_segmentation(baseSegmentationFile)

    #  Load EVENT and TIMEX annotations of all annotators ...
    eventAnnotationsByLoc, eventAnnotationsByIds, \
    tmxAnnotationsByLoc, tmxAnnotationsByIds = data_import.loadAllEntityAnnotations(corpusDir)
    
    #  Load TLINK annotations of all annotators ...
    eventTimexLinks, eventDCTLinks, mainEventLinks, subEventLinks = \
        data_import.loadAllTLINKannotations(corpusDir)
    #print(len(eventTimexLinks), len(eventDCTLinks), len(mainEventLinks), len(subEventLinks))

    # Names of all corpus files
    allFiles = list(eventAnnotationsByIds['j'].keys())
    
    # Iterate over all files, filter and calculate IA agreements on entities
    results = []
    totalCounter = ia_agreements.AggregateCounter() # Results over all files
    deletedAnnotationsByLoc   = dict()
    deletedEVENTStatistics    = dict()
    remainingEventAnnotations = dict()
    fileToAnnotators          = dict()
    for file in sorted(allFiles):
        print (" Processing "+file+" ... ", end="")
        annotators = [annotator for annotator in eventAnnotationsByIds \
                      if file in eventAnnotationsByIds[annotator]]
        fileToAnnotators[file] = annotators
        if (len(annotators) < 3):
            raise Exception(" Too few annotators for the file "+file+" "+str(len(annotators)))
        
        # Construct trees
        sentTrees = dependency_trees.build_dependency_trees( baseAnnotations[file] )
        dependency_trees.add_clause_info_to_trees( baseAnnotations[file], sentTrees )
        
        recordEventCounts(eventAnnotationsByLoc, "total-count-events", \
                          totalCounter, file, judge)
        # Filter out events based on morphological/syntactic/other constraints
        filtering_utils.filterAnnotations(file, annotators, judge, baseAnnotations[file],\
                          sentTrees, eventAnnotationsByLoc, tmxAnnotationsByLoc, \
                          eventAnnotationsByIds, tmxAnnotationsByIds, filterKey, \
                          deletedAnnotationsByLoc, deletedEVENTStatistics, debug=False)
        recordEventCounts(eventAnnotationsByLoc, "total-count-remaining-events", \
                          totalCounter, file, judge)
        # Find annotation agreements on the set of remaining events
        recordEventAnnotationAgreementsOnFile(file, annotators, eventAnnotationsByLoc, \
                                              eventAnnotationsByIds, totalCounter)
        print()

    # Some debug information 
    totalEventsByID   = 0
    deletedEventsByID = 0
    for annotator in deletedEVENTStatistics:
        totalEventsByID   += deletedEVENTStatistics[annotator]["_all_IDs"]
        deletedEventsByID += deletedEVENTStatistics[annotator]["_del_IDs"]
    print ('  Events deleted (counting IDs):       ',deletedEventsByID,'/',totalEventsByID)
    print ('  Judge events deleted (counting IDs): ',deletedEVENTStatistics[judge]["_del_IDs"],'/',deletedEVENTStatistics[judge]["_all_IDs"])    


    recordTLINKCounts(eventTimexLinks, eventDCTLinks, mainEventLinks, subEventLinks,\
                      "_all", totalCounter, judge)
    # Filter out tlinks based on deleted events
    filtering_utils.filterOutDeletedRelations(eventTimexLinks, eventDCTLinks, mainEventLinks, \
                                              subEventLinks, eventAnnotationsByIds, judge)
    recordTLINKCounts(eventTimexLinks, eventDCTLinks, mainEventLinks, subEventLinks,\
                      "_remain", totalCounter, judge)
    # Find tlink annotation agreements on the set of remaining relations
    print (" Recording relation annotation agreements:")
    recordTlinkAnnotationAgreements(eventTimexLinks, eventDCTLinks, mainEventLinks, \
                                    subEventLinks, judge, totalCounter, fileToAnnotators)

    print ()
    print (("="*30))
    print (" Results over all files ("+filterKey+")")
    print (("="*30))

    ia_agreements.aggregateAndPrintFilteringResults( \
        totalCounter, filterKey, judge = judge, onlyTlinkBase = True)

else:
    print(" Please give arguments: <corpus_dir> <experimentID>")
    print(" Example:\n     python  "+sys.argv[0]+"  corpus 1a")
