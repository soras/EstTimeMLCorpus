==============================================
  The Inter-Annotator Agreement Experiments
==============================================

  This folder contains tools for performing inter-annotator agreements experiments 
 on the corpus. These experiments were first reported in (Orasmaa, 2014a) and 
 (Orasmaa, 2014b).
 
  (!) Note that experimental data and tools here are different than the 
      data and tools used in the forementioned publications, so the results
      obtained on this data are also slightly different than the results in 
      the publications.
      
      The initial version of the corpus (reported in publications) consisted 
      of annotated text files (containing morphological, syntactic, EVENT, 
      and TIMEX annotations), and BAT (Brandeis Annotation Tool, 
      http://batcaves.org/bat/tool/ ) export files (containing TLINK 
      annotations). Because processing these formats together required a rather 
      complex procedure for aligning annotations (which made the whole process 
      rather error-prone), a decision was made to homogenize the format of the 
      corpus, resulting in the current corpus. The tools were also rewritten
      and adjusted for processing the new version.
      The differences in results are due to removed & corrected annotations, 
      and due to updates in the tools.

 A) EVENT and TIMEX inter-annotator agreements on extent and attributes 
    (Orasmaa, 2014a) can be calculated with the script 
    "find_entity_annotation_agreements.py":
    
        python  find_entity_annotation_agreements.py  ..\corpus
   
    The script outputs agreements on each file, and at the end, outputs 
    aggregated agreements over the whole corpus;
    
 B) EVENT inter-annotator agreements obtained while filtering EVENTs by
    linguistic (morphological, syntactic) constraints (Orasmaa, 2014a) 
    can be calculated with the script "execute_filtering_IAA_experiments_event.py":
    
        python  execute_filtering_IAA_experiments_event.py  ..\corpus

    The script reports a concise result row for each experiment:
      all-in-one-EVENT   eventCount (eventCount%) tlinkCount (tlinkCount%) 
                                      | eventExtentF1  eventExtent+ClassF1
    
     Note: tlinkCount reports count of all tlinks annotated by annotators
     a, b and c, including tlinks that were annotated only by a single 
     annotator, and not supported by others;
    
 C) TLINK inter-annotator agreements obtained while filtering EVENTs by
    linguistic (morphological, syntactic) constraints (Orasmaa, 2014b) can 
    be calculated with the script "execute_filtering_IAA_experiments_tlink.py":

        python  execute_filtering_IAA_experiments_tlink.py  ..\corpus
     
     Note: tlink counts reported in "TLINK relType assignments in pairs"
     are obtained while counting relations (pairs of entities) that were
     annotated by at least two annotators, so the numbers are different
     compared to tlinkCount-s in B;

 D) The script "find_combined_annotation_agreements.py" can be used to 
    execute a single experiment, alternatively to executing sets of 
    experiments in B and C; 
    E.g. Experiment '2a' (keep only EVENTs that are part of the predicate 
    of a clause) can be executed with the following command:
    
        python  find_combined_annotation_agreements.py  ..\corpus  2a
    
     Note: experiment labels can be different than model names reported
     in the publications.


==============================
  Related publications
==============================

 *) S.Orasmaa (2014a). Towards an Integration of Syntactic and Temporal 
    Annotations in Estonian. In Proceedings of the Ninth International Conference 
    on Language Resources and Evaluation (LREC'14).

 *) S.Orasmaa (2014b). How Availability of Explicit Temporal Cues Affects 
    Manual Temporal Relation Annotation. Human Language Technologies - The Baltic 
    Perspective (215 - 218). IOS Press.
