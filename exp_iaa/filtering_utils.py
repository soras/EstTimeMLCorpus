# -*- coding: utf-8 -*- 
#
#    Utils for filtering TimeML (EVENT, TLINK) annotations based on linguistic 
#   annotations (morphological and syntactic annotations) or on other TimeML
#   annotations (EVENT, TIMEX annotations).
#
#    Developed and tested under Python's version: 3.4.1
#

import re

import sol_format_tools

# =========================================================================
#    Various useful utils
# =========================================================================

def gatherAllAnnotationsOfTheSentence( file, annotators, targetSentID, eventAnnotationsByLoc, tmxAnnotationsByLoc ):
    ''' Gathers all entity annotations of the sentence. '''
    annotations = []
    for annotator in annotators:
        for dataDict in [eventAnnotationsByLoc, tmxAnnotationsByLoc]:
            if annotator in dataDict:
                if file in dataDict[annotator]:
                    for (sentenceID, wordID) in dataDict[annotator][file]:
                        if int(sentenceID) == int(targetSentID):
                            for [eID, expr, ann] in dataDict[annotator][file][(sentenceID, wordID)]:
                                annotations.append( [ annotator, int(sentenceID), int(wordID), eID, expr, ann ] )
            else:
                raise Exception(' Missing data for annotator: ', annotator)
    return annotations


def isOlemaAsSinglePresPredicate( tense, vsLemmas, vcSynts ):
    '''Detects whether 'olema' is not part of a composite tense, but
       forms a single word present tense main verb. '''
    if (tense == "pres" and "ole" in vsLemmas):
        i = vsLemmas.index("ole")
        oleSyntFunct = vcSynts[i]
        oleCompanions = (i + 1 < len(vsLemmas))
        if (oleSyntFunct == "@FMV" and (not oleCompanions)):
            return True
    return False


def getSubordinatedTimexes(sentence, labels, clbFinLabels, allSentenceAnnotations, \
                           focusAnnotator, filterTimexesByType = None):
    ''' Finds all temporal expressions syntactically governed by the words specified in labels. '''
    timexAnnotations    = []
    timexAnnotationsIDs = []
    timexHeader = re.compile('^\s*TIMEX3?\s(DATE|TIME|SET|DURATION|UNK)')
    if (len(labels) > 0):
        sentLabels = [ int(sentence[j][4]) for j in range(len(sentence)) ]
        for i in range(len(sentence)):
            [ sentenceID, wordID, token, morphSynt, label, parentLabel ] = sentence[i]
            #(token2, morphSynt2, label2, parentLabel2, anno2) = sentence[i]
            if (parentLabel in labels):
                if (not sol_format_tools.in_different_clauses(sentence, labels[0], label, clbFinLabels = clbFinLabels)):
                    for [ annotator, sentenceID_int, wordID_int, eID, expr, ann ] in allSentenceAnnotations:
                        if (sentLabels[wordID_int] == int(label) and annotator == focusAnnotator and (ann.strip()).startswith('TIMEX')):
                            if timexHeader.match(ann):
                                timexAnnotations.append( ann )
                                timexAnnotationsIDs.append( eID )
                            else:
                                # Add the header, if missing:
                                headerFound = False
                                for annotation2 in allSentenceAnnotations:
                                    if annotation2[3] == eID and timexHeader.match(annotation2[5]):
                                        timexAnnotations.append( annotation2[5] )
                                        timexAnnotationsIDs.append( annotation2[3] )
                                        headerFound = True
                                        break
                                if not headerFound:
                                    raise Exception(' ! Header not found for the timex: ', [eID, expr, ann] )
    # Filter timexes according to the specified type (if required) ...
    if (filterTimexesByType != None):
        filteredTimexAnnotations = []
        for [ annotator, sentenceID_int, wordID_int, eID, expr, ann ] in allSentenceAnnotations:
            if (annotator != focusAnnotator):
                continue
            if (eID in timexAnnotationsIDs):
                if timexHeader.match(ann) and ("TIMEX "+filterTimexesByType) in ann:
                    filteredTimexAnnotations.append( ann )
        timexAnnotations = filteredTimexAnnotations
    return timexAnnotations


def incCount(hash, key):
    if (key not in hash):
        hash[key] = 1
    else:
        hash[key] = hash[key] + 1


# =========================================================================
#    Methods for filtring annotations
# =========================================================================

