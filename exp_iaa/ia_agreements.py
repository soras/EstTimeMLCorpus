# -*- coding: utf-8 -*- 
#
#    Methods for:
#      *) counting matching annotations (EVENT, TIMEX, TLINK);
#      *) measuring entity inter-annotator agreements;
#      *) aggregating agreement scores over annotator groups;
#      *) displaying aggregated agreement scores;
#
#    Developed and tested under Python's version: 3.4.1
#

import sys, os, re
from math import fsum

import ia_agreements_chance_corrected

class AggregateCounter:
    'An aggregate counter for recording different aspects of annotation.'

    def __init__(self):
        self.results = dict()

    def addToCount(self, task, pair, item, value):
        if (not value):
            value = 0
        if (task not in self.results):
            self.results[task] = dict()
        if (pair not in self.results[task]):
            self.results[task][pair] = dict()
        if (item not in self.results[task][pair]):
            self.results[task][pair][item] = value
        else:
            self.results[task][pair][item] = self.results[task][pair][item] + value

    def getCount(self, task, pair, item):
        if ((task not in self.results) or (pair not in self.results[task]) or (item not in self.results[task][pair])):
            return 0
        else:
            return self.results[task][pair][item]

    def getCounts(self):
        return self.results

    #  Gets sorted pairs of given task. If judge name is defined,
    # all the pairs with the judge are added at the end of the list,
    # regardless the alphabetical sorting order
    def getSortedPairs(self, task, judge):
        if (judge):
            judge_pairs = []
            other_pairs = []
            for pair in sorted(self.results[task].keys()):
                if judge in pair:
                    judge_pairs.append(pair)
                else:
                    other_pairs.append(pair)
            other_pairs.extend(judge_pairs)
            return other_pairs
        else:
            return sorted(self.results[task].keys())

# ============================================================
# ============================================================
#     Entity extent overlap and agreement
# ============================================================
# ============================================================

def findAnnotationMappings( annotationsByID_sug, annotationsByID_ref, multipleStrategy = None, keepMappingsUnique=True ):
    ''' Finds token-wise alignments between two sets of annotations (SUG - suggested annotations, 
        and REF - reference annotations);
        Parameters *multipleStrategy* and *keepMappingsUnique* guide, how one-to-many and 
        many-to-many mappings are handled. For instance, in case of the SUG-to-REF mapping:
            *) If multipleStrategy == None, then one-to-many / many-to-one mappings are allowed: 
                                      each SUG is allowed to be mapped to multiple REF-s;
            *) If multipleStrategy == 'first', then one-to-one mappings are forced:
                                      each SUG is mapped to exactly one REF, picking the first 
                                      one;
            *) If multipleStrategy == 'largest', then one-to-one mappings are forced:
                                      each SUG is mapped to exactly one REF, picking the one 
                                      with the largest overlap;
            *) If keepMappingsUnique == True, then one-to-one mappings are forced:
                                      each REF can be mapped to exactly one SUG;
                                      (otherwise, a REF can be mapped to multiple SUGs, even 
                                      if multipleStrategy != None );
        Returns two mappings: a mapping from SUG-to-REF, and a mapping from REF-to-SUG;
    '''
    multipleStrategy = multipleStrategy.lower() if multipleStrategy else None
    # Create mappings (token-vise-alignments) between two sets of annotations
    mapping_sug_to_ref = dict()
    mapping_ref_to_sug = dict()
    used_refs = dict()
    used_sugs = dict()
    for sugID in sorted(annotationsByID_sug.keys()):
        phrase_sug = annotationsByID_sug[sugID]
        tokens_sug = set([ token[1] for token in phrase_sug ])
        mapping_sug_to_ref[sugID] = []
        biggest_overlap = 0
        for refID in sorted(annotationsByID_ref.keys()):
            if refID in used_refs and keepMappingsUnique:
                continue
            phrase_ref = annotationsByID_ref[refID]
            tokens_ref = set([ token[1] for token in phrase_ref ])
            for [sentenceID_a, wordID_a, expression_a, annotation_a] in phrase_sug:
                for [sentenceID_b, wordID_b, expression_b, annotation_b] in phrase_ref:
                    if sentenceID_a == sentenceID_b and wordID_a == wordID_b and \
                       refID not in mapping_sug_to_ref[sugID]:
                        if multipleStrategy == None:
                            # create one-to-many
                            mapping_sug_to_ref[sugID].append( refID )
                        elif multipleStrategy == 'first' and len(mapping_sug_to_ref[sugID])==0:
                            # create one-to-one: pick the first
                            mapping_sug_to_ref[sugID].append( refID )
                            used_refs[refID] = 1
                        elif multipleStrategy == 'largest':
                            # create one-to-one: pick the largest overlap
                            if len(tokens_sug.intersection(tokens_ref)) > biggest_overlap:
                                biggest_overlap = len(tokens_sug.intersection(tokens_ref))
                                if not mapping_sug_to_ref[sugID]:
                                    mapping_sug_to_ref[sugID].append( refID )
                                else: 
                                    mapping_sug_to_ref[sugID][0] = refID
                                used_refs[refID] = 1
    for refID in sorted(annotationsByID_ref.keys()):
        phrase_ref = annotationsByID_ref[refID]
        tokens_ref = set([ token[1] for token in phrase_ref ])
        mapping_ref_to_sug[refID] = []
        biggest_overlap = 0
        for sugID in sorted(annotationsByID_sug.keys()):
            if sugID in used_sugs and keepMappingsUnique:
                continue
            phrase_sug = annotationsByID_sug[sugID]
            tokens_sug = set([ token[1] for token in phrase_sug ])
            for [sentenceID_a, wordID_a, expression_a, annotation_a] in phrase_sug:
                for [sentenceID_b, wordID_b, expression_b, annotation_b] in phrase_ref:
                    if sentenceID_a == sentenceID_b and wordID_a == wordID_b and \
                       sugID not in mapping_ref_to_sug[refID]:
                        if multipleStrategy == None:
                            # create one-to-many
                            mapping_ref_to_sug[refID].append( sugID )
                        elif multipleStrategy == 'first' and len(mapping_ref_to_sug[sugID])==0:
                            # create one-to-one: pick the first
                            mapping_ref_to_sug[refID].append( sugID )
                            used_sugs[ sugID ] = 1
                        elif multipleStrategy == 'largest':
                            # create one-to-one: pick the largest overlap
                            if len(tokens_sug.intersection(tokens_ref)) > biggest_overlap:
                                biggest_overlap = len(tokens_sug.intersection(tokens_ref))
                                if not mapping_ref_to_sug[refID]:
                                    mapping_ref_to_sug[refID].append( sugID )
                                else: 
                                    mapping_ref_to_sug[refID][0] = sugID
                                used_sugs[ sugID ] = 1
    return (mapping_sug_to_ref, mapping_ref_to_sug)


def debugDisplayMappings(aKey, bKey, annotationsByID_sug, annotationsByID_ref, mapping_sug_to_ref, mapping_ref_to_sug):
    '''  A debug method for displaying the results of findAnnotationMappings();
    '''
    for aID in sorted(mapping_sug_to_ref):
        phrase_a = " ".join( list(set([ phrase[2] for phrase in annotationsByID_sug[aID] ])) )
        for bID in mapping_sug_to_ref[aID]:
            phrase_b = " ".join( list(set([ phrase[2] for phrase in annotationsByID_ref[bID] ])) )
            print (aKey, aID, phrase_a, "   vs   ", bID, phrase_b, bKey)
        if len(mapping_sug_to_ref[aID]) == 0:
            print (aKey, aID, phrase_a, "   vs   None")
    for aID in sorted(mapping_ref_to_sug):
        phrase_a = " ".join( list(set([ phrase[2] for phrase in annotationsByID_ref[aID] ])) )
        for bID in mapping_ref_to_sug[aID]:
            phrase_b = " ".join( list(set([ phrase[2] for phrase in annotationsByID_sug[bID] ])) )
            print (aKey, aID, phrase_a, "   vs   ", bID, phrase_b, bKey)
        if len(mapping_ref_to_sug[aID]) == 0:
            print (aKey, aID, phrase_a, "   vs   None")
    print()


