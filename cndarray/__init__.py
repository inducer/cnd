from __future__ import division
import ply
from pycparser.c_lexer import CLexer as CLexerBase
from pycparser.c_parser import CParser as CParserBase
from pycparser import c_ast
from cndarray.generator import CGenerator as CGeneratorBase
import sys




cnd_keywords = ("dimension",)
class CNdArrayLexer(CLexerBase):

    keywords = CLexerBase.keywords + tuple(
            kw.upper() for kw in cnd_keywords)

    keyword_map = CLexerBase.keyword_map.copy()
    keyword_map.update(dict(
        (kw, kw.upper()) for kw in cnd_keywords))

    tokens = CLexerBase.tokens + tuple(
            kw.upper() for kw in cnd_keywords)





class SingleDim(object):
    def __init__(self, layout, start, end, stride, leading_dim):
        self.end = end
        self.stride = stride

        if layout == "fortran" and start is None:
            start = c_ast.Constant("int", 1)

        self.start = start

        if leading_dim is None:
            if start is None:
                leading_dim = end
            else:
                if layout == "fortran":
                    leading_dim = c_ast.BinaryOp("+",
                            c_ast.BinaryOp("-", end, start),
                            c_ast.Constant("int", 1))
                else:
                    leading_dim = c_ast.BinaryOp("-", end, start)

        self.leading_dim = leading_dim

class DimensionDecl(object):
    def __init__(self, name, layout, dims, coord):
        self.name = name

        self.layout = layout
        self.dims = dims

        self.coord = coord

    def children(self):
        return ()





class CNdArrayParser(CParserBase):
    def __init__(self,
            lex_optimize=True,
            lextab='cndarray.lextab',
            yacc_optimize=True,
            yacctab='cndarray.yacctab',
            yacc_debug=False):

        self.clex = CNdArrayLexer(
            error_func=self._lex_error_func,
            type_lookup_func=self._lex_type_lookup_func)

        self.clex.build(
            optimize=lex_optimize,
            lextab=lextab)
        self.tokens = self.clex.tokens

        rules_with_opt = [
            'abstract_declarator',
            'assignment_expression',
            'declaration_list',
            'declaration_specifiers',
            'designation',
            'expression',
            'identifier_list',
            'init_declarator_list',
            'parameter_type_list',
            'specifier_qualifier_list',
            'block_item_list',
            'type_qualifier_list',
            'struct_declarator_list'
        ]

        for rule in rules_with_opt:
            self._create_opt_rule(rule)

        self.cparser = ply.yacc.yacc(
            module=self,
            start='translation_unit',
            debug=yacc_debug,
            optimize=yacc_optimize,
            tabmodule=yacctab)

    def parse(self, text, filename='', debuglevel=0,
            initial_type_symbols=set()):
        self.clex.filename = filename
        self.clex.reset_lineno()

        # _scope_stack[-1] is the current (topmost) scope.

        self._scope_stack = [initial_type_symbols.copy()]
        if not text or text.isspace():
            return c_ast.FileAST([])
        else:
            return self.cparser.parse(text, lexer=self.clex, debug=debuglevel)

    def p_declaration(self, p):
        """ declaration : decl_body SEMI
                        | dimension_decl SEMI
        """
        p[0] = p[1]

    def p_dimension_decl(self, p):
        """ dimension_decl : DIMENSION dim_layout_opt ID LBRACKET dim_spec_mult RBRACKET
        """
        coord = self._coord(p.lineno(1))
        layout = p[2]
        if layout is not None:
            layout = layout[1:-1]

        if layout is None or layout == "c":
            layout = "c"
        elif layout == "fortran":
            pass
        else:
            raise RuntimeError("invalid  array layout '%s'" % layout)

        p[0] = DimensionDecl(p[3], layout, [
            SingleDim(layout, *args) for args in p[5]], coord)

    def p_dim_layout_opt(self, p):
        """ dim_layout_opt : STRING_LITERAL
                           |
        """
        if len(p) == 2:
            p[0] = p[1]
        else:
            p[0] = None

    def p_dim_spec_mult(self, p):
        """ dim_spec_mult : dim_spec
                          | dim_spec_mult COMMA dim_spec
        """
        p[0] = None
        if len(p) == 2:
            p[0] = [p[1]]
        else:
            p[1].append(p[3])
            p[0] = p[1]

    def p_dim_spec(self, p):
        """ dim_spec : dim_start_end_stride
                     | dim_start_end
                     | dim_end
                     | dim_stride
                     | dim_start
                     | dim_start_end_stride_lead
                     | dim_start_end_lead
                     | dim_end_lead
                     | dim_stride_lead

        """
        p[0] = p[1]

    def p_dim_start_end_stride(self, p):
        """ dim_start_end_stride : assignment_expression COLON assignment_expression COLON assignment_expression
        """
        p[0] = (p[1], p[3], p[5], None)

    def p_dim_start_end(self, p):
        """ dim_start_end : assignment_expression COLON assignment_expression
        """
        p[0] = (p[1], p[3], None, None)

    def p_dim_end(self, p):
        """ dim_end : assignment_expression
        """
        p[0] = (None, p[1], None, None)

    def p_dim_stride(self, p):
        """ dim_stride : COLON assignment_expression
        """
        p[0] = (None, None, p[1], None)

    def p_dim_start(self, p):
        """ dim_start : assignment_expression COLON
        """
        p[0] = (p[1], None, None, None)

    def p_dim_start_end_stride_lead(self, p):
        """ dim_start_end_stride_lead : assignment_expression COLON assignment_expression COLON assignment_expression COLON assignment_expression
        """
        p[0] = (p[1], p[3], p[5], p[7])

    def p_dim_start_end_lead(self, p):
        """ dim_start_end_lead : assignment_expression COLON assignment_expression COLON COLON assignment_expression
        """
        p[0] = (p[1], p[3], None, p[5])

    def p_dim_end_lead(self, p):
        """ dim_end_lead : assignment_expression COLON COLON assignment_expression
        """
        p[0] = (None, p[1], None, p[3])

    def p_dim_stride_lead(self, p):
        """ dim_stride_lead : COLON assignment_expression COLON assignment_expression
        """
        p[0] = (None, None, p[1], p[3])





