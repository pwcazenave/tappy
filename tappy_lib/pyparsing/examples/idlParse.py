#
# idlparse.py
#
# an example of using the parsing module to be able to process a subset of the CORBA IDL grammar
#
# Copyright (c) 2003, Paul McGuire
#

from pyparsing import Literal, CaselessLiteral, Word, Upcase, OneOrMore, ZeroOrMore, \
        Forward, NotAny, delimitedList, oneOf, Group, Optional, Combine, alphas, nums, restOfLine, cStyleComment, \
        alphanums, printables, empty, quotedString, ParseException, ParseResults
import pprint

bnf = None
def CORBA_IDL_BNF():
    global bnf
    
    if not bnf:

        # punctuation
        colon  = Literal(":")
        lbrace = Literal("{")
        rbrace = Literal("}")
        lbrack = Literal("[")
        rbrack = Literal("]")
        lparen = Literal("(")
        rparen = Literal(")")
        equals = Literal("=")
        comma  = Literal(",")
        dot    = Literal(".")
        slash  = Literal("/")
        bslash = Literal("\\")
        star   = Literal("*")
        semi   = Literal(";")
        langle = Literal("<")
        rangle = Literal(">")
        
        # keywords
        any_       = Literal("any")
        attribute_ = Literal("attribute")
        boolean_   = Literal("boolean")
        case_      = Literal("case")
        char_      = Literal("char")
        const_     = Literal("const")
        context_   = Literal("context")
        default_   = Literal("default")
        double_    = Literal("double")
        enum_      = Literal("enum")
        exception_ = Literal("exception")
        false_     = Literal("FALSE")
        fixed_     = Literal("fixed")
        float_     = Literal("float")
        inout_     = Literal("inout")
        interface_ = Literal("interface")
        in_        = Literal("in")
        long_      = Literal("long")
        module_    = Literal("module")
        object_    = Literal("Object")
        octet_     = Literal("octet")
        oneway_    = Literal("oneway")
        out_       = Literal("out")
        raises_    = Literal("raises")
        readonly_  = Literal("readonly")
        sequence_  = Literal("sequence")
        short_     = Literal("short")
        string_    = Literal("string")
        struct_    = Literal("struct")
        switch_    = Literal("switch")
        true_      = Literal("TRUE")
        typedef_   = Literal("typedef")
        unsigned_  = Literal("unsigned")
        union_     = Literal("union")
        void_      = Literal("void")
        wchar_     = Literal("wchar")
        wstring_   = Literal("wstring")
        
        identifier = Word( alphas, alphanums + "_" ).setName("identifier")
        
        real = Combine( Word(nums+"+-", nums) + dot + Optional( Word(nums) ) 
                        + Optional( CaselessLiteral("E") + Word(nums+"+-",nums) ) )
        integer = ( Combine( CaselessLiteral("0x") + Word( nums+"abcdefABCDEF" ) ) |
                    Word( nums+"+-", nums ) ).setName("int")

        udTypeName = delimitedList( identifier, "::", combine=True ).setName("udType")
        # have to use longest match for type, in case a user-defined type name starts with a keyword type, like "stringSeq" or "longArray"
        typeName = ( any_ ^ boolean_ ^ char_ ^ double_ ^ fixed_ ^ 
                    float_ ^ long_ ^ octet_ ^ short_ ^ string_ ^ 
                    wchar_ ^ wstring_ ^ udTypeName ).setName("type")
        sequenceDef = Forward().setName("seq")
        sequenceDef << Group( sequence_ + langle + ( sequenceDef | typeName ) + rangle )
        typeDef = sequenceDef | ( typeName + Optional( lbrack + integer + rbrack ) )
        typedefDef = Group( typedef_ + typeDef + identifier + semi ).setName("typedef")

        moduleDef = Forward()
        constDef = Group( const_ + typeDef + identifier + equals + ( real | integer | quotedString ) + semi ) #| quotedString )
        exceptionItem = Group( typeDef + identifier + semi )
        exceptionDef = ( exception_ + identifier + lbrace + ZeroOrMore( exceptionItem ) + rbrace + semi )
        attributeDef = Optional( readonly_ ) + attribute_ + typeDef + identifier + semi
        paramlist = delimitedList( Group( ( inout_ | in_ | out_ ) + typeName + identifier ) ).setName( "paramlist" )
        operationDef = ( ( void_ ^ typeDef ) + identifier + lparen + Optional( paramlist ) + rparen + \
                        Optional( raises_ + lparen + Group( delimitedList( typeName ) ) + rparen ) + semi )
        interfaceItem = ( constDef | exceptionDef | attributeDef | operationDef )
        interfaceDef = Group( interface_ + identifier  + Optional( colon + delimitedList( typeName ) ) + lbrace + \
                        ZeroOrMore( interfaceItem ) + rbrace + semi ).setName("opnDef")
        moduleItem = ( interfaceDef | exceptionDef | constDef | typedefDef | moduleDef )
        moduleDef << module_ + identifier + lbrace + ZeroOrMore( moduleItem ) + rbrace + semi

        bnf = ( moduleDef | OneOrMore( moduleItem ) )
        
        singleLineComment = "//" + restOfLine
        bnf.ignore( singleLineComment )
        bnf.ignore( cStyleComment )
        
    return bnf


def test( strng ):
    print strng
    try:
        bnf = CORBA_IDL_BNF()
        tokens = bnf.parseString( strng )
        print "tokens = "
        pprint.pprint( tokens.asList() )
    except ParseException, err:
        print err.line
        print " "*(err.column-1) + "^"
        print err
    print
    
    
test(
    """
    /*
     * a block comment *
     */
    typedef string[10] tenStrings;
    typedef sequence<string> stringSeq;
    typedef sequence< sequence<string> > stringSeqSeq;
    
    interface QoSAdmin {
        stringSeq method1( in string arg1, inout long arg2 );
        stringSeqSeq method2( in string arg1, inout long arg2, inout long arg3);
        string method3();
      };
    """
    )
test(
    """
    /*
     * a block comment *
     */
    typedef string[10] tenStrings;
    typedef 
        /** ** *** **** *
         * a block comment *
         */
        sequence<string> stringSeq;
    /* */  /**/ /***/ /****/
    typedef sequence< sequence<string> > stringSeqSeq;
    
    interface QoSAdmin {
        stringSeq method1( in string arg1, inout long arg2 );
        stringSeqSeq method2( in string arg1, inout long arg2, inout long arg3);
        string method3();
      };
    """
    )
test(
    r"""
      const string test="Test String\n";
      const long  a = 0;
      const long  b = -100;
      const float c = 3.14159;
      const long  d = 0x007f7f7f;
      exception TestException
        {
        string msg;
        sequence<string> dataStrings;
        };
      
      interface TestInterface
        {
        void method1( in string arg1, inout long arg2 );
        };
    """
    )
test(
    """
    module Test1 
      {
      exception TestException
        {
        string msg;
        ];
      
      interface TestInterface
        {
        void method1( in string arg1, inout long arg2 ) 
          raises ( TestException );
        };
      };
    """
    )
test(
    """
    module Test1 
      {
      exception TestException
        {
        string msg;
        };

      };
    """
    )
