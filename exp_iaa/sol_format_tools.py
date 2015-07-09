# -*- coding: utf-8 -*- 
#
#    Various utils for processing sol-format linquistic data;
#
#    Developed and tested under Python's version: 3.4.1
#

import re

# =========================================================================
#    Extracting initial linguistic features from *.SOL corpus:
#       words, morphology, syntax
# =========================================================================

def getLemma(morphoSyntactic):
    lemmaMatching = re.match( "^\s*\"([^\"]+)\"\s+L.*", morphoSyntactic )
    if lemmaMatching:
       return lemmaMatching.group(1)
    else:
       return None

def getPOStag(morphoSyntactic):
    wordPosMatching = re.match( "^\s*\"([^\"]+)\"\s+L\S+\s+([A-Z]+).*", morphoSyntactic )
    if wordPosMatching:
       return wordPosMatching.group(2)
    else:
       punctPosMatching = re.match( "^\s*\"(.)\"\s+([A-Z])\s+.*", morphoSyntactic )
       if punctPosMatching:
            return punctPosMatching.group(2)
       else:
            raise Exception(' Could not find pos tag from: '+str(morphoSyntactic))

#  Finds the type of the verb (one of the following: main, mod, aux, inf, sup, ger, partic)
def getVerbType(morphoSyntactic):
    vtMatch = re.match( ".*\s+(mod|aux|inf|sup|ger|partic)\s+", morphoSyntactic )
    if (vtMatch):
        return vtMatch.group(1)
    else:
        if (morphoSyntactic.count(" main ") > 0):
            return "main"
        else:
            return None

#  Finds morphological tense of the verb (one of the following: partic pres, partic past, cond past, pres, impf)
def getVerbTime(morphoSyntactic):
    particTimeMatch = re.match( ".*\s+(partic\spres|partic\spast|cond\spast)\s+", morphoSyntactic )
    if (particTimeMatch):
        return particTimeMatch.group(1)
    timeMatch = re.match( ".*\s+(pres|impf)\s+", morphoSyntactic )
    if (timeMatch):
        return timeMatch.group(1)
    else:
        return None

def getSyntacticFunction(morphoSyntactic):
    functionMatch = re.match( ".*\s(@\S+)\s*", morphoSyntactic )
    if (functionMatch):
        return functionMatch.group(1)
    else:
       return None

# ================================================================
#    Clause boundary detection
# ================================================================

#  For each token in lause, notes down whether it should be a clause boundary
# (CLO, CLC, crd CLB, CLB) or a finite verb (FMV or FCV); If token is neither 
# of these, an empty string is used to note that it is a regular string.
#  Returns list of labels;
#   If "crd CLB" has a finite verb on both sides, a special marking "crd CLB+"
#  is used;
def get_CLB_and_FinVerb_labels( sentence ):
    labels = []
    finVerbMatcher = re.compile("(@FMV|@FCV)")
    for j in range(len( sentence )):
        #for [sentenceID, wordID, token, morphSyntactic, label, parent] in sent:
        #(token, morphSynt, label, parentLabel, anno) = sentence[j]
        [sentenceID, wordID, token, morphSynt, label, parent] = sentence[j]
        # 1) Find, whether we have a finite verb or not
        syntFunc = getSyntacticFunction(morphSynt)
        label = ""
        if (syntFunc):
            finVerbMatch = finVerbMatcher.match(syntFunc)
            if (finVerbMatch):
                label = finVerbMatch.group(1)
        # 2) Find whether we have a clause boundary or not
        morphSynt = re.sub("(\"\(\"\sZ\sOpr\sCLBC)\sCLB", "\\1 CLO", morphSynt)
        morphSynt = re.sub("(\"\)\"\sZ\sCpr\sCLBC)\sCLB", "\\1 CLC", morphSynt)
        if (re.match(".*\sCLB\sCLO\s*.*", morphSynt)):
            label = "CLB CLO"
        elif (re.match(".*\sCLB\sCLC\s*.*", morphSynt)):
            label = "CLB CLC"
        elif (re.match(".*\scrd\sCLB\s*.*", morphSynt)):
            label = "crd CLB"
        elif (re.match(".*\sCLB(\s*|\s.+)$", morphSynt)):
            label = "CLB"
        labels.append(label)
    # Mark these crd boundaries which have a finite verb on both sides
    for i in range(len(labels)):
        label = labels[i]
        if (label == "crd CLB"):
            finPrecedes = False
            j = i - 1
            while (j > -1):
                if (finVerbMatcher.match(labels[j])):
                    finPrecedes = True
                    break
                elif (len(labels[j]) > 0):
                    break
                j = j - 1
            finFollows = False
            j = i + 1
            while (j < len(labels)):
                if (finVerbMatcher.match(labels[j])):
                    finFollows = True
                    break
                elif (len(labels[j]) > 0):
                    break
                j = j + 1
            if ( finPrecedes and finFollows ):
                labels[i] = labels[i]+"+"
    return labels

