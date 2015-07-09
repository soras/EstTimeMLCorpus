# -*- coding: utf-8 -*- 
#
#     Methods for processing dependency syntactic annotations and 
#    dependency trees.
#
#    Developed and tested under Python's version: 3.4.1
#

import re

import sol_format_tools

# ================================================================
#    Dependency tree data structure
# ================================================================
class Tree(object):
    def __init__(self, label, wordID, data):
        self.label    = label
        self.wordID   = wordID
        self.data     = data
        self.parent   = None
        self.children = None

    def addChild(self, tree):
        if (not self.children):
            self.children = []
        tree.parent = self
        self.children.append(tree)

    def addChildToSubTree(self, nodeLabel, tree):
        if (self.label == nodeLabel):
            self.addChild(tree)
        elif (self.children):
            for child in self.children:
                child.addChildToSubTree(nodeLabel, tree)

    def printTree(self, spacing):
        print(spacing + " " + self.label + " "+self.data[0])
        if (self.children):
            spacing = spacing + " "
            for child in self.children:
                child.printTree(spacing)

    def findSubTree(self, nodeLabel):
        if (self.label == nodeLabel):
            return self
        elif (self.children):
            for child in self.children:
                tree = child.findSubTree( nodeLabel )
                if (tree):
                    return tree
        return None

    def findParentTree(self, nodeLabel):
        if (self.label == nodeLabel):
            return self
        elif (self.parent):
            return (self.parent).findParentTree(nodeLabel)
        return None

    def findTaggedSubTrees(self, sentAnnotations, tag, depthLimit, onlyHeaderMatch = False):
        subtrees = []
        if (self.children and (depthLimit > 0 or depthLimit < 0) ):
            headerTag = re.compile('^(EVENT|TIMEX)\s+([A-Z_]+)\s*')
            for child in self.children:
                childAnnotations = [ a for a in sentAnnotations if a[2]==int(child.wordID) ]
                if childAnnotations:
                    for [ annotator, sentenceID, wordID, eID, expr, ann ] in childAnnotations:
                        if onlyHeaderMatch and not headerTag.match(ann):
                            continue
                        if (tag == "EVENT" and re.match('^EVENT', ann)):
                            subtrees.append(child)
                        elif (tag == "TIMEX" and re.match('^TIMEX', ann)):
                            subtrees.append(child)
                        elif (tag != "EVENT" and tag != "TIMEX"):
                            raise Exception(' Unknown tag: "'+tag+'" ')
            for child in self.children:
                childsResults = \
                   child.findTaggedSubTrees(sentAnnotations, tag, depthLimit-1, onlyHeaderMatch)
                if (len(childsResults) > 0):
                    subtrees.extend(childsResults)
        return subtrees

    def findTaggedParentTrees(self, sentAnnotations, tag, heightLimit, onlyHeaderMatch = False):
        subtrees = []
        if (self.parent and (heightLimit > 0 or heightLimit < 0) ):
            headerTag = re.compile('^(EVENT|TIMEX)\s+([A-Z_]+)\s*')
            parentAnnotations = [ a for a in sentAnnotations if a[2]==int(self.parent.wordID) ]
            if parentAnnotations:
                for [ annotator, sentenceID, wordID, eID, expr, ann ] in parentAnnotations:
                    if onlyHeaderMatch and not headerTag.match(ann):
                        continue
                    if (tag == "EVENT" and re.match('^EVENT', ann)):
                        subtrees.append(self.parent)
                    elif (tag == "TIMEX" and re.match('^TIMEX', ann)):
                        subtrees.append(self.parent)
                    elif (tag != "EVENT" and tag != "TIMEX"):
                        raise Exception(' Unknown tag: "'+tag+'" ')
            parentResults = \
              self.parent.findTaggedParentTrees(sentAnnotations, tag, heightLimit-1, onlyHeaderMatch)
            if (len(parentResults) > 0):
                subtrees.extend(parentResults)
        return subtrees

    def getSubtreesSortedByLabel( self ):
        subtrees = [ self ]
        if (self.children):
            for child in self.children:
                childsResults = child.getSubtreesSortedByLabel()
                if (len(childsResults) > 0):
                    subtrees.extend(childsResults)
        # Sort trees based on their syntactic labels
        return sorted(subtrees, key=lambda x: int(x.label))

    def getTreeDepth( self ):
        if (self.children):
            depth = 1
            childDepths = []
            for child in self.children:
                childDepths.append( child.getTreeDepth() )
            return depth + max(childDepths)
        else:
            return 0


