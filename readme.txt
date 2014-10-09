==========================================
==========================================
   Estonian TimeML Annotated Corpus   
==========================================
==========================================

  This corpus consists of 80 Estonian newspaper articles (approx. 22,000 
 word tokens) with manually corrected morphological and dependency 
 syntactic annotations, and with manually added temporal semantic 
 annotations. This corpus is a subcorpus of Dependency Treebank of Estonian
 ( http://www.cl.ut.ee/korpused/soltuvuskorpus/ ).

  Dependency syntactic annotations are based on manually corrected output 
 of syntactic analyser of Estonian (more detailed Estonian descriptions
 can be found from  http://lepo.it.da.ut.ee/~kaili/Syntax/pindsyntax.html ).
 The syntactic analyser of Estonian is based on Constraint Grammar (CG) 
 formalism and its latest version uses VISL CG-3 format and software 
 ( http://beta.visl.sdu.dk/ ).

  Temporal annotations are based on an adaption of the TimeML specification
 ( http://www.timeml.org/ ), and currently consist of EVENT, TIMEX and 
 TLINK annotations. Annotation of TLINKs was separated into 4 layers: 
  1) Relations between EVENTs and TIMEXes (TLINK-event-timex);
  2) Relations between EVENTs and document creation time (TLINK-event-DCT);
  3) Relations between main EVENTs of two consecutive sentences (TLINK-main-events);
  4) Relations between EVENTs in the same sentence (TLINK-event-event);

  Following TLINK relation types are used: BEFORE, BEFORE-OR-OVERLAP,
 SIMULTANEOUS, IS_INCLUDED, INCLUDES, OVERLAP-OR-AFTER, AFTER, IDENTITY, 
 VAGUE. 

  In addition to final TLINK annotations, the corpus also contains initial TLINK 
 annotations provided by three different annotators (A, B, C). Each file was 
 initially annotated by two annotators and the final decision on the relations
 was made by a judge;

  The creation process of the corpus, along with the evaluation of consistency 
 of annotation is described in (Orasmaa, 2014a) and (Orasmaa, 2014b).

==============================
  Accessing/Exploring corpus
==============================

  As the temporal annotation is a complex, multi-layered annotation, it is 
 difficult to explore it manually, just by browsing the annotation files. In 
 order to get full access to all different annotations, some programming skills 
 are currently required. 
  An example of how the corpus can be accessed programmatically is in the 
 Python script "exported_corpus_reader.py". The script can be executed from
 command line in following way:

    python  exported_corpus_reader.py  PATH/TO/CORPUS/FOLDER

  The script loads data from different annotation layers, prints out corpus content 
 sentence by sentence, and lists temporal annotations (EVENT and TIMEX phrases, 
 TLINK relations) for each sentence. Note that only final TLINK annotations 
 (relations corrected by the judge) are printed out, and much of the information 
 available in the corpus is not printed (TLINK annotations provided by 3 annotators, 
 EVENT/TIMEX attributes, morphological and syntactic annotations).

  An example of the script's output can be found in the text file 
 "corpus_tlinks_YYYY-MM-DD.txt" (where YYYY-MM-DD corresponds to the date when the
 file was automatically generated);
 
==============================
  Structure of the corpus
