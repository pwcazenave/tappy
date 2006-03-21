# chemicalFormulas.py
#
# Copyright (c) 2003, Paul McGuire
#

from pyparsing import Word, Optional, OneOrMore, Group, ParseException

atomicWeight = {
    "O"  : 15.9994,
    "H"  : 1.00794,
    "Na" : 22.9897,
    "Cl" : 35.4527,
    "C"  : 12.0107
    }
    
def test( bnf, strg, fn=None ):
    try:
        print strg,"->", bnf.parseString( strg ),
    except ParseException, pe:
        print pe
    else:
        if fn != None:
            print fn( bnf.parseString( strg ) )
        else:
            print
    
caps = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
lowers = caps.lower()
digits = "0123456789"

element = Word( caps, lowers )
elementRef = Group( element + Optional( Word( digits ), default="1" ) )
formula = OneOrMore( elementRef )

fn = lambda x : "(" + str(sum( [ atomicWeight[elem]*int(qty) for elem,qty in x ] ) ) + ")"
test( formula, "H2O", fn )
test( formula, "C6H5OH", fn )
test( formula, "NaCl", fn )


element = Word( caps, lowers )
elementRef = Group( element.setResultsName("symbol") + \
                Optional( Word( digits ), default="1" ).setResultsName("qty") )
formula = OneOrMore( elementRef )

fn = lambda elemList : sum( [ atomicWeight[elem.symbol]*int(elem.qty) for elem in elemList ] )
test( formula, "H2O", fn )
test( formula, "C6H5OH", fn )
test( formula, "NaCl", fn )


# do the same thing with re's
import re

formula = "([A-Z][a-z]*[0-9]*)+"
formulaRE = re.compile( formula )

def test2( regex, strg, fn=None ):
    m = regex.findall(strg)
    ngroups = len(m)
    if ngroups > 0:
        for i in range(ngroups):
            print m[i]
    else:
        print "no match"
    print
    
fn = None
test2( formulaRE, "H2O", fn )
test2( formulaRE, "C6H5OH", fn )
test2( formulaRE, "NaCl", fn )
    