def evaluateEntityExtent(ann_sug, ann_ref, mapping_sug_to_ref, mapping_ref_to_sug, oneBestMatch=True):
    ''' Based on given alignments, finds the agreement on entity extent (token coverage).
        Calculates:
          Recall    = correct / all_in_ref       
          Precision = correct / all_suggestions  
          F-score   = ( 2 * precision * recall ) / (precision + recall)
        If oneBestMatch=True, each sug_annotation is aligned with one ref_annotation with the largest
        token overlap in the extent;
    '''
    correct    = 0
    all_in_ref = 0
    all_in_sug = 0
    if oneBestMatch:
        for sug_id in ann_sug.keys():
            tokens_sug = set([ phrase[1] for phrase in ann_sug[sug_id] ])
            # Find one best match
            biggest_overlap = 0
            best_match      = None
            if sug_id in mapping_sug_to_ref:
                for ref_id in sorted( mapping_sug_to_ref[sug_id] ):
                    # Find, how many of the tokens are matching
                    tokens_ref = set([ phrase[1] for phrase in ann_ref[ref_id] ])
                    common     = len(tokens_sug.intersection(tokens_ref))
                    if common > biggest_overlap:
                        biggest_overlap = common
                        best_match = ref_id
            all_in_sug += 1
            if best_match:
                # relaxed: only one token overlap is required for the match
                correct += 1  
        for ref_id in ann_ref.keys():
            all_in_ref += 1
    else:
        #  The old way of calculating: total overlap of the tokens,
        #  note: mistakenly discards exact phrase boundaries
        for sug_id in ann_sug.keys():
            tokens_sug = set([ phrase[1] for phrase in ann_sug[sug_id] ])
            all_in_sug += len(tokens_sug)
            if sug_id in mapping_sug_to_ref:
                for ref_id in mapping_sug_to_ref[sug_id]:
                    # Find, how many of the tokens are matching
                    tokens_ref = set([ phrase[1] for phrase in ann_ref[ref_id] ])
                    common = len(tokens_sug.intersection(tokens_ref))
                    correct += common
        for ref_id in ann_ref.keys():
            tokens_ref = set([ phrase[1] for phrase in ann_ref[ref_id] ])
            all_in_ref += len(tokens_ref)
    if all_in_ref > 0:
       rec  = correct / all_in_ref
    else:
       rec  = 0.0
    if all_in_sug > 0:
       prec = correct / all_in_sug
    else:
       prec = 0.0
    if prec+rec > 0:
       fscore = (2*prec*rec) / (prec+rec)
    else:
       fscore = 0.0
    return (correct, all_in_ref, all_in_sug, rec, prec, fscore)


def compAnnotationExtents(entityName, annotator_sug, annotator_ref, annotationsByID_sug, annotationsByID_ref, counter, multipleStrategy = 'largest' ):
    ''' Aligns annotations of two annotators, calculates inter-annotator agreements on
        annotation extents, and returns formatted results;
    '''
    pair = annotator_sug+" vs "+annotator_ref
    # Create mappings between two sets of annotations
    # (suggested annotations and reference annotations)
    (mapping_sug_to_ref, mapping_ref_to_sug) = findAnnotationMappings(annotationsByID_sug, annotationsByID_ref, multipleStrategy )
    #debugDisplayMappings(annotator_sug, annotator_ref, annotationsByID_sug, annotationsByID_ref, mapping_sug_to_ref, mapping_ref_to_sug)
    # Find extent agreements: 
    (correct, all_in_ref, all_in_sug, rec, prec, fscore) = \
        evaluateEntityExtent(annotationsByID_sug, annotationsByID_ref, mapping_sug_to_ref, mapping_ref_to_sug)
    results = dict()
    if counter:
        counter.addToCount(entityName+"-extent", pair, "correct", correct)
        counter.addToCount(entityName+"-extent", pair, "all_in_ref", all_in_ref)
        counter.addToCount(entityName+"-extent", pair, "all_in_sug", all_in_sug)
        counter.addToCount(entityName+"-extent", pair, "counted_files", 1)
    if ( all_in_ref + all_in_sug > 0 ):
        rec_f    = '{:.3}'.format( rec  )
        prec_f   = '{:.3}'.format( prec )
        fscore_f = '{:.3}'.format( fscore )
        results[entityName+"-extent"] = (" "*7)+pair+"  "+entityName+"-extent "+"   R: "+rec_f+"   P: "+prec_f+"   F: "+fscore_f
    return (results, pair)

# ============================================================
# ============================================================
#     Overlap and agreement on attributes
# ============================================================
# ============================================================

def incCount(hash, key):
    if (key not in hash):
        hash[key] = 1
    else:
        hash[key] = hash[key] + 1

def isEntityHeader(tagString):
    ''' Finds (approximately) whether given tag represents the header tag.
    '''
    m1 = re.match( '^EVENT\s+"[^"]+"\s+([A-Z_]+)\s*.*$', tagString )
    m2 = re.match( '^EVENT\s+([A-Z_]+)\s*.*$', tagString )
    m3 = re.match( '^TIMEX\s+"[^"]+"\s+([A-Z_]+)\s+\S+.*$', tagString )
    m4 = re.match( '^TIMEX\s+([A-Z_]+)\s+\S+.*$', tagString )
    return m1 or m2 or m3 or m4


def getEntityAttribs(entityName, tagString):
    '''  Extracts main attributes from an EVENT or a TIMEX annotation.
    '''
    if (entityName == "EVENT"):
        m = re.match( "^"+entityName+'\s+"[^"]+"\s*(\S+).*$', tagString )
        if (m): return ( m.group(1) )
        m = re.match( "^"+entityName+"\s+(\S+).*$", tagString )
        if (m): return ( m.group(1) )
    if (entityName == "TIMEX"):
        m = re.match( "^"+entityName+'\s+"[^"]+"\s*(\S+)\s+(\S+).*$', tagString )
        if (m): return ( m.group(1), m.group(2) )
        m = re.match( "^"+entityName+"\s+(\S+)\s+(\S+).*$", tagString )
        if (m): return ( m.group(1), m.group(2) )
    return None


def evaluateMainAttribsFscoreStrict(entityName, ann_sug, ann_ref, mapping_sug_to_ref, mapping_ref_to_sug):
    ''' Evaluates main attribute annotations calculating F-scores:
           Recall    = correct / all_in_ref       
           Precision = correct / all_suggestions  
           F-score   = ( 2 * precision * recall ) / (precision + recall)
        NB! Also penalizes for unmatching annotations: 
        if a suggestion has no alignment with some reference, suggestion's attributes are considered 
        redundant (thus lowering the precision);
        if a reference has no alignment with some suggestion, reference's attributes are considered 
        missing (thus lowering the recall);
        Assumes that UNK in the place of attribute has a special meaning - missing attribute;
    '''
    correct    = dict()
    all_in_ref = dict()
    all_in_sug = dict()
    matched_ref = dict()
    for sugID in sorted(ann_sug.keys()):
        headerFound1 = False
        for [sentenceID_a, wordID_a, expression_a, annotation_a] in ann_sug[sugID]:
            if isEntityHeader(annotation_a):
                headerFound1 = True
                attribs1 = getEntityAttribs(entityName, annotation_a)
                # Record initial counts of attributes
                if (attribs1 and entityName == "EVENT"):
                    if (attribs1 != "UNK"):
                        incCount(all_in_sug, 'class')
                if (attribs1 and entityName == "TIMEX"):
                    if (attribs1[0] != "UNK"):
                        incCount(all_in_sug, 'type')
                    if (attribs1[1] != "UNK"):
                        incCount(all_in_sug, 'value')
                # If there is an aligned annotation, determine and record the overlap
                if (sugID in mapping_sug_to_ref):
                    matchFound = False
                    for refID in mapping_sug_to_ref[sugID]:
                        headerFound2 = False
                        for [sentenceID_b, wordID_b, expression_b, annotation_b] in ann_ref[refID]:
                            if isEntityHeader(annotation_b) and refID not in matched_ref:
                                headerFound2 = True
                                attribs2 = getEntityAttribs(entityName, annotation_b)
                                if (attribs2 and entityName == "EVENT"):
                                    if (attribs2 != "UNK" and attribs1 == attribs2):
                                        incCount(correct, 'class')
                                if (attribs2 and entityName == "TIMEX"):
                                    if (attribs2[0] != "UNK" and attribs1[0] == attribs2[0]):
                                        incCount(correct, 'type')
                                    if (attribs2[1] != "UNK" and attribs1[1] == attribs2[1]):
                                        incCount(correct, 'value')
                                # Remember that this reference has been counted already ...
                                matched_ref[refID] = True
                                matchFound = True
                                break
                        if matchFound:
                            break
    for refID in sorted(ann_ref.keys()):
        headerFound1 = False
        for [sentenceID_a, wordID_a, expression_a, annotation_a] in ann_ref[refID]:
            if isEntityHeader(annotation_a):
                attribs1 = getEntityAttribs(entityName, annotation_a)
                if (attribs1 and entityName == "EVENT"):
                    if (attribs1 != "UNK"):
                        incCount(all_in_ref, 'class')
                if (attribs1 and entityName == "TIMEX"):
                    if (attribs1[0] != "UNK"):
                        incCount(all_in_ref, 'type')
                    if (attribs1[1] != "UNK"):
                        incCount(all_in_ref, 'value')
    rec    = dict()
    prec   = dict()
    fscore = dict()
    attribs = []
    if (entityName == "EVENT"):
        attribs = ["class"]
    elif (entityName == "TIMEX"):
        attribs = ["type", "value"]
    for attrib in attribs:
        if (attrib not in correct):
            correct[attrib] = 0
        if (attrib not in all_in_ref):
            all_in_ref[attrib] = 0
            rec[attrib] = 0.0
        if (attrib not in all_in_sug):
            all_in_sug[attrib] = 0
            prec[attrib] = 0.0
        if (all_in_ref[attrib] > 0):
            rec[attrib] = correct[attrib] / all_in_ref[attrib]
        if (all_in_sug[attrib] > 0):
            prec[attrib] = correct[attrib] / all_in_sug[attrib]
        if (prec[attrib] > 0 or rec[attrib] > 0):
            fscore[attrib] = ( 2 * prec[attrib] * rec[attrib] ) / (prec[attrib] + rec[attrib])
        else:
            fscore[attrib] = 0.0
    return (correct, all_in_ref, all_in_sug, rec, prec, fscore)


