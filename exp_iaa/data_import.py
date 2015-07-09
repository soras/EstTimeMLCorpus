# -*- coding: utf-8 -*- 
#
#   Methods for importing data from the corpus files.
#
#   Developed and tested under Python's version: 3.4.1
#

import sys, os, re

baseAnnotationFile     = "base-segmentation-morph-syntax"
eventAnnotationFile    = "event-annotation"
timexAnnotationFile    = "timex-annotation"
timexAnnotationDCTFile = "timex-annotation-dct"
tlinkEventTimexFile    = "tlink-event-timex"
tlinkEventDCTFile      = "tlink-event-dct"
tlinkMainEventsFile    = "tlink-main-events"
tlinkSubEventsFile     = "tlink-subordinate-events"

# =========================================================================
#    Loading corpus files
# =========================================================================

def load_base_segmentation(inputFile):
    base_segmentation = dict()
    last_sentenceID = ""
    f = open(inputFile, mode='r', encoding="utf-8")
    for line in f:
        # Skip the comment line
        if ( re.match("^#.+$", line) ):
            continue
        items = (line.rstrip()).split("\t")
        if (len(items) != 7):
            raise Exception(" Unexpected number of items on line: '"+str(line)+"'")
        file = items[0]
        if (file not in base_segmentation):
            base_segmentation[file] = []
        sentenceID = items[1]
        if (sentenceID != last_sentenceID):
            base_segmentation[file].append([])
        wordID     = items[2]
        # fileName	sentence_ID	word_ID_in_sentence	token	morphological_and_syntactic_annotations	syntactic_ID	syntactic_ID_of_head
        token           = items[3]
        morphSyntactic  = items[4]
        syntacticID     = items[5]
        syntacticHeadID = items[6]
        base_segmentation[file][-1].append( [sentenceID, wordID, token, morphSyntactic, syntacticID, syntacticHeadID] )
        last_sentenceID = sentenceID
    f.close()
    return base_segmentation
    
def load_entity_annotation(inputFile):
    annotationsByLoc = dict()
    annotationsByID  = dict()
    f = open(inputFile, mode='r', encoding="utf-8")
    for line in f:
        # Skip the comment line
        if ( re.match("^#.+$", line) ):
            continue
        items = (line.rstrip()).split("\t")
        # fileName	sentence_ID	word_ID_in_sentence	expression	event_annotation	event_ID
        # fileName	sentence_ID	word_ID_in_sentence	expression	timex_annotation	timex_ID
        if (len(items) != 6):
            raise Exception(" Unexpected number of items on line: '"+str(line)+"'")
        file       = items[0]
        sentenceID = items[1]
        wordID     = items[2]
        expression = items[3]
        annotation = items[4]
        entityID   = items[5]
        if (file not in annotationsByLoc):
            annotationsByLoc[file] = dict()
        if (file not in annotationsByID):
            annotationsByID[file] = dict()
        # Record annotation by its location in text
        locKey = (sentenceID, wordID)
        if (locKey not in annotationsByLoc[file]):
            annotationsByLoc[file][locKey] = []
        annotationsByLoc[file][locKey].append( [entityID, expression, annotation] )
        # Record annotation by its unique ID in text
        if (entityID not in annotationsByID[file]):
            annotationsByID[file][entityID] = []
        annotationsByID[file][entityID].append( [sentenceID, wordID, expression, annotation] )
    f.close()
    return (annotationsByLoc, annotationsByID)

def load_dct_annotation(inputFile):
    DCTsByFile = dict()
    f = open(inputFile, mode='r', encoding="utf-8")
    for line in f:
        # Skip the comment line
        if ( re.match("^#.+$", line) ):
            continue
        items = (line.rstrip()).split("\t")
        # fileName	document_creation_time
        if (len(items) != 2):
            raise Exception(" Unexpected number of items on line: '"+str(line)+"'")
        file = items[0]
        dct  = items[1]
        DCTsByFile[ file ] = dct
    f.close()
    return DCTsByFile

def load_relation_annotation(inputFile):
    annotationsByID  = dict()
    f = open(inputFile, mode='r', encoding="utf-8")
    for line in f:
        # Skip the comment line
        if ( re.match("^#.+$", line) ):
            continue
        items = line.split("\t")
        # old format: fileName	entityID_A	relation	entityID_B	comment	expression_A	expression_B
        # new format: fileName	entityID_A	relation	entityID_B	comment	
        if (len(items) != 5):
            print (len(items))
            raise Exception(" Unexpected number of items on line: '"+str(line)+"'")
        file     = items[0]
        entityA  = items[1]
        relation = items[2]
        entityB  = items[3]
        comment  = items[4].rstrip()
        if (file not in annotationsByID):
            annotationsByID[file] = dict()
        annotation = [entityA, relation, entityB, comment]
        if (entityA not in annotationsByID[file]):
            annotationsByID[file][entityA] = []
        annotationsByID[file][entityA].append( annotation )
        if (entityB not in annotationsByID[file]):
            annotationsByID[file][entityB] = []
        annotationsByID[file][entityB].append( annotation )
    f.close()
    return annotationsByID