#   Filters the dicts of annotations (eventAnnotationsBy*, tmxAnnotationsBy*) and 
#  removes annotations that should be deleted according to the filtering method
#  (specified in filterKey);
#
#   Note: The decision to delete an annotation can be based either on considering 
#  underlaying linguistic annotations (morphological and syntactic annotations) or on 
#  considering TimeML annotations (EVENT, TIMEX annotations) provided by annotators.
#   ==> If an annotation should be deleted considering underlaying linguistic annotations,
#       the corresponding token is marked as deleted. However, the final deletion of the
#       entity depends on whether the marked token was header token or not; If a header 
#       token of a multiword event gets deleted, whole multiword event is deleted; otherwise 
#       only parts of it get deleted, but the entity itself remains;
#   ==> If an annotation should be deleted considering only TimeML annotations (e.g EVENT
#       class), the entity always gets deleted as a whole;
#
def filterAnnotations( file, annotators, judge, sentences, sentTrees, \
                       eventAnnotationsByLoc, tmxAnnotationsByLoc, \
                       eventAnnotationsByIDs, tmxAnnotationsByIDs, filterKey, deletedAnnotationsByLoc, deletedAnnoStatistics, debug = False ):
    # 1) Filter annotations using given filtering method (referred in filterKey);
    #    Record locations of "deleted tokens" along with IDs of EVENTs that should be deleted
    deletedAnnotationLocs = dict()
    for i in range( len(sentences) ):
        sentence = sentences[i]
        sentTree = sentTrees[i]
        allSentAnnotations = \
            gatherAllAnnotationsOfTheSentence( file, annotators, i, eventAnnotationsByLoc, tmxAnnotationsByLoc )
        for j in range(len(sentence)):
            entityAnnotations = [ a for a in allSentAnnotations if a[1]==i and a[2]==j ]
            for entityAnnotation in entityAnnotations:
                if filterEventsAccordingToKey(filterKey, entityAnnotation, \
                    sentence[j], sentence, sentTree, allSentAnnotations, judge):
                    annotator = entityAnnotation[0]
                    id = entityAnnotation[3]
                    tokenLoc = (file, i, j)
                    if (annotator not in deletedAnnotationLocs):
                        deletedAnnotationLocs[annotator] = dict()
                    if (tokenLoc not in deletedAnnotationLocs[annotator]):
                        deletedAnnotationLocs[annotator][tokenLoc] = []
                    deletedAnnotationLocs[annotator][tokenLoc].append( id )
                    #print( '(D)', entityAnnotation, sentence[j][3], )
                else:
                    #print( '+', entityAnnotation, sentence[j][3],  )
                    pass

    # 2)  Delete filtered annotations permanently
    if debug:
        print()
    for annotator in annotators:
        deletedAnnoLocalStats = dict()
        deletedAnnoLocalStats["_del_IDs"] = 0
        deletedAnnoLocalStats["_all_IDs"] = 0
        deletedAnnoLocalStats["_del_tokens"] = 0
        deletedAnnoLocalStats["_all_tokens"] = 0
        if annotator in eventAnnotationsByLoc:
            if file in eventAnnotationsByIDs[annotator]:
                # Count all annotated eventIDs before deletion
                for idKey in eventAnnotationsByIDs[annotator][file]:
                    if len(eventAnnotationsByIDs[annotator][file][idKey]) > 0:
                        incCount(deletedAnnoLocalStats, "_all_IDs")
            if file in eventAnnotationsByLoc[annotator]:
                # Count all annotated token annotations before deletion
                for locKey in eventAnnotationsByLoc[annotator][file]:
                    if len(eventAnnotationsByLoc[annotator][file][locKey]) > 0:
                        incCount(deletedAnnoLocalStats, "_all_tokens")
                # Delete all designated tokens
                if (annotator in deletedAnnotationLocs):
                    for tokenLoc in deletedAnnotationLocs[annotator]:
                        deleteEventAnnotation(annotator, file, tokenLoc[1], \
                                              tokenLoc[2], eventAnnotationsByLoc, \
                                              eventAnnotationsByIDs, deletedAnnoLocalStats)
        else:
            raise Exception(' No annotations for annotator ',annotator)
        if debug:
            print( "   From "+annotator+" deleted "+ str(deletedAnnoLocalStats["_del_IDs"])+" annotations." )
        #  Record (filtering debug) statistics        
        if (annotator not in deletedAnnoStatistics):
            deletedAnnoStatistics[annotator] = dict()
            deletedAnnoStatistics[annotator]["_del_IDs"] = 0
            deletedAnnoStatistics[annotator]["_all_IDs"] = 0
            deletedAnnoStatistics[annotator]["_del_tokens"] = 0
            deletedAnnoStatistics[annotator]["_all_tokens"] = 0
        deletedAnnoStatistics[annotator]["_del_IDs"] += deletedAnnoLocalStats["_del_IDs"]
        deletedAnnoStatistics[annotator]["_all_IDs"] += deletedAnnoLocalStats["_all_IDs"]
        deletedAnnoStatistics[annotator]["_del_tokens"] += deletedAnnoLocalStats["_del_tokens"]
        deletedAnnoStatistics[annotator]["_all_tokens"] += deletedAnnoLocalStats["_all_tokens"]
    return