def evaluateMainAttribsFscore(entityName, ann_sug, ann_ref, mapping_sug_to_ref, mapping_ref_to_sug, oneBestMatch=True):
    ''' Evaluates main attribute annotations calculating F-scores:
           Recall    = correct / all_in_ref       
           Precision = correct / all_suggestions  
           F-score   = ( 2 * precision * recall ) / (precision + recall)
        Evaluates attributes only on annotations that have been successfully aligned;
        Assumes that UNK in the place of attribute has a special meaning - missing attribute;
        
        If oneBestMatch=True, each sug_annotation is aligned with one ref_annotation with the largest
        token overlap in the extent;
    '''
    correct     = dict()
    all_in_ref  = dict()
    all_in_sug  = dict()
    if oneBestMatch:
        #  Align each suggested annotation with exactly one reference annotation, picking the
        # annotation with the largest extent
        for sugID in sorted(ann_sug.keys()):
            # Count only annotations that have been successfully aligned
            if (sugID in mapping_sug_to_ref and len(mapping_sug_to_ref[sugID]) > 0):
                # 1) Find one best match / alignment
                tokens_sug = set([ phrase[1] for phrase in ann_sug[sugID] ])
                biggest_overlap = 0
                best_match      = None
                for refID in sorted( mapping_sug_to_ref[sugID] ):
                    # Find, how many of the tokens are matching
                    tokens_ref = set([ phrase[1] for phrase in ann_ref[refID] ])
                    common = len(tokens_sug.intersection(tokens_ref))
                    if common > biggest_overlap:
                        biggest_overlap = common
                        best_match = refID
                if not best_match:
                    raise Exception('(!) Unexpectedly, the best match was not found for: '+str(ann_sug[sugID]))
                
                # 2) Find headers of both annotations 
                header_annotation_sug = None
                header_annotation_ref = None
                for [sentenceID_a, wordID_a, expression_a, annotation_a] in ann_sug[sugID]:
                    if isEntityHeader(annotation_a):
                        header_annotation_sug = annotation_a
                for [sentenceID_b, wordID_b, expression_b, annotation_b] in ann_ref[best_match]:
                    if isEntityHeader(annotation_b):
                        header_annotation_ref = annotation_b
                if not header_annotation_sug:
                    raise Exception('(!) Unexpectedly, header annotation not found for: '+str(ann_sug[sugID]))
                if not header_annotation_ref:
                    raise Exception('(!) Unexpectedly, header annotation not found for: '+str(ann_ref[best_match]))

                #print('aligning: '+str(ann_sug[sugID]))
                #print('   alignment: '+str(ann_ref[best_match]))
                
                # 3) Record counts / matches
                attribs1 = getEntityAttribs(entityName, header_annotation_sug)
                # Record initial counts of attributes
                if (attribs1 and entityName == "EVENT"):
                    if (attribs1 != "UNK"):
                        incCount(all_in_sug, 'class')
                if (attribs1 and entityName == "TIMEX"):
                    if (attribs1[0] != "UNK"):
                        incCount(all_in_sug, 'type')
                    if (attribs1[1] != "UNK"):
                        incCount(all_in_sug, 'value')
                attribs2 = getEntityAttribs(entityName, header_annotation_ref)
                if (attribs2 and entityName == "EVENT"):
                    if (attribs2 != "UNK"):
                        incCount(all_in_ref, 'class')
                    if (attribs2 != "UNK" and attribs1 == attribs2):
                        incCount(correct, 'class')
                if (attribs2 and entityName == "TIMEX"):
                    if (attribs2[0] != "UNK"):
                        incCount(all_in_ref, 'type')
                    if (attribs2[0] != "UNK" and attribs1[0] == attribs2[0]):
                        incCount(correct, 'type')
                    if (attribs2[1] != "UNK"):
                        incCount(all_in_ref, 'value')
                    if (attribs2[1] != "UNK" and attribs1[1] == attribs2[1]):
                        incCount(correct, 'value')
    else:
        #   The old / flawed way of calculating: one sug can be aligned to multiple refs,
        #  which seems to result in suprious counting, e.g. suggested annotations are 
        #  counted even if they have no mappings to references ...
        matched_ref = dict()
        for sugID in sorted(ann_sug.keys()):
            # Count only annotations that have been successfully aligned
            if (sugID in mapping_sug_to_ref):  # <-- Problem! mapping_sug_to_ref[sugID] can be empty ...
                headerFound1 = False
                for [sentenceID_a, wordID_a, expression_a, annotation_a] in ann_sug[sugID]:
                    if isEntityHeader(annotation_a):
                        #print('aligning: '+str(ann_sug[sugID]))
                        headerFound1 = True
                        attribs1 = getEntityAttribs(entityName, annotation_a)
                        # Record initial counts of attributes
                        if (attribs1 and entityName == "EVENT"):
                            if (attribs1 != "UNK"):
                                incCount(all_in_sug, 'class')
                        if (attribs1 and entityName == "TIMEX"):
                            if (attribs1[0] != "UNK"):
                                incCount(all_in_sug, 'type')
                            if (attribs1[1] != "UNK"):
                                incCount(all_in_sug, 'value')
                        matchFound = False
                        for refID in mapping_sug_to_ref[sugID]:
                            headerFound2 = False
                            for [sentenceID_b, wordID_b, expression_b, annotation_b] in ann_ref[refID]:
                                if isEntityHeader(annotation_b) and refID not in matched_ref:
                                    headerFound2 = True
                                    attribs2 = getEntityAttribs(entityName, annotation_b)
                                    #print('   alignment: '+str(ann_ref[refID]))
                                    if (attribs2 and entityName == "EVENT"):
                                        if (attribs2 != "UNK"):
                                            incCount(all_in_ref, 'class')
                                        if (attribs2 != "UNK" and attribs1 == attribs2):
                                            incCount(correct, 'class')
                                    if (attribs2 and entityName == "TIMEX"):
                                        if (attribs2[0] != "UNK"):
                                            incCount(all_in_ref, 'type')
                                        if (attribs2[0] != "UNK" and attribs1[0] == attribs2[0]):
                                            incCount(correct, 'type')
                                        if (attribs2[1] != "UNK"):
                                            incCount(all_in_ref, 'value')
                                        if (attribs2[1] != "UNK" and attribs1[1] == attribs2[1]):
                                            incCount(correct, 'value')
                                    # Remember that this reference has been counted already ...
                                    matched_ref[refID] = True
                                    matchFound = True
                                    break
                        if matchFound:
                            break

    rec    = dict()
    prec   = dict()
    fscore = dict()
    attribs = []
    if (entityName == "EVENT"):
        attribs = ["class"]
    elif (entityName == "TIMEX"):
        attribs = ["type", "value"]
    for attrib in attribs:
        if (attrib not in correct):
            correct[attrib] = 0
        if (attrib not in all_in_ref):
            all_in_ref[attrib] = 0
            rec[attrib] = 0.0
        if (attrib not in all_in_sug):
            all_in_sug[attrib] = 0
            prec[attrib] = 0.0
        if (all_in_ref[attrib] > 0):
            rec[attrib] = correct[attrib] / all_in_ref[attrib]
        if (all_in_sug[attrib] > 0):
            prec[attrib] = correct[attrib] / all_in_sug[attrib]
        if (prec[attrib] > 0 or rec[attrib] > 0):
            fscore[attrib] = ( 2 * prec[attrib] * rec[attrib] ) / (prec[attrib] + rec[attrib])
        else:
            fscore[attrib] = 0.0
    return (correct, all_in_ref, all_in_sug, rec, prec, fscore)