==============================

  The corpus format is inspired by the format used in Brandeis Annotation Tool ( 
 http://batcaves.org/bat/tool/ ): the corpus can be roughly divided into base 
 segmentation, entity annotations, and relation annotations. But there are also notable 
 differences, e.g. base segmentation includes morphological and dependency syntactic 
 annotations, and entity annotations include entity attributes.
  Annotation files can be found from the directory "corpus". In following, corpus files 
 and their format are described in more detail.

 
   article-metadata

        Contains metadata for each article (source, author, title etc).
       The metadata has been extracted from Estonian Reference Corpus. 
       Initially, the metadata was extracted by automatic web crawling 
       methods, so there are gaps in the information (missing authors 
       etc.);

   base-segmentation-morph-syntax

        Contains base segmentation (how the corpus is split into files, 
       sentences, and tokens), morphological and syntactic annotations
       provided for each token, and dependency syntactic relations 
       associated with each token. Values are TAB-separated.
       
        Base segmentation provides ID for each sentence in a file, and
       ID for each token in a sentence (numbered sequentially, starting
       from 0).
        Morphological and syntactic annotations are based on the format
       used by syntactic analyser of Estonian, descriptions of the
       tags (in Estonian) can be found from following URLs:
         * morphological tags:
              http://math.ut.ee/~kaili/thesis/pt3_2.html
         * syntactical tags:  
              http://math.ut.ee/~kaili/thesis/pt3_4.html
        Dependency syntactic relations are described by numeric values 
       syntactic_ID  and  syntactic_ID_of_head in following manner:
         * syntactic_ID = label of current token in syntactic tree;
         * syntactic_ID_of_head = label of the parent of current token
           in syntactic tree; 
              - if this value is 0, the current token is the root of the 
                syntactic tree;
              - punctuation is not included in syntactic tree, so in
                case of punctuation, this value is equal to syntactic_ID;
        One syntactic tree mostly corresponds to one sentence; however,
       sometimes there are also multiple syntactic trees in one sentence;

   event-annotation

        Contains pointer to event mention's location in base segmentation 
       (in which file, in which sentence and in which token), the 
       expression corresponding to the event mention, TimeML attributes
       of the event, and event ID. Values are TAB-separated.

        The annotation can be part of a multiword annotation, in this 
       case, value multiword="true" is added to the list of attributes;
        TimeML attributes listed for annotated token are class (one of
       the following: REPORTING, PERCEPTION, I_ACTION, I_STATE, ASPECTUAL,
       MODAL, STATE, OCCURRENCE), modality, polarity, and comment. 
       Only attribute class is mandatory.
       In case of multiword annotation, attributes are listed only for the 
       syntactically dominating token (usually for a verb).

        Event ID is unique within the file/document, and multiword units
       are, naturally, sharing the same ID;

   timex-annotation
   
        Contains pointer to temporal expression's location in base 
       segmentation (in which file, in which sentence and in which token), 
       the string of temporal expression, TimeML attributes of the timex, 
       and ID of the timex. Values are TAB-separated.

        The annotation can be part of a multiword annotation, in this 
       case, value multiword="true" is added to the list of attributes;
        The annotation can also cover only a substring of some token,
       this is indicated by adding tokenSubstring="true";
        TimeML attributes listed for annotated token are type (DATE, TIME,
       SET, or DURATION), value, mod, quant, functionInDocument, and comment.
       Attributes type and value are mandatory.
       In case of multiword annotation, attributes are listed only for the 
       first token of the expression.

        Timex ID is unique within the file/document, and multiword units
       are, naturally, sharing the same ID;

   timex-annotation-dct

        Contains DCT (document creation time) for each file (article). DCT 
       is given as a date value.

   tlink-event-timex

         Contains temporal relations between events and temporal expressions
        (timexes). Both events and timexes are given by their IDs (which are
        unique with-in one document).
         In case of problematic/disputable relations, the comment field is also
        filled (in Estonian).

   tlink-event-dct

         Contains temporal relations between event mentions and DCT (document
        creation time). Events are given by their IDs; DCT values can be found 
        from file 'timex-annotation-dct';

   tlink-main-events

         Contains temporal relations between main events of adjacent sentences
        (inter-sentential temporal relations);
         Events are given by their IDs;
         Main events are usually syntactically governing events, and there can
        be more than one main event selected for one sentence.

   tlink-subordinate-events

         Contains temporal relations within a sentence, between two events if
        one event syntactically dominates other (intra-sentential temporal 
        relations);
         Events are given by their IDs;

  Note: In case of TLINK annotations, the corpus contains both annotations 
 initially provided by 3 annotators (tlink-* files with endings .ann-a, .ann-b, 
 .ann-c), and annotations corrected/adjudicated by the judge (tlink-* files 
 without endings). Each article has been annotated by two annotators, and 
 corrected by the judge.

====================================
   Language-specific differences    
====================================
 
 TODO: Here, Estonian language-specific divergences from the original TimeML 
       specification will be listed
 
==============================
  Related publications
==============================

 The creation of this corpus and its first version is described in:

 *) S.Orasmaa (2014a). Towards an Integration of Syntactic and Temporal 
    Annotations in Estonian. In Proceedings of the Ninth International Conference 
    on Language Resources and Evaluation (LREC'14).

 *) S.Orasmaa (2014b). How Availability of Explicit Temporal Cues Affects 
    Manual Temporal Relation Annotation. Human Language Technologies – The Baltic 
    Perspective (215 - 218). IOS Press.

  Note that the corpus statistics discussed in these articles can be different 
 from the statistics obtained from the current version of the corpus. This is 
 because the format of the corpus has been transformed, and the transformation 
 included removing some of the errorous and redundant annotations.
  The initial version of the corpus consisted of annotated text files (containing
 morphological, syntactic, EVENT, and TIMEX annotations), and BAT (Brandeis Annotation 
 Tool, http://batcaves.org/bat/tool/ ) export files (containing TLINK annotations). 
 Because processing these formats together required a rather complex procedure for 
 aligning annotations, a decision was made to homogenize the format of the corpus, 
 resulting in this format.
  Please contact the author, if You wish to explore or use earlier versions of the 
 corpus.