def filterEventsAccordingToKey(filterKey, annotation, tokenStruct, sentence, sentTree, \
                               allSentAnnotations, judge):
    ''' Analyses the content and the context of the given event annotation, and 
        decides, whether given event annotation should be deleted according to the 
        given filtering method ( specified in filterKey ). 
        Returns True, if deletion should be applied. '''
    [ sentenceID, wordID, token, morphSynt, label, parentLabel ] = tokenStruct
    [ annotator, sentenceID_2, wordID_2, eID, expr, ann ] = annotation
    if (ann.strip()).startswith('EVENT'):
        if (filterKey[0] == "0"):
            #
            # 0) Ära rakenda ühtegi filtrit
            #
            return False
        elif (filterKey[0] == "1"):
            #
            # 1) Sündmuste liigitamine POS-tag'i järgi ...
            #
            pos = sol_format_tools.getPOStag(morphSynt)
            #  a. Ainult verbid (prototüüpne sündmus);
            if (filterKey[1] == "a"):
                return (not (pos in ["V"]))
            #  b. Verbid + nimisõnad;
            elif (filterKey[1] == "b"):
                return (not (pos in ["V", "S"]))
            #  c. Verbid + omadussõnad;
            elif (filterKey[1] == "c"):
                return (not (pos in ["V", "A"]))
            #  d. Verbid + nimisõnad + omadussõnad;
            elif (filterKey[1] == "d"):
                return (not (pos in ["V", "A", "S"]))
            #  e. Verbid + nimisõnad + omadussõnad + ülejäänud;
            elif (filterKey[1] == "e"):
                return False
            else:
                raise Exception(" Unexpected experiment ID: "+filterKey)
        elif (filterKey[0] == "2" and filterKey[1] != "*"):
            #
            #   2) Sündmuste liigitamine predikaati kuulumise ja mittekuulumise järgi:
            #
            delete = True
            pos = sol_format_tools.getPOStag(morphSynt)
            (verbChains, grouped) = sol_format_tools.getClPredicateStructure(sentence, label)
            if (not grouped):
                verbChains = [verbChains]
            isPredicateOrItsChild = False
            for verbChain in verbChains:
                #vcLabels     = [ t[2] for t in verbChain ]
                #vcMorphSynts = [ t[1] for t in verbChain ]
                vcLabels     = [ t[4] for t in verbChain ]
                vcMorphSynts = [ t[3] for t in verbChain ]
                vcSynts = [ sol_format_tools.getSyntacticFunction(t) for t in vcMorphSynts ]
                vsVerbTypes = [ sol_format_tools.getVerbType(t) for t in vcMorphSynts ]
                vsLemmas    = [ sol_format_tools.getLemma(t) for t in vcMorphSynts ]
                if (label in vcLabels or parentLabel in vcLabels):
                    isPredicateOrItsChild = True
                #
                #  a. kuulub ainult predikaati;
                #
                if (filterKey[1] == "a"):
                    if (label in vcLabels):
                        delete = False
                #
                #  b. a + on predikaati kuuluva sõna otsene alam ja verb;
                #
                elif (filterKey[1] == "b"):
                    if (label in vcLabels or (parentLabel in vcLabels and pos and pos == "V")):
                        delete = False
                #
                #  c. a + on predikaati kuuluva sõna otsene alam ja mitteverb;
                #
                elif (filterKey[1] == "c"):
                    if (label in vcLabels or (parentLabel in vcLabels and (not pos or pos != "V"))):
                        delete = False
                #
                #  d. a + pole predikaati kuuluva sõna otsene alam
                #
                elif (filterKey[1] == "d"):
                    if (label in vcLabels):
                        delete = False
                #
                #  e. kõik ylejäänud
                #
                elif (filterKey[1] == "e"):
                    delete = False
                else:
                    raise Exception(" Unexpected experiment ID: "+filterKey)
            #
            #  d. a + pole predikaati kuuluva sõna otsene alam
            #
            if (filterKey[1] == "d" and not isPredicateOrItsChild):
                delete = False
            return delete
        elif (filterKey[0] == "2" and filterKey[1] == "*"):
            #
            #   2*) Predikaati kuulumise ja mittekuulumise järgi (süntaksimärgendite järgi):
            #
            delete = True
            pos = sol_format_tools.getPOStag(morphSynt)
            (verbChains, grouped) = sol_format_tools.getClPredicateStructure(sentence, label)
            if (not grouped):
                verbChains = [verbChains]
            for verbChain in verbChains:
                #vcLabels     = [ t[2] for t in verbChain ]
                #vcMorphSynts = [ t[1] for t in verbChain ]
                vcLabels     = [ t[4] for t in verbChain ]
                vcMorphSynts = [ t[3] for t in verbChain ]
                vcSynts = [ sol_format_tools.getSyntacticFunction(t) for t in vcMorphSynts ]
                vsVerbTypes = [ sol_format_tools.getVerbType(t) for t in vcMorphSynts ]
                vsLemmas    = [ sol_format_tools.getLemma(t) for t in vcMorphSynts ]
                #
                #  a. kuulub ainult predikaati;
                #
                if (filterKey[2] == "a"):
                    if (label in vcLabels):
                        delete = False
                #
                #  b. a + on predikaati kuuluva sõna otsene alam: OBJ ja Verb;
                #
                elif (filterKey[2] == "b"):
                    if (label in vcLabels):
                        delete = False
                    elif (parentLabel in vcLabels):
                        syntFunc = sol_format_tools.getSyntacticFunction(morphSynt)
                        if (syntFunc and syntFunc == "@OBJ" and pos and pos == "V"):
                            delete = False
                #
                #  c. a + on predikaati kuuluva sõna otsene alam: OBJ ja mitteVerb;
                #
                elif (filterKey[2] == "c"):
                    if (label in vcLabels):
                        delete = False
                    elif (parentLabel in vcLabels):
                        syntFunc = sol_format_tools.getSyntacticFunction(morphSynt)
                        if (syntFunc and syntFunc == "@OBJ" and pos and pos != "V"):
                            delete = False
                #
                #  d. a + on predikaati kuuluva sõna otsene alam: SUBJ ja Verb;
                #
                elif (filterKey[2] == "d"):
                    if (label in vcLabels):
                        delete = False
                    elif (parentLabel in vcLabels):
                        syntFunc = sol_format_tools.getSyntacticFunction(morphSynt)
                        if (syntFunc and syntFunc == "@SUBJ" and pos and pos == "V"):
                            delete = False
                #
                #  e. a + on predikaati kuuluva sõna otsene alam: SUBJ ja mitteVerb;
                #
                elif (filterKey[2] == "e"):
                    if (label in vcLabels):
                        delete = False
                    elif (parentLabel in vcLabels):
                        syntFunc = sol_format_tools.getSyntacticFunction(morphSynt)
                        if (syntFunc and syntFunc == "@SUBJ" and pos and pos != "V"):
                            delete = False
                #
                #  f. a + on predikaati kuuluva sõna otsene alam: ADVL ja Verb;
                #
                elif (filterKey[2] == "f"):
                    if (label in vcLabels):
                        delete = False
                    elif (parentLabel in vcLabels):
                        syntFunc = sol_format_tools.getSyntacticFunction(morphSynt)
                        if (syntFunc and syntFunc == "@ADVL" and pos and pos == "V"):
                            delete = False
                #
                #  g. a + on predikaati kuuluva sõna otsene alam: ADVL ja mitteVerb;
                #
                elif (filterKey[2] == "g"):
                    if (label in vcLabels):
                        delete = False
                    elif (parentLabel in vcLabels):
                        syntFunc = sol_format_tools.getSyntacticFunction(morphSynt)
                        if (syntFunc and syntFunc == "@ADVL" and pos and pos != "V"):
                            delete = False
                else:
                    raise Exception(" Unexpected experiment ID: "+filterKey)
            return delete
        elif (filterKey[0] == "3"):
            #
            #   3) Ainult predikaadi liikmed grammatiliste aegade järgi:
            # 
            delete = True
            pos = sol_format_tools.getPOStag(morphSynt)
            (verbChains, grouped) = sol_format_tools.getClPredicateStructure(sentence, label)
            tenses = sol_format_tools.getPredicateTense(verbChains, grouped)
            if (not grouped):
                verbChains = [verbChains]
            for vc in range(len(verbChains)):
                verbChain = verbChains[vc]
                tense     = tenses[vc]
                vcLabels     = [ t[4] for t in verbChain ]
                vcMorphSynts = [ t[3] for t in verbChain ]
                vcSynts = [ sol_format_tools.getSyntacticFunction(t) for t in vcMorphSynts ]
                vsVerbTypes = [ sol_format_tools.getVerbType(t) for t in vcMorphSynts ]
                vsLemmas    = [ sol_format_tools.getLemma(t) for t in vcMorphSynts ]
                modality = False
                negation = False
                if ("@NEG" in vcSynts):
                    negation = True
                if ("mod" in vsVerbTypes):
                    modality = True
                if (label in vcLabels):
                    # a. ainult lihtminevik
                    if (filterKey[1] == "a"):
                        if (tense in ["impf"]):
                            delete = False
                    # b. lihtminevik + enneminevik
                    elif (filterKey[1] == "b"):
                        if (tense in ["impf", "pqpf"]):
                            delete = False
                    # c. lihtminevik + taisminevik
                    elif (filterKey[1] == "c"):
                        if (tense in ["impf", "pf"]):
                            delete = False
                    # d. lihtminevik + taisminevik + enneminevik
                    elif (filterKey[1] == "d"):
                        if (tense in ["impf", "pf", "pqpf"]):
                            delete = False
                    # e. lihtminevik + taisminevik + enneminevik + olevik
                    elif (filterKey[1] == "e"):
                        if (tense in ["impf", "pf", "pqpf", "pres"]):
                            delete = False
                    # f. lihtminevik + olevik
                    elif (filterKey[1] == "f"):
                        if (tense in ["impf", "pres"]):
                            delete = False
                    # g. k6ik
                    elif (filterKey[1] == "g"):
                        delete = False
                    # h. d + olevik (v.a. "olema" verb üksikuna)
                    elif (filterKey[1] == "h"):
                        if (tense in ["impf", "pf", "pqpf", "pres"]):
                            delete = False
                            if (isOlemaAsSinglePresPredicate( tense, vsLemmas, vcSynts )):
                                delete = True
                    # i. d + olevik (ainult indikatiiv)
                    elif (filterKey[1] == "i"):
                        if (tense in ["impf", "pf", "pqpf", "pres"]):
                            delete = False
                            if (tense == "pres"):
                                delete = True
                                vsVerbMoods = [ sol_format_tools.getVerbMood(t) for t in vcMorphSynts ]
                                if ("indic" in vsVerbMoods):
                                    delete = False
                    # j. d + olevik (ainult indikatiiv, v.a. "olema" verb yksikuna)
                    elif (filterKey[1] == "j"):
                        if (tense in ["impf", "pf", "pqpf", "pres"]):
                            delete = False
                            if (tense == "pres"):
                                delete = True
                                vsVerbMoods = [ sol_format_tools.getVerbMood(t) for t in vcMorphSynts ]
                                if ("indic" in vsVerbMoods):
                                    delete = False
                                if (isOlemaAsSinglePresPredicate( tense, vsLemmas, vcSynts )):
                                    delete = True
                    # k. d + olevik (ainult kindel k6neviis + v.a. "olema" verb üksikuna + ilma eituse/modaalsuseta)
                    elif (filterKey[1] == "k"):
                        if (tense in ["impf", "pf", "pqpf", "pres"]):
                            delete = False
                            if (tense == "pres"):
                                delete = True
                                vsVerbMoods = [ sol_format_tools.getVerbMood(t) for t in vcMorphSynts ]
                                if ("indic" in vsVerbMoods):
                                    delete = False
                            if (isOlemaAsSinglePresPredicate( tense, vsLemmas, vcSynts )):
                                delete = True
                            if (negation or modality):
                                delete = True
                    # l. ainult olevik
                    elif (filterKey[1] == "l"):
                        if (tense in ["pres"]):
                            delete = False
                    # m. ainult enneminevik
                    elif (filterKey[1] == "m"):
                        if (tense in ["pqpf"]):
                            delete = False
                    # n. ainult täisminevik
                    elif (filterKey[1] == "n"):
                        if (tense in ["pf"]):
                            delete = False
                    else:
                        raise Exception(" Unexpected experiment ID: "+filterKey)
            return delete
        elif (filterKey[0] == "4" and filterKey[1] != "*"):
            #
            #   4) Ainult predikaadi liikmed ajaväljendite olemasolu järgi
            #
            delete = True
            pos = sol_format_tools.getPOStag(morphSynt)
            (verbChains, grouped) = sol_format_tools.getClPredicateStructure(sentence, label)
            tenses = sol_format_tools.getPredicateTense(verbChains, grouped)
            if (not grouped):
                verbChains = [verbChains]
            clbFinLabels = sol_format_tools.get_CLB_and_FinVerb_labels( sentence )
            timexType = None
            #timexType = "DATE"
            existPredGovernedTimexes = False
            for vc in range(len(verbChains)):
                verbChain = verbChains[vc]
                tense     = tenses[vc]
                #vcLabels     = [ t[2] for t in verbChain ]
                #vcMorphSynts = [ t[1] for t in verbChain ]
                vcLabels     = [ t[4] for t in verbChain ]
                vcMorphSynts = [ t[3] for t in verbChain ]
                vcSynts = [ sol_format_tools.getSyntacticFunction(t) for t in vcMorphSynts ]
                vcVerbTypes = [ sol_format_tools.getVerbType(t) for t in vcMorphSynts ]
                vcLemmas    = [ sol_format_tools.getLemma(t) for t in vcMorphSynts ]
                # Teeme kindlaks, kas m6ni ajav2ljend allub predikaadile
                #predTimexes = getSubordinatedTimexes(sentence, vcLabels, clbFinLabels, allSentAnnotations, judge, filterTimexesByType = timexType)
                predTimexes = getSubordinatedTimexes(sentence, vcLabels, clbFinLabels, allSentAnnotations, judge)
                if (len(predTimexes) > 0):
                    existPredGovernedTimexes = True
                #
                #  a. predikaati kuuluvad sündmused, millele alluvad ajaväljendid;
                #
                if (filterKey[1] == "a"):
                    if ( label in vcLabels and len(predTimexes) > 0 ):
                        delete = False
                #
                #  b. predikaati kuuluvad sündmused, millele EI allu ykski ajaväljend;
                #
                elif (filterKey[1] == "b"):
                    if ( label in vcLabels and len(predTimexes) == 0 ):
                        delete = False
                #
                #  c. kõik predikaati kuuluvad sündmused;
                #
                elif (filterKey[1] == "c"):
                    if ( label in vcLabels ):
                        delete = False
                #
                #  d. a + muud mittepredikaadi sündmused, millele alluvad ajaväljendid;
                #
                elif (filterKey[1] == "d"):
                    if ( label in vcLabels and len(predTimexes) > 0 ):
                        delete = False
                    else:
                        timexes = getSubordinatedTimexes(sentence, [ label ], clbFinLabels, allSentAnnotations, judge, filterTimexesByType = timexType)
                        if (len(timexes) > 0):
                            delete = False
                #
                #  e. samas lauses esineb predikaat, millele allub ajav2ljend;
                #
                elif (filterKey[1] == "e"):
                    True
                #
                #  f. samas lauses EI esine yhtegi predikaati, millele allub ajav2ljend;
                #
                elif (filterKey[1] == "f"):
                    True
                else:
                    raise Exception(" Unexpected experiment ID: "+filterKey)
            #
            #  e. samas lauses esineb predikaat, millele allub ajav2ljend;
            #
            if (filterKey[1] == "e"):
                if (existPredGovernedTimexes):
                    delete = False
            #
            #  f. samas lauses EI esine yhtegi predikaati, millele allub ajav2ljend;
            #
            if (filterKey[1] == "f"):
                if (not existPredGovernedTimexes):
                    delete = False
            return delete
        elif (filterKey[0] == "4" and filterKey[1] == "*"):
            #
            #   4*) Ainult predikaadi liikmed ajaväljendite olemasolu järgi + grammatilised ajad
            #
            delete = True
            pos = sol_format_tools.getPOStag(morphSynt)
            (verbChains, grouped) = sol_format_tools.getClPredicateStructure(sentence, label)
            tenses = sol_format_tools.getPredicateTense(verbChains, grouped)
            if (not grouped):
                verbChains = [verbChains]
            clbFinLabels = sol_format_tools.get_CLB_and_FinVerb_labels( sentence )
            for vc in range(len(verbChains)):
                verbChain = verbChains[vc]
                tense     = tenses[vc]
                #vcLabels     = [ t[2] for t in verbChain ]
                #vcMorphSynts = [ t[1] for t in verbChain ]
                vcLabels     = [ t[4] for t in verbChain ]
                vcMorphSynts = [ t[3] for t in verbChain ]
                vcSynts = [ sol_format_tools.getSyntacticFunction(t) for t in vcMorphSynts ]
                vcVerbTypes = [ sol_format_tools.getVerbType(t) for t in vcMorphSynts ]
                vcLemmas    = [ sol_format_tools.getLemma(t) for t in vcMorphSynts ]
                # Teeme kindlaks, kas m6ni ajav2ljend allub predikaadile
                predTimexes = getSubordinatedTimexes(sentence, vcLabels, clbFinLabels, allSentAnnotations, judge)
                #
                #  *a. 4a + lihtminevik; (kõige selgemini eristuv)
                #
                if (filterKey[2] == "a"):    
                    if ( label in vcLabels ):
                        if (len(predTimexes) > 0 or tense in ["impf"] ):
                            delete = False
                #
                #  *b. *a + enneminevik;
                #
                elif (filterKey[2] == "b"):
                    if ( label in vcLabels ):
                        if (len(predTimexes) > 0 or tense in ["impf", "pqpf"] ):
                            delete = False
                #
                #  *c. *a + täisminevik;
                # 
                elif (filterKey[2] == "c"):
                    if ( label in vcLabels ):
                        if (len(predTimexes) > 0 or tense in ["impf", "pf"] ):
                            delete = False
                #
                #  *d. *a + enneminevik ja täisminevik; (kui süntaks võimaldab tuvastada)
                #
                elif (filterKey[2] == "d"):
                    if ( label in vcLabels ):
                        if (len(predTimexes) > 0 or tense in ["impf", "pf", "pqpf"] ):
                            delete = False
                #
                # *e. *a + olevik (probleemne, läheb sassi üldise väitega)
                #
                elif (filterKey[2] == "e"):
                    if ( label in vcLabels ):
                        if (len(predTimexes) > 0 or tense in ["impf", "pf", "pqpf", "pres"] ):
                            delete = False
                else:
                    raise Exception(" Unexpected experiment ID: "+filterKey)
            return delete
        elif (filterKey[0] == "5"):
            #
            #   5) Ainult predikaadi liikmed eituse/modaalsuse mõjude järgi:
            #
            delete = True
            pos = sol_format_tools.getPOStag(morphSynt)
            (verbChains, grouped) = sol_format_tools.getClPredicateStructure(sentence, label)
            if (not grouped):
                verbChains = [verbChains]
            for verbChain in verbChains:
                vcLabels     = [ t[4] for t in verbChain ]
                vcMorphSynts = [ t[3] for t in verbChain ]
                #vcLabels     = [ t[2] for t in verbChain ]
                #vcMorphSynts = [ t[1] for t in verbChain ]
                vcSynts = [ sol_format_tools.getSyntacticFunction(t) for t in vcMorphSynts ]
                vsVerbTypes = [ sol_format_tools.getVerbType(t) for t in vcMorphSynts ]
                vsLemmas    = [ sol_format_tools.getLemma(t) for t in vcMorphSynts ]
                modality = False
                negation = False
                if ("@NEG" in vcSynts):
                    negation = True
                if ("mod" in vsVerbTypes):
                    modality = True
                #
                #        a. ilma eituse ja modaalsuseta predikaadid;
                #
                if (filterKey[1] == "a"):
                    if (label in vcLabels and not modality and not negation):
                        delete = False
                #
                #        b. a + modaalsusega predikaadid;
                #
                elif (filterKey[1] == "b"):
                    if (label in vcLabels and not negation):
                        delete = False
                #
                #        c. a + eitusega predikaadid;
                #
                elif (filterKey[1] == "c"):
                    if (label in vcLabels and not modality):
                        delete = False
                #
                #        d. a + eituse ja modaalsusega predikaadid;
                #
                elif (filterKey[1] == "d"):
                    if (label in vcLabels):
                        delete = False
                else:
                    raise Exception(" Unexpected experiment ID: "+filterKey)
            return delete
        elif (filterKey[0] == "6" and filterKey[1] == "*"):
            delete = False
            eventHeader = re.compile('^EVENT\s+([A-Z_]+)')
            #
            #   6) Syndmusm2rgendus TimeML class'i m6jude järgi: vaatame l6pliku
            #      hindaja m2rgendusi ning tagastame ainult antud TimeML class'i
            #      liikme argumendistruktuuri kuuluva syndmuse
            #
            if eventHeader.match( ann ):
                delete = True
                isInArgStruct = False
                judgeAnnotations = [a for a in allSentAnnotations if a[0] == judge]
                eventsWithArgs = \
                    dependency_trees.getEventArgStructInSentence(sentence, sentTree, judgeAnnotations, useAllClasses = True)
                for eventWithArgs in eventsWithArgs:
                    treeSeq  = [ eventWithArgs[k] for k in range(1, len(eventWithArgs)) ]
                    labelSeq = [ tree.label for tree in treeSeq ]
                    widSeq   = [ tree.wordID for tree in treeSeq ]
                    #annotations = for annotation in sentAnnotations:
                    if (label in labelSeq):
                        isInArgStruct = True
                        # Collect event classes associated with nodes
                        classSeq = []
                        for wid in widSeq:
                            eClass = "---"
                            for a in judgeAnnotations:
                                if int(wid) == int(a[2]) and eventHeader.match( a[5] ):
                                    eClass = ((a[5]).split())[1]
                                    break
                            classSeq.append( eClass )
                        controllingClass = classSeq[0]
                        #  a) tegemist on REPORTING syndmuse v6i m6ne selle vahetu alluvaga
                        if (filterKey[2] == "a"):
                            if (controllingClass == "REPORTING"):
                                delete = False
                        #  b) tegemist on I_ACTION syndmuse v6i m6ne selle vahetu alluvaga
                        elif (filterKey[2] == "b"):
                            if (controllingClass == "I_ACTION"):
                                delete = False
                        #  c) tegemist on I_STATE syndmuse v6i m6ne selle vahetu alluvaga
                        elif (filterKey[2] == "c"):
                            if (controllingClass == "I_STATE"):
                                delete = False
                        #  d) tegemist on ASPECTUAL syndmuse v6i m6ne selle vahetu alluvaga
                        elif (filterKey[2] == "d"):
                            if (controllingClass == "ASPECTUAL"):
                                delete = False
                        #  e) tegemist on PERCEPTION syndmuse v6i m6ne selle vahetu alluvaga
                        elif (filterKey[2] == "e"):
                            if (controllingClass == "PERCEPTION"):
                                delete = False
                        #  f) tegemist on MODAL'i v6i m6ne selle vahetu alluvaga
                        elif (filterKey[2] == "f"):
                            if (controllingClass == "MODAL"):
                                delete = False
                        #  g) tegemist on OCCURRENCE'i v6i m6ne selle vahetu alluvaga
                        elif (filterKey[2] == "g"):
                            if (controllingClass == "OCCURRENCE"):
                                delete = False
                        #  h) tegemist on STATE'i v6i m6ne selle vahetu alluvaga
                        elif (filterKey[2] == "h"):
                            if (controllingClass == "STATE"):
                                delete = False
                            True
                        #  i) syndmus ei kuulu yhessegi TimeML argumentstruktuuri
                        elif (filterKey[2] == "i"):
                            True
                        else:
                            raise Exception(" Unexpected experiment ID: "+filterKey)
                    #if not delete:
                    #    print(label, labelSeq, classSeq)
                #  i) syndmus ei kuulu yhessegi TimeML argumentstruktuuri
                if (filterKey[2] == "i"):
                    delete = isInArgStruct
            return delete
        else:
            raise Exception(" Unexpected experiment ID: "+filterKey)
    else:
        return False