def compAnnotationAttribsFscore(entityName, annotator_sug, annotator_ref, annotationsByID_sug, annotationsByID_ref, counter, multipleStrategy = 'largest', countOnlyAligned = False ):
    ''' Aligns annotations of two annotators, calculates inter-annotator agreements on
        attributes, and returns formatted results;
        If countOnlyAligned == True, then agreements are only calculated on aligned 
        annotations and unaligned annotations won't affect the result. 
        Otherwise, a strict way for computing the agreement is used, where disagreements 
        on extent also penalize the attribute's agreement score.
    '''
    pair = annotator_sug+" vs "+annotator_ref
    # Create mappings between two sets of annotations 
    # (suggested annotations and reference annotations)
    (mapping_sug_to_ref, mapping_ref_to_sug) = findAnnotationMappings(annotationsByID_sug, annotationsByID_ref, multipleStrategy)
    #debugDisplayMappings(annotations_sug, annotations_ref, mapping_sug_to_ref, mapping_ref_to_sug)
    
    (correct, all_in_ref, all_in_sug, rec, prec, fscore) = \
        evaluateMainAttribsFscore(entityName, annotationsByID_sug, annotationsByID_ref, mapping_sug_to_ref, mapping_ref_to_sug) \
        if countOnlyAligned else \
        evaluateMainAttribsFscoreStrict(entityName, annotationsByID_sug, annotationsByID_ref, mapping_sug_to_ref, mapping_ref_to_sug)

    results = dict()
    if (len(correct.keys()) > 0):
        for k in correct.keys():
            counter.addToCount(entityName+"-"+k, pair, "correct", correct[k])
            counter.addToCount(entityName+"-"+k, pair, "all_in_ref", all_in_ref[k])
            counter.addToCount(entityName+"-"+k, pair, "all_in_sug", all_in_sug[k])
            if ( all_in_ref[k] + all_in_sug[k] > 0 ):
                rec_f    = '{:.3}'.format( rec[k]  )
                prec_f   = '{:.3}'.format( prec[k] )
                fscore_f = '{:.3}'.format( fscore[k] )
                results[entityName+"-"+k] = (" "*7)+pair+"  "+entityName+"-"+k+" "+"   R: "+rec_f+"   P: "+prec_f+"   F: "+fscore_f
    return (results, pair)

# ============================================================
# ============================================================
#     Record tlink agreement counts
# ============================================================
# ============================================================

def mergeRelation(relation, rel_merging, unknownToVague = True):
    ''' Merges semantically similar relations:
        *) "rel_3_1", "rel_3_1_vague":
           "SIMULTANEOUS", "INCLUDES", "IS_INCLUDED", "IDENTITY" => "OVERLAP"
           "OVERLAP-OR-AFTER" => "AFTER"
           "BEFORE-OR-OVERLAP" => "BEFORE"
           UNK => "VAGUE"
        *) "rel_3_1_vague":
           "VAGUE" => "OVERLAP"
        *) "rel_3_2", "rel_3_2_vague":
           "SIMULTANEOUS", "INCLUDES", "IS_INCLUDED", "IDENTITY" => "OVERLAP"
           "OVERLAP-OR-AFTER" => "OVERLAP"
           "BEFORE-OR-OVERLAP" => "OVERLAP"
           UNK => "VAGUE"
        *) "rel_3_2_vague":
           "VAGUE" => "OVERLAP"
        *) "rel_ovrl":
           "SIMULTANEOUS", "INCLUDES", "IS_INCLUDED", "IDENTITY" => "OVERLAP"
    '''
    if (rel_merging == "rel_3_1" or rel_merging == "rel_3_1_vague"):
        if (relation == "SIMULTANEOUS" or relation == "INCLUDES" or relation == "IS_INCLUDED" or relation == "IDENTITY"):
            return "OVERLAP"
        elif (relation == "OVERLAP-OR-AFTER"):
            return "AFTER"
        elif (relation == "BEFORE-OR-OVERLAP"):
            return "BEFORE"
        elif (unknownToVague and not re.match("^\s*(OVERLAP|BEFORE|AFTER|VAGUE|IDENTITY)\s*$", relation)):
            return "VAGUE"
        elif (relation == "VAGUE" and rel_merging == "rel_3_1_vague"):
            return "OVERLAP"
    elif (rel_merging == "rel_3_2" or rel_merging == "rel_3_2_vague"):
        if (relation == "SIMULTANEOUS" or relation == "INCLUDES" or relation == "IS_INCLUDED" or relation == "IDENTITY"):
            return "OVERLAP"
        elif (relation == "OVERLAP-OR-AFTER"):
            return "OVERLAP"
        elif (relation == "BEFORE-OR-OVERLAP"):
            return "OVERLAP"
        elif (unknownToVague and not re.match("^\s*(OVERLAP|BEFORE|AFTER|VAGUE|IDENTITY)\s*$", relation)):
            return "VAGUE"
        elif (relation == "VAGUE" and rel_merging == "rel_3_2_vague"):
            return "OVERLAP"
    elif (rel_merging == "rel_ovrl"):
        if (relation == "SIMULTANEOUS" or relation == "INCLUDES" or relation == "IS_INCLUDED" or relation == "IDENTITY"):
            return "OVERLAP"
    return relation


def makeCommCorrection(relationA, relationB):
    ''' Makes a correction on relations, assuming that entities have 
        been switched: 
            the first relation is in form    X  relationA  Y
            the second relation is in form   Y  relationB  X
        If the switch causes both relations to match, returns corrected
        relations as a tuple: (relationA, relationA), otherwise returns
        (relationA, relationB);
        Considers only cases:
            A BEFORE B    ==  B AFTER A
            A INCLUDES B  ==  B IS_INCLUDED A
    ''' 
    if relationA=='BEFORE' and relationB=='AFTER':
        return ('BEFORE', 'BEFORE')
    elif relationA=='AFTER' and relationB=='BEFORE':
        return ('AFTER', 'AFTER')
    elif relationA=='INCLUDES' and relationB=='IS_INCLUDED':
        return ('INCLUDES', 'INCLUDES')
    elif relationA=='IS_INCLUDED' and relationB=='INCLUDES':
        return ('IS_INCLUDED', 'IS_INCLUDED')
    else:
        return (relationA, relationB)


def getAnnotatorPairs(annotatorLabels):
    ''' Returns all possible annotator pairings as a list.
    '''
    annotators = sorted(annotatorLabels, reverse=True)
    pairs = []
    if (len(annotators) == 2):
        pairs = [ (annotators[0], annotators[1]) ]
    elif (len(annotators) == 3):
        pairs = [ (annotators[0], annotators[1]), \
                  (annotators[1], annotators[2]), \
                  (annotators[0], annotators[2]) ]
    elif (len(annotators) == 4):
        pairs = [ (annotators[0], annotators[1]), \
                  (annotators[1], annotators[2]), \
                  (annotators[2], annotators[3]), \
                  (annotators[0], annotators[3]), \
                  (annotators[1], annotators[3]), \
                  (annotators[0], annotators[2]) ]
    return pairs


def record_tlinks_matches(allRelations, layer, rel_merging, counter, fileToAnnotators, \
                          applyCommCorrect=False):
    ''' Finds all the tlink matches between (all pairs of) annotators on the 
        given layer, and records the counts (matches and mismatches) into the 
        counter.
        Assumes that allRelations is a dict, where annotator names are the keys
        and values are lists of corresponding tlink annotations, and each list 
        has elements with the structure:
            [file, entityA, relation, entityB, comment]
        
        If applyCommCorrect=True, then the method attempts to detect cases
        where the annotators have switched the entities (e.g. "A BEFORE B" vs
        "B AFTER A"), and considers these cases still correctly matching 
        ones ("A BEFORE B" == "B AFTER A"); (NB! Considering these cases seems 
        to have only a minor effect on the overall results);
    '''
    allPairs = getAnnotatorPairs( ['a','b','c','j'] )
    # Divide relations into groups by files
    fileToRels       = dict()
    for annotator in allRelations:
        for [file, entityA, relation, entityB, comment] in allRelations[annotator]:
            if file not in fileToRels:
                fileToRels[file] = []
            fileToRels[file].append( [annotator, entityA, relation, entityB, comment] )
    # Count agreements for each annotator pair
    for (a, b) in allPairs:
        pair = a+" vs "+b
        for file in fileToRels:
            if a not in fileToAnnotators[file] or b not in fileToAnnotators[file]:
                #  If one of the annotators was not tasked to annotate the file,
                #  skip the counting on that file;
                continue
            for i in range(len(fileToRels[file])):
                relation1 = fileToRels[file][i]
                if (relation1[0] == a):
                    counter.addToCount("tlink-"+layer+"-find", pair, "all_in_ref", 1)
                if (relation1[0] == b):
                    counter.addToCount("tlink-"+layer+"-find", pair, "all_in_sug", 1)
                keyList1 = sorted([ relation1[1], relation1[3] ])
                key1 = keyList1[0]+"_"+keyList1[1]
                if relation1[0] == a:
                    # Find whether we have a matching relation from the other annotator
                    for j in range(len(fileToRels[file])):
                        relation2 = fileToRels[file][j]
                        if relation2[0] == b:
                            keyList2 = sorted([ relation2[1], relation2[3] ])
                            key2 = keyList2[0]+"_"+keyList2[1]
                            if (key1 == key2):
                                #
                                # Entities of both relations are matching, so we know
                                # that at least both annotators draw a relation in
                                # that place
                                #
                                counter.addToCount("tlink-"+layer+"-find", pair, "correct", 1)
                                counter.addToCount("tlink-"+layer+"-rel_match-"+rel_merging, pair, "all", 1)

                                # The next question is: whether the relation type is also
                                # matching?
                                relType1 = relation1[2]
                                relType2 = relation2[2]
                                if relation1[1] != relation2[1] and applyCommCorrect:
                                    #
                                    #   The order of the entities is different, i.e.
                                    #   we have the case:
                                    #        A relation1 B     vs     B relation2 A
                                    #   Attempt to make some corrections, if relation1
                                    #   and relation2 represent clear opposite relations
                                    #   (e.g.    A AFTER B     vs     B BEFORE A   );
                                    #
                                    (relType1, relType2) = \
                                        makeCommCorrection(relType1, relType2)
                                    #
                                    #    NB! Some of the cases remain uncorrected, e.g. 
                                    #       A BEFORE-OR-OVERLAP B   vs   B AFTER A
                                    #
                                
                                #
                                #   If required (specified in rel_merging), try to merge 
                                #  semantically similar relations;
                                #
                                relType1 = mergeRelation(relType1, rel_merging)
                                relType2 = mergeRelation(relType2, rel_merging)

                                ia_agreements_chance_corrected.update_contingency_table( \
                                    a, b, relType1, relType2, counter, \
                                    "tlink-"+layer+"-rel_match-"+rel_merging, pair)
                                if (relType1 == relType2):
                                    counter.addToCount("tlink-"+layer+"-rel_match-"+rel_merging, pair, "agree", 1)
                                break


