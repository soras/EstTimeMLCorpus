# -*- coding: utf-8 -*- 
#
#    Executes EVENT filtering experiments using the Python's 
#   script "find_combined_annotation_agreements.py" and outputs
#   results to the file 'outputFile';
#
#    After all the experiments are done, gathers the compact part
#   of the results and prints to stdin;
#
#    Requires that python3 binary is accessible via command line.
#   If the python3 is in custom location, the path-to-python3
#   should be set in variable 'pythonLoc';
#
#    Developed and tested under Python's version: 3.4.1
#

import sys, os, re


browseOldExperiments = False  # Whether experiments should be skipped and only existing results should be browsed
pythonLoc  = "python"         # Put here path-to-the-python3-binary, if it is not accessible from the command line
outputFile = "filtering_exp_results_event.txt"  # File where all the results shall be written

#
#   All models (used in different experiments)
# 
experiments = [ ["0a", "a. Ilma filtreerimiseta;"],

                ["1a", "a. Ainult verbid;"],
                ["1b", "b. Verbid + nimisõnad;"],
                ["1c", "c. Verbid + omadussõnad;"],
                ["1d", "d. Verbid + nimisõnad + omadussõnad;"],
                
                ["2a", "a. kuulub ainult predikaati;"],
                ["2b", "b. a + on predikaati kuuluva sõna otsene alam ja verb;"],
                ["2c", "c. a + on predikaati kuuluva sõna otsene alam ja mitteverb;"],
                ["2d", "d. a + pole predikaati kuuluva sõna otsene alam;"],
                
                ["2*a", "a. kuulub ainult predikaati;"],
                ["2*b", "b. a + on predikaati kuuluva sõna otsene alam: OBJ ja verb;"],
                ["2*c", "c. a + on predikaati kuuluva sõna otsene alam: OBJ ja mitteverb;"],
                ["2*d", "d. a + on predikaati kuuluva sõna otsene alam: SUBJ ja verb;"],
                ["2*e", "e. a + on predikaati kuuluva sõna otsene alam: SUBJ ja mitteverb;"],
                ["2*f", "f. a + on predikaati kuuluva sõna otsene alam: ADVL ja verb;"],
                ["2*g", "g. a + on predikaati kuuluva sõna otsene alam: ADVL ja mitteverb;"],

                ["5a", "a. ilma eituse ja modaalsuseta predikaadid;"],
                ["5b", "b. a + modaalsusega predikaadid;"],
                ["5c", "c. a + eitusega predikaadid;"],
                ["5d", "d. a + eituse ja modaalsusega predikaadid;"],
                
                ["6*a", "a) REPORTING syndmus ja selle vahetud alluvad"],
                ["6*b", "b) I_ACTION syndmus ja selle vahetud alluvad"],
                ["6*c", "c) I_STATE syndmus ja selle vahetud alluvad"],
                ["6*d", "d) ASPECTUAL syndmus ja selle vahetud alluvad"],
                ["6*e", "e) PERCEPTION syndmus ja selle vahetud alluvad"],
                ["6*f", "f) MODAL syndmus ja selle vahetud alluvad"],
                ["6*g", "g) OCCURRENCE ja selle vahetud alluvad"],
                ["6*h", "h) STATE ja selle vahetud alluvad"],
                ["6*i", "i) syndmus ei kuulu yhessegi argumentstruktuuri"],
                ]

#
#   Models reported in (Orasmaa 2014)
# 
experiments = [ ["0a", "a. Ilma filtreerimiseta;"],

                ["1a", "a. Ainult verbid;"],
                ["1b", "b. Verbid + nimisõnad;"],
                ["1c", "c. Verbid + omadussõnad;"],
                ["1d", "d. Verbid + nimisõnad + omadussõnad;"],
                
                ["2a", "a. kuulub ainult predikaati;"],
                ["2b", "b. a + on predikaati kuuluva sõna otsene alam ja verb;"],
                ["2c", "c. a + on predikaati kuuluva sõna otsene alam ja mitteverb;"],
                ["2d", "d. a + pole predikaati kuuluva sõna otsene alam;"]
              ]

# Fetches text snippets containing specific keywords from the file content (lines);
# Groups the snippets by filtering methods;
def filterFileAndPrintSpecificSnippets(lines, experiments, snippetKey):
    i = 0
    currentExp = ""
    outString  = ""
    anyMatchFound = False
    while (i < len(lines)):
        rida = lines[i].rstrip()
        filterKeyMatch = re.match("^\s*Using\s+the\s+filtering\s+method:\s+(\S+)\s*$", rida)
        if (filterKeyMatch):
            currentExp = filterKeyMatch.group(1)
            outString += "\n"
            for [expID, description] in experiments:
                if (expID == currentExp):
                    outString += " "*7+""+currentExp+"  "+description+"\n"
                    break
        snippetMatchTLINK = re.match("^\s+"+snippetKey+".+$", rida)
        if (snippetMatchTLINK):
            anyMatchFound = True
            outString += rida+"\n"
        i += 1
    if (anyMatchFound):
        print (outString)


if len(sys.argv) > 1 and os.path.isdir(sys.argv[1]):
    corpusDir = sys.argv[1]
    # Whether we should execute new experiments
    if (not browseOldExperiments):
        # Remove old results file
        if (os.path.exists(outputFile)):
            print (" Removing "+outputFile+" ...")
            os.unlink(outputFile)

        # Execute experiments one by one
        for [expID, description] in experiments:
            command = pythonLoc+" "+"find_combined_annotation_agreements.py"+" "+corpusDir+" "+expID+" >> "+outputFile
            print (" ::: "+command+" ...")
            os.system(command)
            
    if (not os.path.exists(outputFile)):
        raise Exception(" Results file "+outputFile+" not found ...")
    resultLines = []
    with open(outputFile, 'r', encoding="utf-8") as f:
        resultLines = f.readlines()
    print ()
    print (("="*30))
    print ("  EVENT annotation results ")
    print (("="*30))
    filterFileAndPrintSpecificSnippets(resultLines, experiments, "all-in-one-EVENT")
    print ()
else:
    print(" Please give argument: <corpus_dir> ")
    print(" Example:\n     python  "+sys.argv[0]+"  corpus ")