# =========================================================================
#    Methods for deleting EVENT, TLINK annotations
# =========================================================================

#
#   Deletes all event annotations from given location;
#  *) If a multiword event with header information (event type etc.) gets deleted,
#     the method also locates other parts of the event, and eliminates the event
#     completely from eventAnnotationsByLoc and from eventAnnotationsByIDs;
#  *) If a multiword event without any header information (event type etc.) gets 
#     deleted, its other parts will remain as they are;
#
def deleteEventAnnotation(annotator, file, sentID, wordID, eventAnnotationsByLoc, \
                                                           eventAnnotationsByIDs, \
                                                           deletedAnnoLocalStats ):
    if annotator not in eventAnnotationsByLoc or file not in eventAnnotationsByLoc[annotator]:
        return
    if annotator not in eventAnnotationsByIDs or file not in eventAnnotationsByIDs[annotator]:
        return
    headerTag = re.compile('^(EVENT|TIMEX)\s+([A-Z_]+)\s*')
    sentID = str(sentID)
    wordID = str(wordID)
    if (sentID, wordID) in eventAnnotationsByLoc[annotator][file]:
        idsToFullyDelete     = []
        idsToPartiallyDelete = []
        for ann in eventAnnotationsByLoc[annotator][file][(sentID, wordID)]:
            [entityID, expression, annotation] = ann
            if headerTag.match(annotation):
                # If the header event gets deleted, it must be deleted at 
                # full span. Record the ID for this
                idsToFullyDelete.append( entityID )
                deletedAnnoLocalStats["_del_IDs"] += 1
            else:
                idsToPartiallyDelete.append( entityID )
            deletedAnnoLocalStats["_del_tokens"] += 1
        # Delete all annotations from given location
        del eventAnnotationsByLoc[annotator][file][(sentID, wordID)]
        # Delete all annotations covered by deleted header events
        if idsToFullyDelete:
            locsToDelete = []
            for eid in idsToFullyDelete:
                # Find additional locations of the event span
                for ann in eventAnnotationsByIDs[annotator][file][eid]:
                    [sID, wID, expression, annotation] = ann
                    if sentID != sID or wordID != wID:
                        locsToDelete.append( [sID, wID, eid])
                        deletedAnnoLocalStats["_del_tokens"] += 1
                del eventAnnotationsByIDs[annotator][file][eid]
            # Delete events from all additional locations
            if locsToDelete:
                for [sID, wID, eid] in locsToDelete:
                    if (sID, wID) in eventAnnotationsByLoc[annotator][file]:
                        locations = len(eventAnnotationsByLoc[annotator][file][(sID, wID)])
                        indexesToDelete = []
                        for i in range(locations):
                            ann = eventAnnotationsByLoc[annotator][file][(sID, wID)][i]
                            [entityID, expression, annotation] = ann
                            if entityID == eid:
                                indexesToDelete.append(i)
                        for r in sorted(indexesToDelete, reverse=True):
                            del eventAnnotationsByLoc[annotator][file][(sID, wID)][r]
                        if len(eventAnnotationsByLoc[annotator][file][(sID, wID)]) == 0:
                            del eventAnnotationsByLoc[annotator][file][(sID, wID)]
        # Delete locations (sentID, wordID) from eventsByIDs;
        if idsToPartiallyDelete:
            for eid in idsToPartiallyDelete:
                anns = eventAnnotationsByIDs[annotator][file][eid]
                j = -1
                for i in range(len(anns)):
                    if anns[i][0] == sentID and anns[i][1] == wordID:
                        j = i
                        break
                if j > -1:
                    del eventAnnotationsByIDs[annotator][file][eid][j]