# ============================================================
# ============================================================
#     Aggregate and display the results
# ============================================================
# ============================================================

def printAggregateResults(counter, details = False, judge = None, findGroupAvgs = False):
    '''  Calculates aggregate results for entity (EVENT, TIMEX) annotation agreement,
         and outputs these results to the stdout.
         Uses the counts from counter;
    '''
    results = counter.getCounts()
    if (details):
        print ("--------------")
        print (" Details")
        print ("--------------")
        # Output numbers of files counted
        for evalPhase in sorted(results.keys()):
            if (re.match("^.*-extent$", evalPhase)):
                for pair in counter.getSortedPairs(evalPhase, judge):
                    files = counter.getCount(evalPhase, pair, "counted_files")
                    string = (" "*7)+pair+"  "+evalPhase+" files: "+str(files)
                    print (string)
            print()
        # Output detailed precisions/recalls
        for evalPhase in sorted(results.keys()):
            if (re.match("^.*-extent$", evalPhase)):
                for pair in counter.getSortedPairs(evalPhase, judge):
                    correct = counter.getCount(evalPhase, pair, "correct")
                    all_in_ref = counter.getCount(evalPhase, pair, "all_in_ref")
                    all_in_sug = counter.getCount(evalPhase, pair, "all_in_sug")
                    if all_in_ref > 0:
                        rec  = correct / all_in_ref
                    else:
                        rec  = 0.0
                    if all_in_sug > 0:
                        prec = correct / all_in_sug
                    else:
                        prec = 0.0
                    if prec+rec > 0:
                        fscore = (2*prec*rec) / (prec+rec)
                    else:
                        fscore = 0.0
                    if ( all_in_ref + all_in_sug > 0 ):
                        rec_f    = '{:.3}'.format( rec  )
                        prec_f   = '{:.3}'.format( prec )
                        fscore_f = '{:.3}'.format( fscore )
                        string = (" "*7)+pair+"  "+evalPhase+" "+\
                                "   R: "+str(correct)+"/"+str(all_in_ref)+\
                                "   P: "+str(correct)+"/"+str(all_in_sug)
                        print (string)
            print()
        for evalPhase in sorted(results.keys()):
            if (not re.match("^.*-extent$", evalPhase)):
                for pair in counter.getSortedPairs(evalPhase, judge):
                    correct = counter.getCount(evalPhase, pair, "correct")
                    all_in_ref = counter.getCount(evalPhase, pair, "all_in_ref")
                    all_in_sug = counter.getCount(evalPhase, pair, "all_in_sug")
                    if all_in_ref > 0:
                        rec  = correct / all_in_ref
                    else:
                        rec  = 0.0
                    if all_in_sug > 0:
                        prec = correct / all_in_sug
                    else:
                        prec = 0.0
                    if prec+rec > 0:
                        fscore = (2*prec*rec) / (prec+rec)
                    else:
                        fscore = 0.0
                    if ( all_in_ref + all_in_sug > 0 ):
                        rec_f    = '{:.3}'.format( rec  )
                        prec_f   = '{:.3}'.format( prec )
                        fscore_f = '{:.3}'.format( fscore )
                        string = (" "*7)+pair+"  "+evalPhase+" "+\
                                "   R: "+str(correct)+"/"+str(all_in_ref)+\
                                "   P: "+str(correct)+"/"+str(all_in_sug)
                        print (string)
            print()
        print ("--------------")
    # K6igepealt extent
    for evalPhase in sorted(results.keys()):
        if (re.match("^.*-extent$", evalPhase)):
            groupScores = []
            judgeScoreReached = False
            for pair in counter.getSortedPairs(evalPhase, judge):
                correct = counter.getCount(evalPhase, pair, "correct")
                all_in_ref = counter.getCount(evalPhase, pair, "all_in_ref")
                all_in_sug = counter.getCount(evalPhase, pair, "all_in_sug")
                if all_in_ref > 0:
                    rec  = correct / all_in_ref
                else:
                    rec  = 0.0
                if all_in_sug > 0:
                    prec = correct / all_in_sug
                else:
                    prec = 0.0
                if prec+rec > 0:
                    fscore = (2*prec*rec) / (prec+rec)
                else:
                    fscore = 0.0
                if (findGroupAvgs and judge in pair and not judgeScoreReached):
                    avg_f = fsum(groupScores)/len(groupScores)
                    fscore_f = '{:.3}'.format( avg_f )
                    string = (" "*20)+"  "+evalPhase+" "+(" "*24)+"F1_avg: "+fscore_f
                    print (string)
                    groupScores = []
                    judgeScoreReached = True
                groupScores.append(fscore)
                if ( all_in_ref + all_in_sug > 0 ):
                    rec_f    = '{:.3}'.format( rec  )
                    prec_f   = '{:.3}'.format( prec )
                    fscore_f = '{:.3}'.format( fscore )
                    string = (" "*7)+pair+"  "+evalPhase+" "+\
                           "   R: "+rec_f+"   P: "+prec_f+"   F1: "+fscore_f
                    print (string)
            if (findGroupAvgs):
                avg_f = fsum(groupScores)/len(groupScores)
                fscore_f = '{:.3}'.format( avg_f )
                string = (" "*20)+"  "+evalPhase+" "+(" "*24)+"F1_avg: "+fscore_f
                print (string)
                groupScores = []
        print()

    # Seej2rel teised atribuudid
    for evalPhase in sorted(results.keys()):
        if (not re.match("^.*-extent$", evalPhase) and not re.match("^.+-acc-.+$", evalPhase)):
            groupScores = []
            judgeScoreReached = False
            for pair in counter.getSortedPairs(evalPhase, judge):
                # Precision, Recall, F1-score
                correct = counter.getCount(evalPhase, pair, "correct")
                all_in_ref = counter.getCount(evalPhase, pair, "all_in_ref")
                all_in_sug = counter.getCount(evalPhase, pair, "all_in_sug")
                if all_in_ref > 0:
                    rec  = correct / all_in_ref
                else:
                    rec  = 0.0
                if all_in_sug > 0:
                    prec = correct / all_in_sug
                else:
                    prec = 0.0
                if prec+rec > 0:
                    fscore = (2*prec*rec) / (prec+rec)
                else:
                    fscore = 0.0
                if (findGroupAvgs and judge in pair and not judgeScoreReached):
                    avg_f = fsum(groupScores)/len(groupScores)
                    fscore_f = '{:.3}'.format( avg_f )
                    string = (" "*20)+"  "+evalPhase+" "+(" "*24)+"F1_avg: "+fscore_f
                    print (string)
                    groupScores = []
                    judgeScoreReached = True
                groupScores.append(fscore)
                if ( all_in_ref + all_in_sug > 0 ):
                    rec_f    = '{:.3}'.format( rec  )
                    prec_f   = '{:.3}'.format( prec )
                    fscore_f = '{:.3}'.format( fscore )
                    string = (" "*7)+pair+"  "+evalPhase+" "+\
                           "   R: "+rec_f+"   P: "+prec_f+"   F1: "+fscore_f
                    print (string)
            if (findGroupAvgs):
                avg_f = fsum(groupScores)/len(groupScores)
                fscore_f = '{:.3}'.format( avg_f )
                string = (" "*20)+"  "+evalPhase+" "+(" "*24)+"F1_avg: "+fscore_f
                print (string)
                groupScores = []
        print()