#  Finds whether two nodes in syntactic tree are in different
# clauses (separated by clause markers CLB).
#  If onlySubordination == True, only subordination relations
# are considered as relations distinguishing sentences;
def in_different_clauses(sentence, label1, label2, clbFinLabels = None, onlySubordination = False):
    if (not clbFinLabels):
        clbFinLabels = get_CLB_and_FinVerb_labels( sentence )
    firstLabelFound = -1
    secondLabel     = -1
    CLBseen = False
    insideCleft = 0
    # If there is Fin on both sides
    firstLabelBoundaries  = []
    secondLabelBoundaries = []
    for j in range(len(sentence)):
        [sentenceID, wordID, token, morphSynt, label, parent] = sentence[j]
        if (firstLabelFound == -1):
            if (label == label1):
                firstLabelFound = label1
                secondLabel     = label2
            if (label == label2):
                firstLabelFound = label2
                secondLabel     = label1
        else:
            clbFinLabel = clbFinLabels[j]
            if (len(clbFinLabel) > 0):
                #  Cleft-clauses: assuming only one level of cleft clauses,
                # no clefts inside clefts ...
                if (clbFinLabel == "CLB CLO"):
                    insideCleft = insideCleft + 1
                elif (clbFinLabel == "CLB CLC"):
                    insideCleft = insideCleft - 1
                elif (re.match(".*CLB.*", clbFinLabel) and insideCleft == 0):
                    # Skip co-ordinated clauses, consider only subordination;
                    if (not clbFinLabel == "crd CLB"):
                        # Non co-ordinated clauses (subordinated clauses) are always OK
                        if (not onlySubordination or (onlySubordination and not clbFinLabel == "crd CLB+")):
                            # Co-ordinated clauses with finite verbs on both sides ("crd CLB+")
                            # are OK depending of the flag onlySubordination;
                            CLBseen = True
            if (label == secondLabel):
                if (insideCleft != 0):
                    # If we did not pass the cleft throughly, we take it 
                    # as an clause boundary ...
                    CLBseen = True
                return CLBseen
    return False

# ================================================================
#   Detection of the syntactic predicate structure of the clause
# ================================================================

#  Finds and returns the predicate structure (elements tagged with 
# NEG, FMV, FCV, IMV, ICV) of the clause surrounding the labelToFind;
#  Returns a list of lause elements that belong to the predicate
# structure and Boolean indicating whether the returned list is
# two-level (meaning that there was more than one finite verb inside
# the clause boundaries);
def getClPredicateStructure(sentence, labelToFind, clbFinLabels = None):
    if (not clbFinLabels):
        clbFinLabels = get_CLB_and_FinVerb_labels(sentence)
    clbMatcher = re.compile("^(CLB|CLB\s(CLO|CLC)|crd\sCLB\+)$")
    # 1) Leiame osalausepiirid antud label'iga token'i jaoks
    leftBound  = -1
    rightBound = -1
    for j in range( len(sentence) ):
        #(token, morphSynt, label, parentLabel, anno) = lause[j]
        [sentenceID, wordID, token, morphSynt, label, parent] = sentence[j]
        if (int(labelToFind) == int(label)):
            i = j
            while(i > -1):
                if (clbMatcher.match(clbFinLabels[i])):
                    leftBound = i
                    break
                i = i - 1
                if (i == -1):
                    leftBound = 0
            i = j + 1
            if (i == len(clbFinLabels)):
                rightBound = len(clbFinLabels)-1
            while(i < len(clbFinLabels)):
                if (clbMatcher.match(clbFinLabels[i])):
                    rightBound = i
                    break
                i = i + 1
                if (i == len(clbFinLabels)):
                    rightBound = len(clbFinLabels)-1
    if (rightBound == -1 or leftBound == -1):
        tokens = [ (t[1],t[2]) for t in sentence ]
        print (tokens)
        raise Exception(" Could not locate clause boundaries for the element with label "+label)
    # 2) Leiame predikaatstruktuuri osalausepiiride seest
    verbChainMatcher = re.compile("@(NEG|FMV|FCV|IMV|ICV)")
    verbChain = []
    finVerbCount = 0
    for j in range( leftBound, rightBound + 1 ):
        #(token, morphSynt, label, parentLabel, anno) = lause[j]
        [sentenceID, wordID, token, morphSynt, label, parent] = sentence[j]
        syntFunct = getSyntacticFunction(morphSynt)
        if (syntFunct and verbChainMatcher.match(syntFunct)):
            if (re.match("@(FMV|FCV)", syntFunct)):
                finVerbCount = finVerbCount + 1
            verbChain.append( sentence[j] )
    if (finVerbCount > 1):
        #  V6ib juhtuda, et syntaktilise analyysi vea t6ttu on osalausepiirid
        # nigelalt ning tuleb verbiahel, kus on mitu finiitverbi; Proovime 
        # sellisel juhul grupeerida omakorda osalause sees ...
        grouped = groupPredicateParts(verbChain)
        sortedGroups = [ sortPredicateParts(verbChain) for verbChain in grouped ]
        return (sortedGroups, True)
    else:
        return (sortPredicateParts(verbChain), False)


