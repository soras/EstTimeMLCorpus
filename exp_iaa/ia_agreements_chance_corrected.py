# -*- coding: utf-8 -*- 
#
#   Chance-corrected inter-annotator agreement measures:
#      * Cohen's Kappa
#      * Scott's PI
#      * Krippendorff's Alpha
#
#   Developed and tested under Python's version: 3.4.1
#

import sys, os, re
from math import fsum

# ============================================================
#    Updating and converting contingency tables
# ============================================================

#  Updated contingency table in the counter (an instance of AggregateCounter)
def update_contingency_table(annotatorA, annotatorB, responseA, responseB, counter, conterKey, pair):
    tableKey = "table:"+responseA+"___"+responseB
    counter.addToCount(conterKey, pair, tableKey, 1)


#  Records the contigency table to the counter (an instance of AggregateCounter)
def transfer_contingency_table(counter, conterKey, pair, confMatrix, attribName):
   for key in confMatrix.keys():
        keyMatch = re.match("^([^:]+):(.+)$", key)
        if (keyMatch):
            attrib = keyMatch.group(1)
            if (attrib == attribName):
                (v1, v2) = (keyMatch.group(2)).split("___")
                update_contingency_table("", "", v1, v2, counter, conterKey, pair)


#  Reconstructs a contigency table (confusion matrix) from the values 
# recorded in an instance of AggregateCounter (counter);
def reconstruct_contigency_table(counter, conterKey, pair):
    allRecords = (counter.getCounts())[conterKey][pair]
    allResponses = dict()
    table = dict()
    for record in allRecords:
        tableRecordMatch = re.match("^table:(.+)$", record)
        if (tableRecordMatch):
            r = tableRecordMatch.group(1)
            (respA, respB) = r.split("___")
            allResponses[respA] = 1
            allResponses[respB] = 1
            if (respA not in table):
                table[respA] = dict()
            if (respB not in table[respA]):
                table[respA][respB] = 0
            table[respA][respB] += counter.getCount(conterKey, pair, record)
    # Add null-fields
    for resp1 in allResponses:
        if (resp1 not in table):
            table[resp1] = dict()
            for resp2 in allResponses:
                table[resp1][resp2] = 0
    for resp1 in allResponses:
        for resp2 in allResponses:
            if (resp2 not in table[resp1]):
                table[resp1][resp2] = 0
    return (table, allResponses)


# ============================================================
#    Debug: counting elements in the confusion matrix;
#           finding agreements without chance correction;
# ============================================================

#  Extracts how many times each value was suggested (by both annotators)
# from the list of contingency tables ...
def collectValueCountsFromConfTables( listOfTables ):
    valueCounts = dict()
    for table in listOfTables:
        for a in table.keys():
            for b in table[a].keys():
                if (a not in valueCounts):
                    valueCounts[a] = 0
                if (b not in valueCounts):
                    valueCounts[b] = 0
                valueCounts[a] += table[a][b]
                valueCounts[b] += table[a][b]
    return valueCounts

#  Formats output of the method collectValueCountsFromConfTables()
def formatValCountsAsStr( valueCounts ):
    allCounts = 0
    for k in valueCounts.keys():
        allCounts += valueCounts[k]
    sortedKeys = sorted( valueCounts, key = lambda key: valueCounts[key], reverse = True )
    resStr = ""
    for k in sortedKeys:
        percentage = valueCounts[k] * 100.0 / allCounts
        keyStr = k
        if (keyStr == "IDENTITY"):
            keyStr = "ID"
        elif (keyStr == "BEFORE"):
            keyStr = "BEF"
        elif (keyStr == "AFTER"):
            keyStr = "AFT"
        elif (keyStr == "BEFORE-OR-OVERLAP"):
            keyStr = "BEF-OVR"
        elif (keyStr == "OVERLAP-OR-AFTER"):
            keyStr = "AFT-OVR"
        elif (keyStr == "SIMULTANEOUS"):
            keyStr = "SIM"
        elif (keyStr == "IS_INCLUDED"):
            keyStr = "INCD"
        elif (keyStr == "INCLUDED"):
            keyStr = "INCD"
        elif (keyStr == "INCLUDES"):
            keyStr = "INCS"
        elif (keyStr == "VAGUE"):
            keyStr = "VAG"
        resStr += keyStr+" "+'{:.3}'.format( percentage )+"%  "
    return resStr

