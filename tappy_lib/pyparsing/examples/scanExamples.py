#
# scanExamples.py
#
#  Illustration of using pyparsing's scanString and transformString methods
#
# Copyright (c) 2004, Paul McGuire
#
from pyparsing import Word, alphas, alphanums, Literal, restOfLine, OneOrMore, Empty

# simulate some C++ code
testData = """
#define MAX_LOCS=100
#define USERNAME = "floyd"
#define PASSWORD = "swordfish"

a = MAX_LOCS;

A::assignA( a );
A2::A1::printA( a );

CORBA::initORB("xyzzy", USERNAME, PASSWORD );

"""

#################
print "Example of an extractor"
print "----------------------"

# simple grammar to match #define's
ident = Word(alphas, alphanums+"_")
macroDef = Literal("#define") + ident.setResultsName("name") + "=" + restOfLine.setResultsName("value")
for t,s,e in macroDef.scanString( testData ):
    print t.name,":", t.value
    
# or a quick way to make a dictionary of the names and values (need to suppress output of all tokens, other than the name and the value)
macroDef = Literal("#define").suppress() + ident + Literal("=").suppress() + Empty() + restOfLine
macros = dict([t for t,s,e in macroDef.scanString(testData)])
print "macros =", macros
print


#################
print "Examples of a transformer"
print "----------------------"

# convert C++ namespaces to mangled C-compatible names
scopedIdent = ident + OneOrMore( Literal("::").suppress() + ident )
scopedIdent.setParseAction(lambda s,l,t: "_".join(t))

print "(replace namespace-scoped names with C-compatible names)"
print scopedIdent.transformString( testData )
    
    
# or a crude pre-processor (use parse actions to replace matching text)
def substituteMacro(s,l,t):
    if t[0] in macros:
        return macros[t[0]]
ident.setParseAction( substituteMacro )
ident.ignore(macroDef)

print "(simulate #define pre-processor)"
print ident.transformString( testData )



#################
print "Example of a stripper"
print "----------------------"

from pyparsing import dblQuotedString, LineStart

# remove all string macro definitions (after extracting to a string resource table?)
ident.setParseAction( None )
stringMacroDef = Literal("#define") + ident + "=" + dblQuotedString + LineStart()
stringMacroDef.setParseAction( lambda s,l,t: [] )

print stringMacroDef.transformString( testData )