# ================================================================
#    Building dependency trees from the annotations
# ================================================================

#  Builds sentence trees from dependency syntactic annotations;
#  Assumes that the input 'sentences' is a list of sentences,
#  each sentence consisting of word-describing tuples:
#    [sentenceID, wordID, token, morphSyntactic, syntacticID, syntacticHeadID]
def build_dependency_trees( sentences ):
    allSentenceTrees = []  # Lausepuude j2rjend
    for sent in sentences:
        trees_of_a_sentence = []
        nodes = [ "0" ]
        while(len(nodes) > 0):
            node = nodes.pop(0)
            #for (t, ms, label, parent, annotations) in lause:
            for [sentenceID, wordID, token, morphSyntactic, label, parent] in sent:
                if (parent == node and label != parent):
                    tree1 = Tree( label, wordID, (token, morphSyntactic, label, parent, []) )
                    if (parent == "0"):
                        # Add the root node
                        trees_of_a_sentence.append(tree1)
                    else:
                        # For each root node, attempt to add the child
                        for root_node in trees_of_a_sentence:
                            root_node.addChildToSubTree(parent, tree1)
                    nodes.append(label)
        allSentenceTrees.append(trees_of_a_sentence)
    return allSentenceTrees


# ================================================================
#    Adding clause boundary information to the trees
# ================================================================

ROOT            = 1
BETWEEN_CLAUSES = 2
IN_CLAUSE       = 3

# Adds clause boundary information to sentence trees
def add_clause_info_to_trees(sentences, sentTrees):
    global ROOT, BETWEEN_CLAUSES, IN_CLAUSE
    for i in range(len(sentences)):
        sentence = sentences[i]
        sentTree = sentTrees[i]
        clbFinLabels = sol_format_tools.get_CLB_and_FinVerb_labels(sentence)
        for root in sentTree:
            treeList = [ root ]
            while(len(treeList) > 0):
                tree = treeList.pop(0)
                if (tree.parent):
                    if (sol_format_tools.in_different_clauses(sentence, tree.label, tree.parent.label, clbFinLabels = clbFinLabels)):
                        # Find, whether we have a coordinating or subordinating boundary:
                        tree.crd_clb = True
                        if (sol_format_tools.in_different_clauses(sentence, tree.label, tree.parent.label, clbFinLabels = clbFinLabels, onlySubordination = True)):
                            tree.crd_clb = False
                        tree.clb_rel = BETWEEN_CLAUSES
                    else:
                        tree.clb_rel = IN_CLAUSE
                else:
                    tree.clb_rel = ROOT
                if (tree.children):
                    for c in tree.children:
                        treeList.append(c)


# ===================================================================
#   Finding sentence-internal Event-to-event argument relations 
# ===================================================================