# Finds accuracy (an agreement without chance correction)
def find_Accuracy(table, allResponses):
    allSuggestions = 0
    agreements     = 0
    for a in table.keys():
        for b in table[a].keys():
            if (a == b):
                agreements += table[a][b]
            allSuggestions += table[a][b]
    acc = -1.0
    if (allSuggestions > 0):
        acc = agreements/allSuggestions
    return (acc, agreements, allSuggestions)

# Finds accuracy (an agreement without chance correction) using a special distance function
def find_weighted_Accuracy(table, allResponses, distanceMetric):
    allSuggestions = 0
    agreements     = 0
    for a in table.keys():
        for b in table[a].keys():
            agreements += table[a][b] * (1.0 - distanceMetric(a, b))
            allSuggestions += table[a][b]
    acc = -1.0
    if (allSuggestions > 0):
        acc = agreements/allSuggestions
    return (acc, agreements, allSuggestions)


# ============================================================
#    Chance-corrected agreement measures
# ============================================================

# The implementation follows the guide:  http://gate.ac.uk/sale/tao/splitch10.html
def find_Cohens_Kappa(table, allResponses):
    # Find marginal sums and total
    ann1_marginals = []
    for respA in allResponses:
        sum1 = 0
        for respB in allResponses:
            sum1 = sum1 + table[respA][respB]
        ann1_marginals.append( sum1 )
    ann2_marginals = []
    for respB in allResponses:
        sum1 = 0
        for respA in allResponses:
            sum1 = sum1 + table[respA][respB]
        ann2_marginals.append( sum1 )
    if (sum(ann1_marginals) != sum(ann2_marginals)):
        raise Exception(' Lists of marginals give different sums: '+str(ann1_marginals)+' vs '+str(ann2_marginals))
    total = sum(ann1_marginals)
    # Find expected agreement:
    # 1) Find proportions
    ann1_marginals = map(lambda x: x / total, ann1_marginals)
    ann2_marginals = map(lambda x: x / total, ann2_marginals)
    # 2) get the likelihood of chance agreement
    likelihoods = [ a*b for (a,b) in list(zip(ann1_marginals, ann2_marginals)) ]
    # 3) get total sum as expected agreement
    expected = fsum(likelihoods)
    # Find observed agreement
    observed_agreements = [ table[resp][resp] for resp in allResponses ]
    observed = sum(observed_agreements) / total
    # Find Cohen's Kappa
    if (1 - expected != 0):
        kappa = (observed - expected)/(1 - expected)
    else:
        kappa = -10.0
    return (kappa, observed, expected, table)


#
# The implementation follows the guide in article:  The Kappa statistic: a second look 
#  http://www.eecis.udel.edu/~carberry/CIS-885/Papers/DiEugenio-Kappa-Second-Look.pdf
#  Siegel & Castellan's Kappa:
#     -- should be tolerant to the bias effect, e.g. if there are great differences 
#        between the ways two annotators are annotating the text, the bias effect causes
#        unjustifiably high Cohen's Kappa value;
#  NB! Should be very similar to Scott's PI;
def find_Siegel_Castellan_Kappa(table, allResponses):
    # 1) For each category, find overall proportion of items assigned to the category
    categoryItems = dict()
    allItems = 0
    total = 0
    for respA in allResponses:
        for respB in allResponses:
            if (respA == respB):
                if (respA not in categoryItems):
                    categoryItems[respA] = 0
                categoryItems[respA] += table[respA][respB]*2
                allItems += table[respA][respB]*2
                total += table[respA][respB]
            else:
                if (respA not in categoryItems):
                    categoryItems[respA] = 0
                if (respB not in categoryItems):
                    categoryItems[respB] = 0
                categoryItems[respA] += table[respA][respB]
                categoryItems[respB] += table[respA][respB]
                allItems += table[respA][respB]*2
                total += table[respA][respB]
    # 2) Find proportion squares
    proportionSquares = []
    for respA in allResponses:
        proportion = categoryItems[respA]/allItems
        proportionSquares.append( proportion**2 )
    # 3) Sum proportion squares and find Kappa
    expected = fsum( proportionSquares )
    # Find observed agreement
    observed_agreements = [ table[resp][resp] for resp in allResponses ]
    observed = sum(observed_agreements) / total
    # Find Siegel & Castellan's Kappa
    if (1 - expected != 0):
        kappa = (observed - expected)/(1 - expected)
    else:
        kappa = -10.0
    return (kappa, observed, expected, table)