def getSubListOfNumbers(list, startIndex, endIndex ):
    ''' Fetches all the numbers from described sublist, discards NA values. '''
    sublist = list[startIndex : (endIndex+1)]
    filtered = []
    hasNAs = ""
    for a in sublist:
        if ( isinstance(a, int) or isinstance(a, float) ):
            filtered.append( a )
        else:
            hasNAs += "*"
    return ( filtered, hasNAs )


def aggregateAndPrintFilteringResults(counter, filterKey, judge = None, onlyTlinkBase = True, \
                                                                        addCohensKappa = True):
    '''  Calculates aggregate results for EVENT annotation agreement,
         and TLINK annotation agreements, and outputs these results to the stdout.
         Uses the counts from counter;
    '''
    results = counter.getCounts()
    findGroupAvgs = True
    # -----------------------------------------------
    #   gathering and aggregating data : EVENTs
    # -----------------------------------------------
    allEventScores = dict()
    allConfTables  = dict()
    for evalPhase in sorted(results.keys()):
        allFscores      = []
        allFscoresAnns  = []
        allFscoresJudge = []
        if (re.match("^EVENT-.*", evalPhase) and not re.match("^EVENT-extent-K", evalPhase)):
            if (evalPhase not in allEventScores):
                allEventScores[evalPhase] = dict()
            for pair in counter.getSortedPairs(evalPhase, judge):
                # F-score
                correct = counter.getCount(evalPhase, pair, "correct")
                all_in_ref = counter.getCount(evalPhase, pair, "all_in_ref")
                all_in_sug = counter.getCount(evalPhase, pair, "all_in_sug")
                if all_in_ref > 0:
                    rec  = correct / all_in_ref
                else:
                    rec  = -1.0
                if all_in_sug > 0:
                    prec = correct / all_in_sug
                else:
                    prec = -1.0
                if prec+rec > 0:
                    fscore = (2*prec*rec) / (prec+rec)
                else:
                    fscore = -1.0
                isJudgeScore = False
                if (judge and judge in pair):
                    allFscoresJudge.append(fscore)
                    isJudgeScore = True
                else:
                    allFscoresAnns.append(fscore)
                allFscores.append(fscore)
                if (pair not in allEventScores[evalPhase]):
                    allEventScores[evalPhase][pair] = []
                allEventScores[evalPhase][pair].extend([ rec, prec, fscore, isJudgeScore, -1.0, -1.0])
                # Accuracy (EVENT class)
                if (evalPhase == "EVENT-class"):
                    correct = counter.getCount(evalPhase, pair, "acc_correct")
                    all     = counter.getCount(evalPhase, pair, "acc_all")
                    if all > 0:
                        acc = correct/all
                    else:
                        acc = -1.0
                    allEventScores[evalPhase][pair][4] = acc
                    allEventScores[evalPhase][pair][5] = 0.0
        if (len(allFscores) > 0):
            allEventScores[evalPhase]["_all_groups"] = fsum(allFscores)/len(allFscores)
        if (len(allFscoresAnns) > 0):
            allEventScores[evalPhase]["_annotator_groups"] = fsum(allFscoresAnns)/len(allFscoresAnns)
        if (len(allFscoresJudge) > 0):
            allEventScores[evalPhase]["_judge_groups"] = fsum(allFscoresJudge)/len(allFscoresJudge)

    allAnnosEventsRemaining = 0
    allAnnosEventsTotal     = 0
    allAnnosEventsCoverage  = -1.0
    if ("total-count-remaining-events" in results.keys()):
        allAnnosEventsRemaining = counter.getCount("total-count-remaining-events", "_all_uniq_anns", "_")
        allAnnosEventsTotal = counter.getCount("total-count-events", "_all_uniq_anns", "_")
        allAnnosEventsCoverage = (allAnnosEventsRemaining*100.0)/allAnnosEventsTotal

    annoVagueProportion = -1.0
    allAnnosLinks      = 0
    allAnnosVagueLinks = 0
    allAnnosTLINKCoverage = -1.0
    if ("total-count-remaining-tlinks" in results.keys()):
        for annotator in counter.getSortedPairs("total-count-remaining-tlinks", judge=None):
            if (annotator in ["_all"]):
                continue
            allAnnotatorLinks   = counter.getCount("total-count-remaining-tlinks", annotator, "_")
            vagueAnnotatorLinks = counter.getCount("total-count-remaining-tlinks", annotator, "_vague")
            if (judge and annotator != judge):
                allAnnosLinks += allAnnotatorLinks
                allAnnosVagueLinks += vagueAnnotatorLinks
        annoVagueProportion = (allAnnosVagueLinks*100.0)/allAnnosLinks
    allAnnosLinksTotal = 0
    if ("total-count-tlinks" in results.keys()):
        for annotator in counter.getSortedPairs("total-count-tlinks", judge=None):
            if (annotator in ["_all"]):
                continue
            allAnnotatorLinks = counter.getCount("total-count-tlinks", annotator, "_")
            if (judge and annotator != judge):
                allAnnosLinksTotal += allAnnotatorLinks
    if (allAnnosLinksTotal > 0):
        allAnnosTLINKCoverage = (allAnnosLinks*100.0)/allAnnosLinksTotal

    # -----------------------------------------------
    #   display long output: event annotation
    # -----------------------------------------------
    print (("="*35))
    print ("  Detailed results for EVENTs ("+filterKey+")")
    print (("="*35))
    # EVENT 
    for evalPhase in [ "EVENT-extent", "EVENT-class" ]:
        #  annotators
        for pair in sorted( allEventScores[evalPhase].keys() ):
            if (pair in ["_annotator_groups", "_judge_groups", "_all_groups"]):
                continue
            [ rec, prec, fscore, isJudgeScore, acc, kappa ] = allEventScores[evalPhase][pair]
            if (not isJudgeScore):
                rec_f    = '{:.3}'.format( rec  )
                prec_f   = '{:.3}'.format( prec )
                fscore_f = '{:.3}'.format( fscore )
                out_string = (" "*7)+pair+"  "+evalPhase+" "+\
                          "   R: "+rec_f+"   P: "+prec_f+"   F1: "+fscore_f
                if (acc > 0.0):
                    out_string += "   Acc: "+'{:.3}'.format( acc )
                if (kappa > 0.0):
                    out_string += "   K: "+'{:.3}'.format( kappa )
                print (out_string)
        total_fscore_f = '{:.3}'.format( allEventScores[evalPhase]["_annotator_groups"] )
        out_string = (" "*20)+"  "+evalPhase+" "+(" "*24)+"F1_avg: "+total_fscore_f
        print (out_string)
        #   judge
        for pair in sorted( allEventScores[evalPhase].keys() ):
            if (pair in ["_annotator_groups", "_judge_groups", "_all_groups"]):
                continue
            [ rec, prec, fscore, isJudgeScore, acc, kappa ] = allEventScores[evalPhase][pair]
            if (isJudgeScore):
                rec_f    = '{:.3}'.format( rec  )
                prec_f   = '{:.3}'.format( prec )
                fscore_f = '{:.3}'.format( fscore )
                out_string = (" "*7)+pair+"  "+evalPhase+" "+\
                          "   R: "+rec_f+"   P: "+prec_f+"   F1: "+fscore_f
                if (acc > 0.0):
                    out_string += "   Acc: "+'{:.3}'.format( acc )
                if (kappa > 0.0):
                    out_string += "   K: "+'{:.3}'.format( kappa )
                print (out_string)
        total_fscore_f = '{:.3}'.format( allEventScores[evalPhase]["_judge_groups"] )
        out_string = (" "*20)+"  "+evalPhase+" "+(" "*24)+"F_avg: "+total_fscore_f
        print (out_string)
        print ()

    # -----------------------------------------------
    #   display short output: event annotation
    # -----------------------------------------------
    print (("="*35))
    print ("  Compact results for EVENTs ("+filterKey+")")
    print (("="*35))
    #  for entity agreement
    print ( (" "*7)+"all-in-one-EVENT  ",end="" )
    print ( " "+str(allAnnosEventsRemaining)+" ("+'{:.4}'.format( allAnnosEventsCoverage )+"%)", end="" )
    print ( " "+str(allAnnosLinks)+" ("+'{:.4}'.format( allAnnosTLINKCoverage )+"%) ", end="" )
    print ("|", end="")
    print (" "+'{:.3}'.format(allEventScores["EVENT-extent"]["_annotator_groups"]), end="")
    print ("  "+'{:.3}'.format(allEventScores["EVENT-class"]["_annotator_groups"]), end="")
    #print (" | ", end="")
    #print (" "+'{:.3}'.format( totalTLINKFscoresAnnsExcl2 ), end="")
    print ()
    print ()

    # -----------------------------------------------
    #   gathering and aggregating data : TLINKs
    # -----------------------------------------------
    #
    # ****  Precision/Recall on choosing entities for tlinks
    #
    allTLINKFscores = []
    allPairsSorted  = counter.getSortedPairs("tlink-event_dct-rel_match-base", judge)
    for tlinkLayer in ["event_timex", "event_dct", "main_events", "event_event"]:
        evalPhase = "tlink-"+tlinkLayer+"-find"
        if (evalPhase not in results.keys()):
            raise Exception(" Err: "+evalPhase+" not in listed evaluation phases.")
        for p in range(len(allPairsSorted)):
            pair = allPairsSorted[ p ]
            if (pair not in counter.getSortedPairs(evalPhase, judge)):
                allTLINKFscores.append("N/A")
                continue
            correct = counter.getCount(evalPhase, pair, "correct")
            all_in_ref = counter.getCount(evalPhase, pair, "all_in_ref")
            all_in_sug = counter.getCount(evalPhase, pair, "all_in_sug")
            isJudgeScore = True
            if (judge == None or (judge and judge not in pair)):
                isJudgeScore = False
                if all_in_ref > 0:
                    rec  = correct / all_in_ref
                else:
                    rec  = -1.0
                if all_in_sug > 0:
                    prec = correct / all_in_sug
                else:
                    prec = -1.0
                if prec+rec > 0:
                    fscore = (2*prec*rec) / (prec+rec)
                else:
                    fscore = "N/A"
                allTLINKFscores.append( fscore )

    allTLINKrelTypeDetails = dict()
    allTLINKaccs          = []
    allTLINKaccs_weighted = []
    allTLINKccs           = []
    allTLINKvagueRelCount = []
    allTLINKconfTables    = []
    allTLINKcounts        = []
    #
    # ****  Accuracy on deciding the relType
    #
    for tlinkLayer in ["event_timex", "event_dct", "main_events", "event_event"]:
        evalPhase = "tlink-"+tlinkLayer+"-rel_match-base"
        if (evalPhase not in results.keys()):
            raise Exception(" Err: "+evalPhase+" not in listed evaluation phases.")
        for p in range(len(allPairsSorted)):
            pair = allPairsSorted[ p ]
            if (pair not in counter.getSortedPairs(evalPhase, judge)):
                #  In case all relations were removed / filtered out, insert 
                #  'N/A' values as placeholders;
                allTLINKaccs.append("N/A")
                allTLINKaccs_weighted.append("N/A")
                allTLINKccs.append("N/A")
                allTLINKvagueRelCount.append(0)
                allTLINKcounts.append(0)
                detailed = [ evalPhase, "N/A", "N/A", "N/A", False, "N/A" ]
                if (tlinkLayer not in allTLINKrelTypeDetails):
                    allTLINKrelTypeDetails[tlinkLayer] = dict()
                allTLINKrelTypeDetails[tlinkLayer][pair] = detailed
                confTable = dict()
                allTLINKconfTables.append( confTable )
                print (" WARN: '"+tlinkLayer+"' results not available for pair '"+pair+"'")
                continue
            #  Find the confusion matrix
            (confTable, allResponses) = ia_agreements_chance_corrected.reconstruct_contigency_table(counter, evalPhase, pair)
            #
            #  Accuracy without chance correction
            #
            (acc, correct, all) = ia_agreements_chance_corrected.find_Accuracy(confTable, allResponses)
            #
            #  Accuracy without chance correction (weighted)
            #
            (acc_w, correct_w, all_w) = ia_agreements_chance_corrected.find_weighted_Accuracy(confTable, allResponses, ia_agreements_chance_corrected.TLINK_distance)

            #
            #  Accuracy with chance correction
            #
            (kappa, observed, expected, tbl) = ia_agreements_chance_corrected.find_Cohens_Kappa(confTable, allResponses)
            #(kappa, observed, expected, tbl) = ia_agreements_chance_corrected.find_Scotts_PI(confTable, allResponses)
            #(alpha, coincidence) = ia_agreements_chance_corrected.find_Krippendorff_Alpha(confTable, allResponses, ia_agreements_chance_corrected.default_distance)
            #(alpha, coincidence) = ia_agreements_chance_corrected.find_Krippendorff_Alpha(confTable, allResponses, ia_agreements_chance_corrected.TLINK_distance)
            chance_corrected = kappa
            #chance_corrected = alpha
            #if ( tlinkLayer == "event_dct" ):
            #    print (pair, ia_agreements_chance_corrected.debugGetContingencyTableAsString(confTable) )

            isJudgeScore = True
            if (judge == None or (judge and judge not in pair)):
                isJudgeScore = False
                #
                #  ***  Record detailed annotator agreements
                #
                detailed = [ evalPhase, correct, all, acc, isJudgeScore, chance_corrected ]
                if (tlinkLayer not in allTLINKrelTypeDetails):
                    allTLINKrelTypeDetails[tlinkLayer] = dict()
                allTLINKrelTypeDetails[tlinkLayer][pair] = detailed
                #  ***  Record agreements only
                allTLINKaccs.append( acc )
                allTLINKaccs_weighted.append( acc_w )
                allTLINKccs.append( chance_corrected )
                #  ***  Record relation counts
                allTLINKcounts.append( all*2 )
                #  ***  Record number of vague relations
                valueCounts = ia_agreements_chance_corrected.collectValueCountsFromConfTables( [confTable] )
                if ("VAGUE" in valueCounts):
                    allTLINKvagueRelCount.append( valueCounts["VAGUE"] )
                else:
                    allTLINKvagueRelCount.append( 0 )
                #  ***  Record conf tables
                allTLINKconfTables.append( confTable )
                
                #  ***  Write table in R format, so R functions can be used to further check the agreement
                #if (writeRscriptForIAA):
                #    ia_agreements_chance_corrected.addResultToRscript(evalPhase, pair, str(chance_corrected), confTable, allResponses, filterKey)

    # ****  A small sanity check
    if (len(allTLINKFscores) != 12):
        raise Exception(" Unexpected number of F-scores: "+str(len(allTLINKFscores)))
    if (len(allTLINKconfTables) != 12):
        raise Exception(" Unexpected number of confusion matrixes: "+str(len(allTLINKconfTables)))
    if (len(allTLINKvagueRelCount) != 12):
        raise Exception(" Unexpected number of vague link counts: "+str(len(allTLINKvagueRelCount)))
    if (len(allTLINKccs) != 12):
        raise Exception(" Unexpected number of chance-corrected agreements: "+str(len(allTLINKccs)))
    if (len(allTLINKaccs) != 12):
        raise Exception(" Unexpected number of agreements: "+str(len(allTLINKaccs)))
    if (len(allTLINKaccs_weighted) != 12):
        raise Exception(" Unexpected number of weighted agreements: "+str(len(allTLINKaccs_weighted)))
    if (len(allTLINKcounts) != 12):
        raise Exception(" Unexpected number of TLINK counts: "+str(len(allTLINKcounts)))

    #
    #  Output the detailed table on TLINK agreements
    #
    print (("="*46))
    print ("   Detailed results for TLINKs ("+filterKey+")")
    print ("  (relType IAAs layer by layer, pair by pair)")
    print (("="*46))
    allTlinkLayers = ["event_timex", "event_dct", "main_events", "event_event"]
    for i in range( len(allTlinkLayers) ):
        tlinkLayer = allTlinkLayers[i]
        if (tlinkLayer not in allTLINKrelTypeDetails):
            raise Exception(" No annotations collected from the TLINK layer : "+tlinkLayer)
        print ( (" "*7)+"--- "+tlinkLayer+" ---" )
        #
        #  Results on each pair
        #
        for pair in sorted( allTLINKrelTypeDetails[tlinkLayer].keys() ):
            [ evalPhase, correct, all, acc, isJudgeScore, chance_corrected ] = allTLINKrelTypeDetails[tlinkLayer][pair]
            if (isinstance(acc, str) and acc == "N/A"):
                print( (" "*7)+pair+"  "+evalPhase+" "+"   Acc: "+acc+"    "+str(correct)+" / "+str(all)+"   CC: "+chance_corrected )
                continue
            acc_f = '{:.3}'.format( acc )
            out_string = (" "*7)+pair+"  "+evalPhase+" "+\
                         "   Acc: "+acc_f+"    "+str(correct)+" / "+str(all)
            out_string += "   CC: "+'{:.3}'.format( chance_corrected )
            print( out_string )
        #
        #  Aggregated results
        #
        startIndex = i*3
        endIndex   = i*3 + 2
        (allAccs, hasNAs1) = getSubListOfNumbers(allTLINKaccs, startIndex, endIndex )
        (allCCs, hasNAs2)  = getSubListOfNumbers(allTLINKccs, startIndex, endIndex )
        
        avg_acc = fsum(allAccs) / len(allAccs)
        avg_cc = fsum(allCCs) / len(allCCs)
        out_string = (" "*20)+"  "+evalPhase+" "
        out_string += "  Avg_acc: "+'{:.3}'.format( avg_acc )+hasNAs1
        out_string += "  Avg_CC: "+'{:.3}'.format( avg_cc )+hasNAs2
        print( out_string )
        print ()            

    #
    #  Output:   F1-scores on choosing entities for tlinks (detecting TLINKs)
    # 
    snippetStr = (" "*7)+"find-TLINK-F1scores |"
    for i in range( len(allTlinkLayers) ):
        tlinkLayer = allTlinkLayers[i]
        startIndex = i*3
        endIndex   = i*3 + 2
        (allFscores, hasNAs1) = getSubListOfNumbers( allTLINKFscores, startIndex, endIndex )
        avg_F  = fsum(allFscores) / len(allFscores)
        snippetStr += " "+'{:.3}'.format( avg_F )+hasNAs1+" "
    (allFscores, hasNAs1) = getSubListOfNumbers( allTLINKFscores, 0, len(allTLINKFscores) - 1 )
    avg_F  = fsum(allFscores) / len(allFscores)
    snippetStr += "| "+'{:.3}'.format( avg_F )+hasNAs1+" "
    print (snippetStr)

    #
    #  Output:   detailed counts of TLINKs
    # 
    numberOfAllUsedRelations = sum(allTLINKcounts)
    snippetStr = (" "*7)+"counts-for-TLINK-base | "
    for i in range( len(allTlinkLayers) ):
        tlinkLayer = allTlinkLayers[i]
        startIndex = i*3
        endIndex   = i*3 + 2
        (allCounts, hasNAs1) = getSubListOfNumbers( allTLINKcounts, startIndex, endIndex )
        snippetStr += str(sum(allCounts))+" "
    snippetStr += "| "+str( numberOfAllUsedRelations )
    print (snippetStr)
    print()

    #
    #  Output:   detailed counts of VAGUE relations
    # 
    print ( (" "*7)+'Details on distributions of vague relations: ' )
    allTlinkLayers = ["event_timex", "event_dct", "main_events", "event_event"]
    for i in range( len(allTlinkLayers) ):
        tlinkLayer = allTlinkLayers[i]
        print ( (" "*7)+"--- "+tlinkLayer+" ---" )
        evalPhase = 'tlink-'+tlinkLayer+'-vague-dist'
        startIndex = i*3
        endIndex   = i*3 + 2
        layerVAGUE = allTLINKvagueRelCount[startIndex : (endIndex+1)]
        layerAll   = allTLINKcounts[startIndex : (endIndex+1)]
        for p in range(len(allPairsSorted)):
            pair = allPairsSorted[ p ]
            if 'j' not in pair:
                #
                # 1st way for total: over all pairs and layers:
                #
                #totalTLINKRelations = numberOfAllUsedRelations
                #
                # 2nd way for total: over all layers of given pair
                #
                totalTLINKRelations = sum([ allTLINKcounts[j*3+p] for j in range( len(allTlinkLayers) ) ])
                percentage = layerVAGUE[p] * 100.0 / totalTLINKRelations
                out_string = (" "*7)+pair+"  "+evalPhase+" "+\
                              "   VAGUE: "+str(layerVAGUE[p])+\
                              "   "+'{:.3}'.format( percentage )+"% "
                print(out_string)
    print()
    
    focusOnLayer = "base"
    print (("="*46))
    print ("  Compact results for TLINKs ("+filterKey+")")
    print (("="*46))
    #  Agreement ja Chance-corrected agreement, layer by layer
    shortAccsStr  = (" "*7)+"short-accs-for-TLINK-"+focusOnLayer+"   "+str(numberOfAllUsedRelations)+" |"
    shortAccsWStr = (" "*7)+"short-accs-w-for-TLINK-"+focusOnLayer+" "+str(numberOfAllUsedRelations)+" |"
    shortCCsStr   = (" "*7)+"short-CCs-for-TLINK-"+focusOnLayer+"    "+str(numberOfAllUsedRelations)+" |"
    allTlinkLayers = ["event_timex", "event_dct", "main_events", "event_event"]
    for i in range( len(allTlinkLayers) ):
        tlinkLayer = allTlinkLayers[i]
        startIndex = i*3
        endIndex   = i*3 + 2
        (allAccs, hasNAs1)  = getSubListOfNumbers(allTLINKaccs, startIndex, endIndex )
        (allAccWs, hasNAs3) = getSubListOfNumbers(allTLINKaccs_weighted, startIndex, endIndex )
        (allCCs, hasNAs2)   = getSubListOfNumbers(allTLINKccs, startIndex, endIndex )
        avg_acc  = fsum(allAccs) / len(allAccs)
        avg_accw = fsum(allAccWs) / len(allAccWs)
        avg_cc   = fsum(allCCs) / len(allCCs)
        shortAccsStr += " "+'{:.3}'.format( avg_acc )+hasNAs1
        shortAccsWStr += " "+'{:.3}'.format( avg_accw )+hasNAs3
        shortCCsStr += " "+'{:.3}'.format( avg_cc )+hasNAs2
    (allAccs, hasNAs1)  = getSubListOfNumbers(allTLINKaccs, 0, len(allTLINKaccs)-1 )
    (allAccWs, hasNAs3) = getSubListOfNumbers(allTLINKaccs_weighted, 0, len(allTLINKaccs_weighted)-1 )
    (allCCs, hasNAs2)   = getSubListOfNumbers(allTLINKccs, 0, len(allTLINKccs)-1 )
    avg_acc  = fsum(allAccs)  / len(allAccs)
    avg_accw = fsum(allAccWs) / len(allAccWs)
    avg_cc   = fsum(allCCs)   / len(allCCs)
    shortAccsStr += " | "+'{:.3}'.format( avg_acc )+hasNAs1
    shortAccsWStr += " | "+'{:.3}'.format( avg_accw )+hasNAs3
    shortCCsStr += " | "+'{:.3}'.format( avg_cc )+hasNAs2
    print ( (" "*7)+'Observed agreements (accuracies): ' )
    print ( shortAccsStr )
    print ( shortAccsWStr )
    print ()
    
    print ( (" "*7)+'Chance-corrected agreements (kappas): ' )
    print ( shortCCsStr )
    #  Chance-corrected agreement, pair by pair
    ccResultsForPairs = dict()
    allTlinkLayers = ["event_timex", "event_dct", "main_events", "event_event"]
    for i in range( len(allTlinkLayers) ):
        tlinkLayer = allTlinkLayers[i]
        for pair in sorted( allTLINKrelTypeDetails[tlinkLayer].keys() ):
            [ evalPhase, correct, all, acc, isJudgeScore, chance_corrected ] = allTLINKrelTypeDetails[tlinkLayer][pair]
            if (pair not in ccResultsForPairs):
                ccResultsForPairs[pair] = []
            ccResultsForPairs[pair].append( chance_corrected )
    for pair in sorted( ccResultsForPairs.keys() ):
        print ( (" "*7)+"short-pair-CCs-for-TLINK-"+pair+"-"+focusOnLayer+" ",end="" )
        for k in ccResultsForPairs[pair]:
            if (not isinstance(acc, str)):
                print ( " "+'{:.3}'.format( k ), end="" )
            else:
                print ( " "+acc, end="" )
        (allCCs, hasNAs) = getSubListOfNumbers(ccResultsForPairs[pair], 0, len(ccResultsForPairs[pair])-1 )
        avg_K = fsum(allCCs)/len(allCCs)
        print (" | "+'{:.3}'.format( avg_K )+hasNAs, end="")
        print ()
    print ()
    
    #  Distributions of relType, layer by layer
    print ( (" "*7)+'Distributions of relTypes: ' )
    allTlinkLayers = ["event_timex", "event_dct", "main_events", "event_event"]
    for i in range( len(allTlinkLayers) ):
        tlinkLayer = allTlinkLayers[i]
        startIndex = i*3
        endIndex   = i*3 + 2
        allTables  = allTLINKconfTables[startIndex : (endIndex+1)]
        valueCounts = ia_agreements_chance_corrected.collectValueCountsFromConfTables( allTables )
        valStr = ia_agreements_chance_corrected.formatValCountsAsStr( valueCounts )
        print ( (" "*7)+"tlink-distr-"+tlinkLayer+"  "+valStr )
    print ()

    #  Proportions of VAGUE, layer by layer
    print ( (" "*7)+'Distributions of vague relations: ' )
    print ( (" "*7)+"tlink-vague-relations  ", end = "")
    totalVague = 0
    allTlinkLayers = ["event_timex", "event_dct", "main_events", "event_event"]
    for i in range( len(allTlinkLayers) ):
        tlinkLayer = allTlinkLayers[i]
        startIndex = i*3
        endIndex   = i*3 + 2
        allVAGUE  = allTLINKvagueRelCount[startIndex : (endIndex+1)]
        layerVagueCount = sum(allVAGUE)
        totalVague += layerVagueCount
        percentage = layerVagueCount * 100.0 / numberOfAllUsedRelations
        print (""+'{:.3}'.format( percentage )+"% ", end="")
    percentage = totalVague * 100.0 / numberOfAllUsedRelations
    print ("|  #"+str(totalVague)+"  "+'{:.3}'.format( percentage )+"% ")
    print ()
    
