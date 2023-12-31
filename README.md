# UHMB Qlik Python SSE
Built from the column operations example in the Qlik official github https://github.com/qlik-oss/server-side-extension/tree/master/examples/python 

Currently 6 functions:

Scalar functions (can use in front end, one call per row)
* PorterStem 
    *  does Porter's Stemming Algorithm from the NLTK package against the words passed to it (currently single word only)

* Lemma 
    * does a bad attempt at lemmatizing with hard coded v POS tags - probably dont use

* XMR_Row(\<return value\>,\<x value\>,\<y value\>,\<grouping\>) 
    * return value one of the following
      * UCL - value of the Upper control limit line
      * LCL - value of the Lower control limit line
      * AVG - value of the mean line
      * MR - value of the Moving Range
      * highlight - either 1 (highlighted on an upward rule) -1 (highlighted on a downward rule) 0 no highlight 
    * x value (what is on the x axis - usually a date)
    * y value (the measure)
    * grouping (if there are recalculation periods used this to define them, if no recalculation just put a constant in there like 'test')
      * Qlik Combochart where expressions just use 'test' in the final parameter - i.e UHMBSSE.XMR_Row('UCL',WeekStart,Sum(Expression1),'TEST')
        * ![NoGrouping](https://github.com/DizzleWizzle/UHMB_Qlik_Python_SSE/assets/111445780/813e9320-594a-4915-ac65-e677dc58c707)
      * Qlik Combochart where expressions recalculate on each calendar year - i.e UHMBSSE.XMR_Row('UCL',WeekStart,Sum(Expression1),year(WeekStart))
        *![Grouping](https://github.com/DizzleWizzle/UHMB_Qlik_Python_SSE/assets/111445780/80ba0680-107f-4c1b-9baf-62a85fdef228)

Tensor functions (use the Load ... Extension syntax in the load script, one call per table)

* XMR_Table(\<x value\>,\<grouping\>,\<y value\>)
   * x value (what is on the x axis - usually a date)
   * y value (the measure)
   * grouping (if there are recalculation periods used this to define them, if no recalculation just put a constant in there like 'test')
   * Returns a table with the following columns:
      * Dimension - x value
      * Measure - Y value
      * UCL
      * LCL
      * MR
      * Mean
      * highlight (either -1,0,1 depending if an XMR rules is triggered and if its increasing or decreasing)

* PorterStem_Table(Word)
   * Returns a table with the following columns:
      *  Original - the Word value passed to it
      *  Stemmed - the Stem of the word
    
* Rev_PorterStem_Table()
   * Returns a table with all the distinct words in the nltk brown corpus with their stem (over 40k words) in lower case:
      *  Original - the Word value passed to it
      *  Stemmed - the Stem of the word  


Setup:
Follow the guide in the linked Qlik SSE (would strongly suggest getting their examples working first).

I also used NSSM and followed this guide (https://www.mssqltips.com/sqlservertip/7325/how-to-run-a-python-script-windows-service-nssm/) to have it running on a seperate server as a service.