# Sorts elements of the predicate structure;
# Assumes the "natural order" is "@NEG", "@FCV", "@FMV", "@ICV", "@IMV"
def sortPredicateParts(verbChain):
    newChain = []
    # 1) Lisame kindlalt finiitverbi koosseisu kuuluvad elemendid
    for part in [ "@NEG", "@FCV", "@FMV", "@ICV", "@IMV" ]:
        for t in verbChain:
            morphSynt = t[3]
            syntFunc = getSyntacticFunction(morphSynt)
            if (syntFunc and syntFunc == part):
                newChain.append(t)
    # 2) Lisame k6ik ylej22nud elemendid
    for t in verbChain:
        if (t not in newChain):
            newChain.append(t)
    return newChain


#  Tries to separate different clauses inside verbChain by grouping
# them around finite verbs (there shouldn't be more than one finite 
# verb in a clause); Uses a naive heuristic for grouping;
def groupPredicateParts(verbChain):
    groups = []
    for t in verbChain:
        if (len(groups) == 0):
            groups.append([t])
        else:
            addNewGroup = False
            lastGroup = groups[-1]
            groupSynt = [ getSyntacticFunction(t1[3]) for t1 in lastGroup ]
            if ("@FMV" in groupSynt or "@FCV" in groupSynt):
                # Last group has finite verb
                thisSynt = getSyntacticFunction( t[3] )
                if (thisSynt=="@FMV" or thisSynt=="@FCV" or thisSynt=="@NEG"):
                    addNewGroup = True
                    #  TODO: ära-predikaadid (nt ärgem_@FCV ajagem_@FMV) lähevad
                    # siin samuti katki;
            if (addNewGroup):
                groups.append([t])
            else:
                groups[-1].append(t)
    return groups

# ================================================================
#    Detects tense of the main verb
# ================================================================

# Determine grammatical tense(s) of the clause predicate(s):
#    pres - olevik e present
#    impf - lihtminevik e imperfekt
#    pf   - taisminevik
#    pqpf - enneminevik
#    cond past - tingliku kõneviisi minevik;
def getPredicateTense(verbChains, grouped):
    if (not grouped):
        verbChains = [ verbChains ]
    tenses = []
    for verbChain in verbChains:
        #vcLabels = [ t[4] for t in verbChain ]
        #vcTokens = [ t[2] for t in verbChain ]
        tense = ""
        vcTimes  = [ getVerbTime(t[3]) for t in verbChain ]
        vcTimes  = ['_' if t is None else t for t in vcTimes]
        vcLemmas = [ getLemma(t[3]) for t in verbChain ]
        vcSynts  = [ getSyntacticFunction(t[3]) for t in verbChain ]
        # Single-word tenses: impf or pres
        vcTimesSet = set(vcTimes)
        if (len(vcTimesSet) == 1 or (len(vcTimesSet) == 2 and "_" in vcTimesSet)):
            if ("impf" in vcTimesSet):
                tense = "impf"
            elif ("pres" in vcTimesSet):
                tense = "pres"
            elif ("cond past" in vcTimesSet):
                tense = "cond past"
        if (len(vcTimes) > 1 and len(tense) == 0):
            # Composite tenses:
            if (vcTimes[0] == "impf" and vcLemmas[0] == "ole"):
                allPastPart = True
                for j in range(1, len(vcTimes)):
                    if (vcTimes[j] != "partic past"):
                        allPastPart = False
                if (allPastPart):
                    tense = "pqpf"
            if (vcTimes[0] == "pres" and vcLemmas[0] == "ole"):                            
                allPastPart = True
                for j in range(1, len(vcTimes)):
                    if (vcTimes[j] != "partic past"):
                        allPastPart = False
                if (allPastPart):
                    tense = "pf"
        # Negation or composite tense ("täis/enneminevik") with the infinite verb ...
        if ((len(vcTimesSet) == 3 and "_" in vcTimesSet) and len(tense) == 0):
            if ("pres" in vcTimesSet):
                presLoc = vcTimes.index("pres")
                if (presLoc > -1 and presLoc + 1 < len(vcTimes)):
                    if (vcTimes[presLoc + 1] == "partic past"):
                        tense = "pf"
            if ("impf" in vcTimesSet):
                impfLoc = vcTimes.index("impf")
                if (impfLoc > -1 and impfLoc + 1 < len(vcTimes)):
                    if (vcTimes[impfLoc + 1] == "partic past"):
                        tense = "pqpf"
        #  What will be left undetermined:
        #  -- da-infinitive as the main verb;
        #  -- nud/tud-infinitive as the main verb; (elliptic 'olema'?)
        #  -- past of the conditional mood;
        tenses.append( tense )
    return tenses