#
#   Attempts to find all event-event argument structures of TimeML
#  events from classes that require an argument ("REPORTING", "I_ACTION", 
#  "ASPECTUAL", "I_STATE", "PERCEPTION", "MODAL");
#
#   NB! Basically, the method finds all direct children or direct
#  parent of the event that requires an argument. Results are redundant:
#  can contain incorrect argument-suggestions;
#
#  Returns a list of items, in the form:
#      [ KS,  tree_of_the_parent_event, tree_of_subevent1, tree_of_subevent2 etc. ]
#  where
#     KS = True, if all relations follow the syntactic relations (subevents are also
#                children according to the syntax);
#     KS = False, if there is a mismatch with syntax (a subevent is actually a parent
#                 according to the syntax);
# 
def getEventArgStructInSentence(sentence, sentenceTrees, sentAnnotations, \
            onlyIntraClause = False, useAllClasses = False, onlyDepthOne = True):
    # 0) Index all TimeML annotations for easier access:
    wordToAnnotation = dict()
    for annotation in sentAnnotations:
        if annotation[2] not in wordToAnnotation:
            wordToAnnotation[annotation[2]] = []
        wordToAnnotation[annotation[2]].append( annotation )
    # 1) Find all argument-demanding TimeML events from the sentence
    #    Assign a syntactic tree to all of them
    argDemandingEvents       = []
    argDemandingEventTrees   = []
    argDemandingEventClasses = []
    timeMLargDemandingClasses = ["REPORTING", "I_ACTION", "ASPECTUAL", "I_STATE", \
                                 "PERCEPTION", "MODAL"]
    eventHeader = re.compile('^EVENT\s+([A-Z_]+)')
    for i in range(len(sentence)):
        [sentenceID, wordID, token, morphSyntactic, label, parent] = sentence[i]
        if int(wordID) in wordToAnnotation:
            for [ annotator, sentenceID_int, wordID_int, eID, expr, ann ] in wordToAnnotation[int(wordID)]:
                if eventHeader.match( ann ):
                    headerParts = ann.split()
                    eClass = headerParts[1]
                    if (eClass in timeMLargDemandingClasses or useAllClasses):
                        argDemandingEvents.append(sentence[i])
                        argDemandingEventClasses.append(eClass)
                        subTreeFound = False
                        for root in sentenceTrees:
                            subTree = root.findSubTree(label)
                            if (subTree):
                                argDemandingEventTrees.append( subTree )
                                subTreeFound = True
                                break
                        if (not subTreeFound):
                             raise Exception(" Subtree with label "+str(label)+ " not found. ")
    # 2) Collect possible arguments of given EVENT's
    eventsWithArguments = []
    for i in range(len(argDemandingEvents)):
        tokenStruct = argDemandingEvents[i]
        tree        = argDemandingEventTrees[i]
        timeMLclass = argDemandingEventClasses[i]
        subTrees = tree.findTaggedSubTrees(sentAnnotations, "EVENT", -1, onlyHeaderMatch = True)
        if (len(subTrees) > 0):
            # Keep only subtrees that have this tree as direct parent
            filteredSubTrees = []
            for subTree in subTrees:
                if (subTree.parent == tree):
                    filteredSubTrees.append( subTree )
            if (len(filteredSubTrees) == 0):
                #  If nothing was left, however, we only had one subtree, assume that
                # it could be the correct subtree ...
                if (onlyDepthOne and len(subTrees) == 1):
                    filteredSubTrees = subTrees
                elif (not onlyDepthOne and len(subTrees) > 0):
                    filteredSubTrees = subTrees
            eventWithArguments = [ True ]
            eventWithArguments.append( tree )
            eventWithArguments.extend( filteredSubTrees )
            eventsWithArguments.append( eventWithArguments )
        else:
            # Take the initial parent as a potential subtree
            superTrees = \
              tree.findTaggedParentTrees(sentAnnotations, "EVENT", -1, onlyHeaderMatch = True)
            eventAdded = False
            if (len(superTrees) > 0 and (timeMLclass in timeMLargDemandingClasses)):
                for superTree in superTrees:
                    amongstChildren = False
                    if (sol_format_tools.in_different_clauses(sentence, tree.label, superTree.label)):
                        # If the syntactic parent is outside the clause boundaries, 
                        # do not use it as a potential argument ...
                        continue
                    if (superTree.children):
                        for child in superTree.children:
                            if (child.label == tree.label):
                                amongstChildren = True
                                break
                    if (amongstChildren):
                        eventWithArguments = [ False ]
                        eventWithArguments.append( tree )
                        eventWithArguments.append( superTree )
                        eventsWithArguments.append( eventWithArguments )
                        eventAdded = True
                        break
            if (not eventAdded):
                eventWithArguments = [ False ]
                eventWithArguments.append( tree )
                eventsWithArguments.append( eventWithArguments )
    # 3) Filter if necessary
    if (onlyIntraClause):
        #  ****  Keep only inside-clause arguments of the events ...
        newEventsWithArgs = []
        for eventWithArgs in eventsWithArguments:
            treeSeq  = [ eventWithArgs[j] for j in range(1, len(eventWithArgs)) ]
            labelSeq = [ tree.label for tree in treeSeq ]
            if (len(labelSeq) > 1):
                parentLabel = labelSeq[0]
                keepTrees = []
                for i in range( 1, len(labelSeq) ):
                    if (not sol_format_tools.in_different_clauses(sentence, parentLabel, labelSeq[i])):
                        keepTrees.append( treeSeq[i] )
                newData = [ eventWithArgs[0], treeSeq[0] ]
                newData.extend ( keepTrees )
                newEventsWithArgs.append( newData )
            else:
                newEventsWithArgs.append( eventWithArgs )
        eventsWithArguments = newEventsWithArgs
    return eventsWithArguments