#
# The implementation follows the guide in article:  The Kappa statistic: a second look 
#  http://www.eecis.udel.edu/~carberry/CIS-885/Papers/DiEugenio-Kappa-Second-Look.pdf
#  Returns Cohen's Kappa and it's adjustments:
#     1. an adjustment for prevalence;
#     2. an adjustment for bias;
def find_adj_Cohens_Kappa_using_CounterTable(counter, conterKey, pair):
    (table, allresponses) = reconstruct_contigency_table(counter, conterKey, pair)
    (kappa_Co, observed_Co, expected_Co, table_Co) = \
        find_Cohens_Kappa(table, allresponses)
    (kappa_SC, observed_SC, expected_SC, table_SC) = \
        find_Siegel_Castellan_Kappa(table, allresponses)
    K_adj_for_prevalence = 2.0*observed_Co - 1.0
    K_adj_for_bias       = kappa_SC
    return (kappa_Co, K_adj_for_prevalence, K_adj_for_bias, observed_Co, table_Co)

#
# The implementation follows the guide:  
#  Artstein, Ron and Massimo Poesio. 2008. Inter-coder agreement for Computational Linguistics. 
#  Computational Linguistics.
#  NB! Should be very similar to Siegel&Castellan's Kappa;
def find_Scotts_PI(table, allResponses):
    #   i - cardinality of the set of annotated items;
    #   k - cardinality of the set of possible categories;
    #   c - cardinality of the set of coders(annotators);
    #   n_ik - the number of coders who assigned item i to category k;
    #   n_ck - the number of items assigned by coder c to category k;
    #   n_k  - the total number of items assigneb by all coders to category k;
    #  Scott's PI:
    #   1/4*(i**2)*sum_over_k( (n_k)**2 )
    all_items  = 0
    items_in_k = dict()
    for respB in allResponses:
        for respA in allResponses:
            all_items = all_items + table[respA][respB]
            if (respA not in items_in_k):
                items_in_k[respA] = 0
            if (respB not in items_in_k):
                items_in_k[respB] = 0
            if (table[respA][respB] > 0):
                items_in_k[respA] += table[respA][respB]
                items_in_k[respB] += table[respA][respB]
    # Find expected agreement:
    sum_of_proportions = 0.0
    for respA in allResponses:
        sum_of_proportions += items_in_k[respA]**2
    expected = sum_of_proportions / (4*(all_items**2))
    # Find observed agreement
    observed_agreements = [ table[resp][resp] for resp in allResponses ]
    observed = sum(observed_agreements) / all_items
    # Find Scott's PI
    if (1 - expected != 0):
        kappa = (observed - expected)/(1 - expected)
    else:
        kappa = -10.0
    return (kappa, observed, expected, table)


# ============================================================
#    Chance-corrected agreement measures
#      with special weighting schemes
# ============================================================

