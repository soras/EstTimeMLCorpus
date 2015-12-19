# -*- coding: utf-8 -*- 
#
#    Executes TLINK filtering experiments using the Python's 
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
outputFile = "filtering_exp_results_tlink.txt"  # File where all the results shall be written

#  ===================================================
#    TLINK models with intersecting layers
#  ===================================================
experiments = [ ["2a", "0. kuulub ainult predikaati (baasjuht)"],

                ["3a", "a. ainult lihtminevik"],
                ["3b", "b. lihtminevik + enneminevik"],
                ["3c", "c. lihtminevik + taisminevik"],
                ["3d", "d. lihtminevik + taisminevik + enneminevik"],
                ["3e", "e. lihtminevik + taisminevik + enneminevik + olevik"],
                
                ["4a", "a. predikaati kuuluvad sündmused, millele alluvad ajaväljendid;"],
                ["4c", "c. kõik predikaati kuuluvad sündmused;"],
              ]
              
#  ===================================================
#    TLINK models with non-intersecting layers,
#  ===================================================
experiments = [ ["2a", "0. kuulub ainult predikaati (baasjuht)"],

                ["3a", 'a. ainult lihtminevik'],
                ["3m", 'b. ainult enneminevik'],
                ["3n", 'c. ainult t2isminevik'],
                ["3l", 'd. ainult olevik'],
                
                ["4a", "a. predikaati kuuluvad sündmused, millele alluvad ajaväljendid;"],
                ["4b", "b. predikaati kuuluvad sündmused, millele EI allu ykski ajaväljend;"],
                ]
                
#  ===================================================
#    TLINK models with non-intersecting layers,
#      reported in (Orasmaa, 2014))
#  ===================================================
experiments = [ ["2a", "0. kuulub ainult predikaati (baasjuht)"],

                ["3a", 'a. ainult lihtminevik'],
                ["3l", 'd. ainult olevik'],
                
                ["4a", "a. predikaati kuuluvad sündmused, millele alluvad ajaväljendid;"],
                ["4b", "b. predikaati kuuluvad sündmused, millele EI allu ykski ajaväljend;"],
                ]

                
#  ===================================================
#    TLINK models with non-intersecting layers,
#      reported in thesis)
#  ===================================================
experiments = [ ["0a", "00. Ilma filtreerimiseta;"],

                ["2a", "0. kuulub ainult predikaati (baasjuht)"],

                ["3a", 'a. ainult lihtminevik'],
                ["3l", 'd. ainult olevik'],
                
                ["4a", "a. predikaati kuuluvad sündmused, millele alluvad ajaväljendid;"],
                ["4b", "b. predikaati kuuluvad sündmused, millele EI allu ykski ajaväljend;"],
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
    print (("="*30))
    print ("  TLINK find members agreements (F1-Scores) ")
    print (("="*30))
    filterFileAndPrintSpecificSnippets(resultLines, experiments, "find-TLINK-F1scores")
    print ()

    print (("="*30))
    print ("  TLINK relType assignments in pairs ")
    print (("="*30))
    filterFileAndPrintSpecificSnippets(resultLines, experiments, "counts-for-TLINK-base")
    print ()
    
    print (("="*30))
    print ("  TLINK relType agreement results (Accuracies) ")
    print (("="*30))
    filterFileAndPrintSpecificSnippets(resultLines, experiments, "short-accs-for-TLINK-base")
    print ()

    print (("="*30))
    print ("  TLINK relType agreement results (Chance corrected) ")
    print (("="*30))
    filterFileAndPrintSpecificSnippets(resultLines, experiments, "short-CCs-for-TLINK-base")
    print ()

    print (("="*30))
    print ("  TLINK relType agreement results (VAGUE relations) ")
    print (("="*30))
    filterFileAndPrintSpecificSnippets(resultLines, experiments, "tlink-vague-relations")
    print ()
    
else:
    print(" Please give argument: <corpus_dir> ")
    print(" Example:\n     python  "+sys.argv[0]+"  corpus ")