#  Fix argument structure of multiword events: remove redundant subevents, and 
# collect dependencies from all parts of the multiword ...
def fixMWEventArgStruct(sentence, sentenceTrees, sentAnnotations, eventsWithArguments, onlyDepthOne = True):
    newEventsWithArgs = []
    eventHeader = re.compile('^EVENT\s+([A-Z_]+)')
    for eventWithArgs in eventsWithArguments:
        mainTree    = eventWithArgs[1]
        mainTreeWID = mainTree.wordID
        # Gather all multiword EVENT annotations associated with the main tree
        mwEventAnns = []
        for [ annotator, sentID_int, wordID_int, eID, expr, ann ] in sentAnnotations:
            if int(mainTree.wordID) == wordID_int and eventHeader.match(ann) and \
               expr and expr.find(" ") > -1:
                mwEventAnns.append( [wordID_int, eID, expr, ann] )
        if mwEventAnns:
            for [wordID_int, eID, expr, ann] in mwEventAnns:
                # 1) Locate other parts of the multiword annotation:
                otherParts       = []
                otherPartsLabels = []
                for [ annotator, sentID_int, wordID_int_2, eID_2, expr_2, ann_2 ] in sentAnnotations:
                    if wordID_int != wordID_int_2  and  eID == eID_2:
                        otherParts.append( [wordID_int_2, eID_2, expr_2, ann_2] )
                        for l in range( len(sentence) ):
                            [sID, wID, tok, morphSynt, label, parent] = sentence[l]
                            if int(wID) == wordID_int_2:
                                otherPartsLabels.append( str(label) )
                if not otherParts or len(otherParts) != len(otherPartsLabels):
                    raise Exception(' Unable to find correct other parts of the EVENT annotation:',\
                          [eID, expr, ann],' ', otherParts, otherPartsLabels)
                          
                newEventWithArgs = []
                # 2) Remove other parts that were mistakenly considered as subtrees/subevents
                if (len(eventWithArgs) > 2):
                    children = filter(lambda x: x.label not in otherPartsLabels, eventWithArgs[2:])
                    newEventWithArgs = eventWithArgs[0:2]
                    newEventWithArgs.extend( children )
                else:
                    newEventWithArgs = eventWithArgs
                # 3) Find subtrees of the other parts and add as subtrees of the main tree
                for label in otherPartsLabels:
                    tree = None
                    for root in sentenceTrees:
                        subTree = root.findSubTree(label)
                        if (subTree):
                            tree = subTree
                    if (not tree):
                        raise Exception(" Could not find subtree with label "+label)
                    else:
                        subTrees = tree.findTaggedSubTrees(sentAnnotations, "EVENT", -1, onlyHeaderMatch = True)
                        if (len(subTrees) > 0):
                            # Keep only subtrees parented by the current tree
                            filteredSubTrees = []
                            for subTree in subTrees:
                                if (subTree.parent == tree):
                                    filteredSubTrees.append( subTree )
                            if (len(filteredSubTrees) == 0):
                                #  If nothing was left, however, we only had one subtree, assume that
                                # it could be the correct subtree ...
                                if (onlyDepthOne and len(subTrees) == 1):
                                    filteredSubTrees = subTrees
                                elif (not onlyDepthOne and len(subTrees) > 0):
                                    filteredSubTrees = subTrees
                            newEventWithArgs.extend( filteredSubTrees )
                # 4) Add to the new set of results
                newEventsWithArgs.append( newEventWithArgs )
        elif len(mwEventAnns) > 1:
            raise Exception(' Unexpectedly multiple EVENT annotation per label: ',mwEventAnns)
        else:
            newEventsWithArgs.append(eventWithArgs)
    return newEventsWithArgs


def getChainOfCoordinateEvents(sentence, sentenceTrees, sentAnnotations, label):
    # 1) Find location of current token in the syntactic tree
    cTree = None
    for root in sentenceTrees:
        subTree = root.findSubTree(label)
        if (subTree):
            cTree = subTree
            break
    if (cTree == None):
        raise Exception(" Token with label ",label, " not found. ")
    cSyntFunc = sol_format_tools.getSyntacticFunction( cTree.data[1] )
    # 2) Find all of it's co-ordinate EVENTs (subevents that have same label)
    subTrees = cTree.findTaggedSubTrees(sentAnnotations, "EVENT", -1, onlyHeaderMatch = True)
    result = [ cTree ]
    for subTree1 in subTrees:
        cSyntFunc1 = sol_format_tools.getSyntacticFunction( subTree1.data[1] )
        if (cSyntFunc and cSyntFunc1 and cSyntFunc1 == cSyntFunc):
            result.append( subTree1 )
    return result