def load_relation_to_dct_annotations(inputFile):
    annotationsByID  = dict()
    f = open(inputFile, mode='r', encoding="utf-8")
    for line in f:
        # Skip the comment line
        if ( re.match("^#.+$", line) ):
            continue
        items = line.split("\t")
        # old format: fileName	entityID_A	relation_to_DCT	comment	expression_A
        # new format: fileName	entityID_A	relation_to_DCT	comment
        if (len(items) != 4):
            raise Exception(" Unexpected number of items on line: '"+str(line)+"'")
        file          = items[0]
        entityA       = items[1]
        relationToDCT = items[2]
        comment       = items[3].rstrip()
        if (file not in annotationsByID):
            annotationsByID[file] = dict()
        annotation = [entityA, relationToDCT, "t0", comment]
        if (entityA not in annotationsByID[file]):
            annotationsByID[file][entityA] = []
        annotationsByID[file][entityA].append( annotation )
    f.close()
    return annotationsByID

# =========================================================================
#    Restructuring TLINK annotations
# =========================================================================

def get_relation_annotations_as_list(annotationsByID):
    annotationsList = []
    for file in annotationsByID:
        seenAnnotations = []
        for entity in annotationsByID[file]:
            for annotation in annotationsByID[file][entity]:
                if annotation not in seenAnnotations:
                    seenAnnotations.append(annotation)
                    annotationsList.append( [file] + annotation )
    return annotationsList

# =========================================================================
#    Loading all annotations at once
# =========================================================================

def loadAllEntityAnnotations(corpusDir):
    ''' Loads EVENT and TIMEX annotations of all annotators (annotators A, B, C 
        and the judge J).
    '''
    # Load EVENT annotations
    eventAnnotationsByLoc = { "a" : None, "b" : None, "c" : None, "j" : None }
    eventAnnotationsByIds = { "a" : None, "b" : None, "c" : None, "j" : None }
    (eventsByLoc, eventsByID) = \
        load_entity_annotation( os.path.join(corpusDir, eventAnnotationFile) )
    eventAnnotationsByLoc['j'] = eventsByLoc
    eventAnnotationsByIds['j'] = eventsByID
    for annotatorID in [ "a", "b", "c" ]:
        suffix = ".ann-"+annotatorID
        (eventsByLoc, eventsByID) = \
          load_entity_annotation( os.path.join(corpusDir, eventAnnotationFile + suffix) )
        eventAnnotationsByLoc[annotatorID] = eventsByLoc
        eventAnnotationsByIds[annotatorID] = eventsByID
    # Load TIMEX annotations
    tmxAnnotationsByLoc = { "a" : None, "b" : None, "c" : None, "j" : None }
    tmxAnnotationsByIds = { "a" : None, "b" : None, "c" : None, "j" : None }
    (tmxByLoc, tmxByID) = \
        load_entity_annotation( os.path.join(corpusDir, timexAnnotationFile) )
    tmxAnnotationsByLoc['j'] = tmxByLoc
    tmxAnnotationsByIds['j'] = tmxByID
    for annotatorID in [ "a", "b", "c" ]:
        suffix = ".ann-"+annotatorID
        (tmxByLoc, tmxByID) = \
          load_entity_annotation( os.path.join(corpusDir, timexAnnotationFile + suffix) )
        tmxAnnotationsByLoc[annotatorID] = tmxByLoc
        tmxAnnotationsByIds[annotatorID] = tmxByID
    return eventAnnotationsByLoc, eventAnnotationsByIds, \
           tmxAnnotationsByLoc, tmxAnnotationsByIds

def loadAllTLINKannotations(corpusDir):
    ''' Loads TLINK annotations of all annotators (annotators A, B, C and 
        the judge J).
    '''
    # eventTimexLinks
    eventTimexLinks = { "a" : None, "b" : None, "c" : None, "j" : None }
    for key in eventTimexLinks:
        suffix = ''
        if key != 'j':
            suffix = ".ann-"+key
        tlinks = load_relation_annotation( \
            os.path.join(corpusDir, tlinkEventTimexFile + suffix) )
        eventTimexLinks[ key ] = tlinks
    # eventDCTLinks
    eventDCTLinks   = { "a" : None, "b" : None, "c" : None, "j" : None }
    for key in eventDCTLinks:
        suffix = ''
        if key != 'j':
            suffix = ".ann-"+key
        tlinks = load_relation_to_dct_annotations( \
            os.path.join(corpusDir, tlinkEventDCTFile + suffix) )
        eventDCTLinks[ key ] = tlinks    
    # mainEventLinks
    mainEventLinks   = { "a" : None, "b" : None, "c" : None, "j" : None }
    for key in mainEventLinks:
        suffix = ''
        if key != 'j':
            suffix = ".ann-"+key
        tlinks = load_relation_annotation( \
            os.path.join(corpusDir, tlinkMainEventsFile + suffix) )
        mainEventLinks[ key ] = tlinks 
    # subEventLinks
    subEventLinks   = { "a" : None, "b" : None, "c" : None, "j" : None }
    for key in subEventLinks:
        suffix = ''
        if key != 'j':
            suffix = ".ann-"+key
        tlinks = load_relation_annotation( \
            os.path.join(corpusDir, tlinkSubEventsFile + suffix) )
        subEventLinks[ key ] = tlinks 
    return eventTimexLinks, eventDCTLinks, mainEventLinks, subEventLinks