#  Implemented following the guide:  
#   Computing Krippendorff’s Alpha-Reliability 
#   http://www.asc.upenn.edu/usr/krippendorff/mwebreliability5.pdf
def find_Krippendorff_Alpha(table, allResponses, distanceMetric):
    #
    # 1) Create a coincidence matrix from the confusion matrix
    #  Basically, the units are entered twice: e.g (A, B) is 
    #  entered once as A-B pairs and once as B-A pairs;
    coincidence = dict()
    for respA in allResponses:
        for respB in allResponses:
            sum = table[respA][respB] + table[respB][respA]
            if (respA not in coincidence):
                coincidence[respA] = dict()
            coincidence[respA][respB] = sum
            if (respB not in coincidence):
                coincidence[respB] = dict()
            coincidence[respB][respA] = sum
    #for k in sorted(coincidence.keys()):
    #    print (k, str([(k1,coincidence[k][k1]) for k1 in sorted(coincidence[k].keys())]) )
    #
    # 2) Collect frequencies of each category + total frequency
    categoryItems = dict()
    totalFreq = 0
    for respA in allResponses:
        for respB in allResponses:
            if (respA not in categoryItems):
                categoryItems[respA] = 0
            if (respB not in categoryItems):
                categoryItems[respB] = 0
            if (table[respA][respB] > 0):
                categoryItems[respA] += table[respA][respB]
                categoryItems[respB] += table[respA][respB]
                totalFreq += 2*table[respA][respB]
    #for k in sorted(categoryItems.keys()):
    #    print (k, categoryItems[k])
    #print(totalFreq)
    #
    # 3) Compute alpha-reliability
    sortedKeys = sorted(allResponses.keys())
    sum_o_ck = 0.0
    for i in range(len(sortedKeys)):
        c = sortedKeys[i]
        for j in range(i+1, len(sortedKeys)):
            k = sortedKeys[j]
            sum_o_ck += coincidence[c][k]*distanceMetric(c, k)
    sum_n_ck = 0.0
    for i in range(len(sortedKeys)):
        c = sortedKeys[i]
        for j in range(i+1, len(sortedKeys)):
            k = sortedKeys[j]
            sum_n_ck += categoryItems[c]*categoryItems[k]*distanceMetric(c, k)
    if (sum_n_ck > 0.0 or sum_n_ck < 0.0):
        alpha = 1.0 - ((float(totalFreq) - 1.0)*(sum_o_ck/sum_n_ck))
    else:
        alpha = -100.0
    return (alpha, coincidence)

# ============================================================
#    Distance metrics for the Krippendorff's Alpha
# ============================================================

def default_distance(valueA, valueB):
    if (valueA == valueB):
        return 0.0
    else:
        return 1.0

def TLINK_distance(valueA, valueB):
    overlapRels = re.compile("^\s*(SIMULTANEOUS|INCLUDES|IS_INCLUDED|IDENTITY)\s*$")
    beforeRels  = re.compile("^\s*(BEFORE-OR-OVERLAP|BEFORE)\s*$")
    afterRels   = re.compile("^\s*(OVERLAP-OR-AFTER|AFTER)\s*$")
    befOvrRels  = re.compile("^\s*(BEFORE-OR-OVERLAP|SIMULTANEOUS|INCLUDES|IS_INCLUDED|IDENTITY)\s*$")
    aftOvrRels  = re.compile("^\s*(OVERLAP-OR-AFTER|SIMULTANEOUS|INCLUDES|IS_INCLUDED|IDENTITY)\s*$")
    if (valueA == valueB):
        return 0.0
    elif (overlapRels.match(valueA) and \
          overlapRels.match(valueB)):
        return 0.5
    elif (beforeRels.match(valueA) and \
          beforeRels.match(valueB)):
        return 0.5
    elif (afterRels.match(valueA) and \
          afterRels.match(valueB)):
        return 0.5
    elif (befOvrRels.match(valueA) and \
          befOvrRels.match(valueB)):
        return 0.5
    elif (aftOvrRels.match(valueA) and \
          aftOvrRels.match(valueB)):
        return 0.5
    else:
        return 1.0
