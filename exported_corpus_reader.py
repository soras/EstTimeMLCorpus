#!/usr/bin/python
# -*- coding: utf-8 -*- 
#
#   Developed and tested under Python's version: 3.3.2
#
#    Script for reading and displaying Estonian TimeML corpus annotations;
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
        # Skipt the comment line
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
        # Skipt the comment line
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
        # Skipt the comment line
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
        # Skipt the comment line
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
        # Skipt the comment line
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
#    Displaying annotations on corpus files
# =========================================================================
def getEntityIDsOfTheSentence(file, sentID, base, eventsByLoc, timexesByLoc):
    events  = []
    timexes = []
    seenIDs = dict()
    for wordID in range(len(base[file][sentID])):
        [sID, wID, token, morphSyntactic, syntacticID, syntacticHeadID] = base[file][sentID][wordID]
        key = (sID, wID)
        if (file in eventsByLoc and key in eventsByLoc[file]):
            for [entityID, expression, annotation] in eventsByLoc[file][key]:
                if ( entityID not in seenIDs ):
                    events.append(entityID)
                    seenIDs[entityID] = 1
        if (file in timexesByLoc and key in timexesByLoc[file]):
            for [entityID, expression, annotation] in timexesByLoc[file][key]:
                if ( entityID not in seenIDs ):
                    timexes.append(entityID)
                    seenIDs[entityID] = 1
    return ( events, timexes )

def getSentenceWithEntityAnnotations(file, sentID, base, eventsByLoc, timexesByLoc):
    sentAnnotation = " s"+str(sentID)+" "
    for wordID in range(len(base[file][sentID])):
        [sID, wID, token, morphSyntactic, syntacticID, syntacticHeadID] = base[file][sentID][wordID]
        key = (sID, wID)
        # Start of tag
        if (file in timexesByLoc and key in timexesByLoc[file]):
            for [entityID, expression, annotation] in timexesByLoc[file][key]:
                expressionMatcher = re.match("^\"(.+)\"$", expression)
                expressionClean = expressionMatcher.group(1)
                multiWord = ("multiword=\"true\"" in annotation)
                if (not multiWord or (multiWord and expressionClean.startswith(token))):
                    sentAnnotation += " ["+entityID+""
        if (file in eventsByLoc and key in eventsByLoc[file]):
            for [entityID, expression, annotation] in eventsByLoc[file][key]:
                expressionMatcher = re.match("^\"(.+)\"$", expression)
                expressionClean = expressionMatcher.group(1)
                multiWord = ("multiword=\"true\"" in annotation)
                sentAnnotation += " ["+entityID+""
        # Token
        sentAnnotation += " "+token
        # End of tag
        if (file in timexesByLoc and key in timexesByLoc[file]):
            for [entityID, expression, annotation] in timexesByLoc[file][key]:
                expressionMatcher = re.match("^\"(.+)\"$", expression)
                expressionClean = expressionMatcher.group(1)
                multiWord = ("multiword=\"true\"" in annotation)
                if (not multiWord or (multiWord and expressionClean.endswith(token))):
                    sentAnnotation += " ]"
        if (file in eventsByLoc and key in eventsByLoc[file]):
            for [entityID, expression, annotation] in eventsByLoc[file][key]:
                expressionMatcher = re.match("^\"(.+)\"$", expression)
                expressionClean = expressionMatcher.group(1)
                multiWord = ("multiword=\"true\"" in annotation)
                sentAnnotation += " ]"
    return sentAnnotation


# Retrieves an expression corresponding to the entity
def getExpr(file, entityID, entitiesByIDs):
    if (entityID in entitiesByIDs[file]):
        # Collect entity expressions
        expressions = set()
        for item in entitiesByIDs[file][entityID]:
            # [sentenceID, wordID, expression, annotation]
            expressions.add( item[2] )
        if (len(expressions) == 1):
            return expressions.pop()
        else:
            raise Exception(" Unexpected number of expressions for "+entityID+": "+str(expressions))
    else:
        raise Exception(" Unable to the retrieve expression for the entity "+entityID)


