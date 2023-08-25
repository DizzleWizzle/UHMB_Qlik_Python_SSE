# UHMB Qlik Python SSE
Built from the column operations example in the Qlik official github https://github.com/qlik-oss/server-side-extension/tree/master/examples/python 

Currently 3 functions:
* PorterStem 
    *  does Porter's Stemming Algorithm from the NLTK package against the words passed to it (currently single word only)

* Lemma 
    * currently broken

* XMR_Row(<return value>,<x value>,<y value>,<grouping>) 
    * return value one of the following
      * UCL - value of the Upper control limit line
      * LCL - value of the Lower control limit line
      * AVG - value of the mean line
      * MR - value of the Moving Range
      * highlight - either 1 (highlighted on an upward rule) -1 (highlighted on a downward rule) 0 no highlight 
    * x value (what is on the x axis - usually a date)
    * y value (the measure)
    * grouping (if there are recalculation periods used this to define them, if no recalculation just put a constant in there like 'test')