#
#   Deletes all relations that are associated with the event (given by eventID)
#   from the collection of tlinks (the collection is indexed by event ids):
#   *) Deletes the entry indexed by the eventID from the collection;
#   *) Looks through all the other entries and if they contain relation
#      annotations involving the event, also deletes these annotations;
#
def deleteAllRelationsAssociatedWithEvent( file, annotator, eventID, tlinks ):
    if annotator not in tlinks or file not in tlinks[annotator]:
        return
    if eventID in tlinks[annotator][file]:
        #debugRelsDeleted += len(tlinks[annotator][file][eventID])
        del tlinks[annotator][file][eventID]
    for eID in tlinks[annotator][file]:
        toDelete = []
        for i in range(len(tlinks[annotator][file][eID])):
            [entityA, relation, entityB, comment] = \
                tlinks[annotator][file][eID][i]
            if entityA == eventID or entityB == eventID:
                toDelete.append( tlinks[annotator][file][eID][i] )
        if toDelete:
            #debugRelsDeleted += len(toDelete)
            for annotation in toDelete:
                tlinks[annotator][file][eID].remove(annotation)

#
#    Filters all collections of relations, and deletes the relations associated
#   with events not present in eventAnnotationsByIds (events annotated by the judge);
#
def filterOutDeletedRelations(eventTimexLinks, eventDCTLinks, mainEventLinks, \
                              subEventLinks, eventAnnotationsByIds, judge, debug=True):
    timexIndex = re.compile('^t[0-9]+$')
    eventsRemovedTotal = 0
    for file in sorted( eventAnnotationsByIds[judge] ):
        debugRelsDeleted = 0
        existingEvents = eventAnnotationsByIds[judge][file]
        for annotator in ['a', 'b', 'c', 'j']:
            # 1) Gather all eventIDs that refer to events to be deleted from given file
            toDelete = {}
            if annotator in eventTimexLinks and file in eventTimexLinks[annotator]:
                for index in eventTimexLinks[annotator][file]:
                    if index not in existingEvents and not timexIndex.match(index):
                        toDelete[ index ] = 1
            if annotator in eventDCTLinks and file in eventDCTLinks[annotator]:
                for index in eventDCTLinks[annotator][file]:
                    if index not in existingEvents and not timexIndex.match(index):
                        toDelete[ index ] = 1
            if annotator in mainEventLinks and file in mainEventLinks[annotator]:
                for index in mainEventLinks[annotator][file]:
                    if index not in existingEvents and not timexIndex.match(index):
                        toDelete[ index ] = 1
            if annotator in subEventLinks and file in subEventLinks[annotator]:
                for index in subEventLinks[annotator][file]:
                    if index not in existingEvents and not timexIndex.match(index):
                        toDelete[ index ] = 1
            eventsRemovedTotal += len(toDelete.keys())
            # 2) Perform the deletion
            for eventID in toDelete.keys():
                deleteAllRelationsAssociatedWithEvent(file, annotator, eventID, eventTimexLinks)
                deleteAllRelationsAssociatedWithEvent(file, annotator, eventID, eventDCTLinks)
                deleteAllRelationsAssociatedWithEvent(file, annotator, eventID, mainEventLinks)
                deleteAllRelationsAssociatedWithEvent(file, annotator, eventID, subEventLinks)