class CGenerator(CGeneratorBase):
    def __init__(self):
        CGeneratorBase.__init__(self)
        self.dim_decl_stack = [{}]

    def visit_DimensionDecl(self, n):
        decl_stack = self.dim_decl_stack[-1]
        if n.name in decl_stack:
            raise RuntimeError("may not redimension array '%s' at %s"
                    % (n.name, n.coord))
        decl_stack[n.name] = n
        return ""

    def visit_Compound(self, n):
        s = self._make_indent() + '{\n'
        self.indent_level += 2

        dim_decls = self.dim_decl_stack[-1].copy()
        self.dim_decl_stack.append(dim_decls)
        for stmt in n.block_items:
            s += ''.join(self._generate_stmt(stmt) )
        self.dim_decl_stack.pop()

        self.indent_level -= 2
        s += self._make_indent() + '}\n'
        return s

    def visit_ArrayRef(self, n):
        if isinstance(n.name, c_ast.ID):
            dim_decl = self.dim_decl_stack[-1].get(n.name.name)
        else:
            dim_decl = None

        if dim_decl is not None:
            if isinstance(n.subscript, c_ast.ExprList):
                indices = n.subscript = n.subscript.exprs
            else:
                indices = [n.subscript]

            if len(indices) != len(dim_decl.dims):
                raise RuntimeError("invalid number of indices in "
                        "array reference to '%s' at %s"
                        % (n.name.name, n.coord))


            if dim_decl.layout == "c":
                dim_it = zip(indices, dim_decl.dims)
            elif dim_decl.layout == "fortran":
                dim_it = zip(indices[::-1], dim_decl.dims[::-1])
            else:
                raise RuntimeError("invalid  array layout '%s'" % dim_decl.layout)

            access = None
            for idx, dim in dim_it:
                if access is not None:
                    access = c_ast.BinaryOp("*", access, dim.leading_dim)

                if dim.stride is not None:
                    idx = c_ast.BinaryOp("*", idx, dim.stride)

                if dim.start is not None:
                    idx = c_ast.BinaryOp("-", idx, dim.start)

                if access is not None:
                    access = c_ast.BinaryOp("+", access, idx)
                else:
                    access = idx

            return "%s[%s]" % (n.name.name, self.visit(access))

        else:
            arrref = self._parenthesize_unless_simple(n.name)
            return arrref + '[' + self.visit(n.subscript) + ']'




def run_standalone():
    from optparse import OptionParser

    parser = OptionParser("usage: %prog [options] source.c")
    parser.add_option("-o", "--output",
            help="write output to FILE (default stdout)", metavar="FILE")
    parser.add_option("-E", "--preprocess", action="store_true")
    parser.add_option("-I", "--include", action="append",
            help="include path, passed on to C preprocessor", metavar="PATH")
    parser.add_option("-D", "--define", action="append",
            help="C macro definition, passed on to C preprocessor",
            metavar="NAME[=VALUE]")
    parser.add_option("--cpp",
            help="C preprocessor to use", metavar="COMMAND",
            default="cpp")

    (options, args) = parser.parse_args()

    if not args:
        parser.print_help()
        sys.exit(1)

    in_file = args[0]

    src = open(in_file, "rt").read()

    parser = CNdArrayParser()
    ast = parser.parse(src, filename=in_file,
            initial_type_symbols=set(["dimension", "fdimension"]))
    generator = CGenerator()

    if options.output is not None:
        outf = open(options.output, "wt")
    else:
        outf = sys.stdout

    try:
        outf.write(generator.visit(ast))
    finally:
        if options.output is not None:
            outf.close()




def run_as_compiler_frontend():
    raise NotImplementedError
