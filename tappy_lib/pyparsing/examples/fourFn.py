# fourFn.py
#
# Demonstration of the parsing module, implementing a simple 4-function expression parser,
# with support for scientific notation, and symbols for e and pi.
# Extended to add exponentiation and simple built-in functions.
#
# Copyright 2003, by Paul McGuire
#
from pyparsing import Literal,CaselessLiteral,Word,Combine,Group,Optional,ZeroOrMore,Forward,nums,alphas
import math

exprStack = []

def pushFirst( str, loc, toks ):
    global exprStack
    if toks: 
        exprStack.append( toks[0] )
    return toks

bnf = None
def BNF():
    global bnf
    if not bnf:
        point = Literal( "." )
        e     = CaselessLiteral( "E" )
        fnumber = Combine( Word( "+-"+nums, nums ) + 
                           Optional( point + Optional( Word( nums ) ) ) +
                           Optional( e + Word( "+-"+nums, nums ) ) )
        ident = Word(alphas, alphas+nums+"_$")
     
        plus  = Literal( "+" )
        minus = Literal( "-" )
        mult  = Literal( "*" )
        div   = Literal( "/" )
        lpar  = Literal( "(" ).suppress()
        rpar  = Literal( ")" ).suppress()
        addop  = plus | minus
        multop = mult | div
        expop = Literal( "^" )
        pi    = CaselessLiteral( "PI" )
        
        expr = Forward()
        atom = ( pi | e | fnumber | ident + lpar + expr + rpar ).setParseAction( pushFirst ) | ( lpar + expr.suppress() + rpar )
        
        # by defining exponentiation as "atom [ ^ factor ]..." instead of "atom [ ^ atom ]...", we get right-to-left exponents, instead of left-to-righ
        # that is, 2^3^2 = 2^(3^2), not (2^3)^2.
        factor = Forward()
        factor << atom + ZeroOrMore( ( expop + factor ).setParseAction( pushFirst ) )
        
        term = factor + ZeroOrMore( ( multop + factor ).setParseAction( pushFirst ) )
        expr << term + ZeroOrMore( ( addop + term ).setParseAction( pushFirst ) )
        bnf = expr
    return bnf

# map operator symbols to corresponding arithmetic operations
opn = { "+" : ( lambda a,b: a + b ),
        "-" : ( lambda a,b: a - b ),
        "*" : ( lambda a,b: a * b ),
        "/" : ( lambda a,b: a / b ),
        "^" : ( lambda a,b: a ** b ) }
fn  = { "sin" : math.sin,
        "cos" : math.cos,
        "tan" : math.tan,
        "abs" : abs,
        "trunc" : ( lambda a: int(a) ),
        "round" : ( lambda a: int(a+0.5) ),
        "sgn" : ( lambda a: ( (a<0 and -1) or (a>0 and 1) or 0 ) ) }
def evaluateStack( s ):
    op = s.pop()
    if op in "+-*/^":
        op2 = evaluateStack( s )
        op1 = evaluateStack( s )
        return opn[op]( op1, op2 )
    elif op == "PI":
        return 3.1415926535
    elif op == "E":
        return 2.718281828
    elif op[0].isalpha():
        fnarg = evaluateStack( s )
        return (fn[op])( fnarg )
    else:
        return float( op )

if __name__ == "__main__":
  
    def test( str ):
        global exprStack
        exprStack = []
        results = BNF().parseString( str )
        print str, "->", results, "=>", exprStack, "=", evaluateStack( exprStack )
  
    test( "9" )
    test( "9 + 3 + 6" )
    test( "9 + 3 / 11" )
    test( "(9 + 3)" )
    test( "(9+3) / 11" )
    test( "9 - 12 - 6" )
    test( "9 - (12 - 6)" )
    test( "2*3.14159" )
    test( "3.1415926535*3.1415926535 / 10" )
    test( "PI * PI / 10" )
    test( "PI*PI/10" )
    test( "PI^2" )
    test( "6.02E23 * 8.048" )
    test( "e / 3" )
    test( "sin(PI/2)" )
    test( "trunc(E)" )
    test( "E^PI" )
    test( "2^3^2" )
    test( "2^3+2" )
    test( "2^9" )
    test( "sgn(-2)" )
    test( "sgn(0)" )
    test( "sgn(0.1)" )


"""
Test output:
>pythonw -u fourFn.py
9 -> ['9'] => ['9'] = 9.0
9 + 3 + 6 -> ['9', '+', '3', '+', '6'] => ['9', '3', '6', '+', '+'] = 18.0
9 + 3 / 11 -> ['9', '+', '3', '/', '11'] => ['9', '3', '11', '/', '+'] = 9.27272727273
(9 + 3) -> [] => ['9', '3', '+'] = 12.0
(9+3) / 11 -> ['/', '11'] => ['9', '3', '+', '11', '/'] = 1.09090909091
9 - (12 - 6) -> ['9', '-'] => ['9', '12', '6', '-', '-'] = 3.0
2*3.14159 -> ['2', '*', '3.14159'] => ['2', '3.14159', '*'] = 6.28318
3.1415926535*3.1415926535 / 10 -> ['3.1415926535', '*', '3.1415926535', '/', '10'] => ['3.1415926535', '3.1415926535', '10', '/', '*'] = 0.986960440053
PI * PI / 10 -> ['PI', '*', 'PI', '/', '10'] => ['PI', 'PI', '10', '/', '*'] = 0.986960440053
PI*PI/10 -> ['PI', '*', 'PI', '/', '10'] => ['PI', 'PI', '10', '/', '*'] = 0.986960440053
PI^2 -> ['PI', '^', '2'] => ['PI', '2', '^'] = 9.86960440053
6.02E23 * 8.048 -> ['6.02E23', '*', '8.048'] => ['6.02E23', '8.048', '*'] = 4.844896e+024
e / 3 -> ['E', '/', '3'] => ['E', '3', '/'] = 0.906093942667
sin(PI/2) -> ['sin', 'PI', '/', '2'] => ['PI', '2', '/', 'sin'] = 1.0
trunc(E) -> ['trunc', 'E'] => ['E', 'trunc'] = 2
E^PI -> ['E', '^', 'PI'] => ['E', 'PI', '^'] = 23.1406926184
1/7 -> ['1', '/', '7'] => ['1', '7', '/'] = 0.142857142857
2^3^2 -> ['2', '^', '3', '^', '2'] => ['2', '3', '2', '^', '^'] = 512.0
2^9 -> ['2', '^', '9'] => ['2', '9', '^'] = 512.0
sgn(-2) -> ['sgn', '-2'] => ['-2', 'sgn'] = -1
sgn(0) -> ['sgn', '0'] => ['0', 'sgn'] = 0
sgn(0.1) -> ['sgn', '0.1'] => ['0.1', 'sgn'] = 1
>Exit code: 0
"""