def getTLINKAnnotations(file, eventIDs, timexIDs, eventsByID, timexesByID, \
                        eventTimexLinks, eventDCTLinks, mainEventLinks, subEventLinks):
    linkAnnotations = []
    for eventID in eventIDs:
        if (file in eventTimexLinks and eventID in eventTimexLinks[file]):
            for annotation in eventTimexLinks[file][eventID]:
                [entityA, relation, entityB, comment] = annotation
                if (eventID == entityA):
                    exprA = getExpr(file, entityA, eventsByID)
                    exprB = getExpr(file, entityB, timexesByID)
                    linkAnnotations.append( " "*5+entityA+" "+exprA+"  "+relation+"  "+entityB+" "+exprB+" "+comment )
        if (file in eventDCTLinks and eventID in eventDCTLinks[file]):
            for annotation in eventDCTLinks[file][eventID]:
                [entityA, relation, entityB, comment] = annotation
                if (eventID == entityA):
                    exprA = getExpr(file, entityA, eventsByID)
                    exprB = "DCT"
                    linkAnnotations.append( " "*5+entityA+" "+exprA+"  "+relation+"  "+exprB+" "+comment )
        if (file in subEventLinks and eventID in subEventLinks[file]):
            for annotation in subEventLinks[file][eventID]:
                [entityA, relation, entityB, comment] = annotation
                if (eventID == entityA):
                    exprA = getExpr(file, entityA, eventsByID)
                    exprB = getExpr(file, entityB, eventsByID)
                    linkAnnotations.append( " "*5+entityA+" "+exprA+"  "+relation+"  "+entityB+" "+exprB+" "+comment )
        if (file in mainEventLinks and eventID in mainEventLinks[file]):
            for annotation in mainEventLinks[file][eventID]:
                [entityA, relation, entityB, comment] = annotation
                if (eventID == entityA):
                    exprA = getExpr(file, entityA, eventsByID)
                    exprB = getExpr(file, entityB, eventsByID)
                    linkAnnotations.append( " "*5+entityA+" "+exprA+"  "+relation+"  "+entityB+" "+exprB+" "+comment )
    return "\n".join(linkAnnotations)


def display(base, eventsByLoc, timexesByLoc, eventsByID, timexesByID, \
            DCTsByFile, eventTimexLinks, eventDCTLinks, mainEventLinks, subEventLinks):
    for file in sorted(base):
        print ("="*50)
        print (" "*5 + file)
        print (" "*5 + " DCT: "+DCTsByFile[file])
        print ("="*50)
        for sentID in range(len(base[file])):
            # Display sentence annotation
            sentAnnotation = getSentenceWithEntityAnnotations(file, sentID, base, eventsByLoc, timexesByLoc)
            try:
                print ( sentAnnotation )
            except:
                print ( sentAnnotation.encode("utf-8") )
            # Display relation annotations
            ( eventIDs, timexIDs ) = getEntityIDsOfTheSentence(file, sentID, base, eventsByLoc, timexesByLoc)
            linkAnnotations = \
                getTLINKAnnotations(file, eventIDs, timexIDs, eventsByID, timexesByID, \
                                    eventTimexLinks, eventDCTLinks, mainEventLinks, subEventLinks)
            if (len(linkAnnotations) > 0):
                try:
                    print ( linkAnnotations+"\n" )
                except:
                    print ( linkAnnotations.encode("utf-8")+"\n" )
        print ()

# =========================================================================
#    Main program : loading corpus from files and displaying the content
# =========================================================================

if len(sys.argv) > 1 and os.path.isdir(sys.argv[1]):
    corpusDir = sys.argv[1]

    # Load base segmentation, morphological and syntactic annotations
    baseSegmentationFile = os.path.join(corpusDir, baseAnnotationFile)
    baseAnnotations = load_base_segmentation(baseSegmentationFile)

    # Load EVENT, TIMEX annotations
    (eventsByLoc, eventsByID) = load_entity_annotation( os.path.join(corpusDir, eventAnnotationFile) )
    (timexesByLoc, timexesByID) = load_entity_annotation( os.path.join(corpusDir, timexAnnotationFile) )
    DCTsByFile = load_dct_annotation( os.path.join(corpusDir, timexAnnotationDCTFile) )

    # Load TLINK annotations
    eventTimexLinks = load_relation_annotation( os.path.join(corpusDir, tlinkEventTimexFile) )
    eventDCTLinks   = load_relation_to_dct_annotations( os.path.join(corpusDir, tlinkEventDCTFile) )
    mainEventLinks  = load_relation_annotation( os.path.join(corpusDir, tlinkMainEventsFile) )
    subEventLinks  = load_relation_annotation( os.path.join(corpusDir, tlinkSubEventsFile) )

    # Display annotations
    display(baseAnnotations, eventsByLoc, timexesByLoc, eventsByID, timexesByID, DCTsByFile, eventTimexLinks, eventDCTLinks, mainEventLinks, subEventLinks)

else:
    print(" Please give argument: <annotated_corpus_dir> ")
    print(" Example:\n     python  "+sys.argv[0]+"  corpus")
