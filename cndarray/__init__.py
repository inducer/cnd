from __future__ import division
import ply
from pycparser.c_lexer import CLexer as CLexerBase
from pycparser.c_parser import CParser as CParserBase
from pycparser import c_ast
from pycparser.c_generator import CGenerator as CGeneratorBase
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

        if leading_dim is None and end is not None:
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

    def __repr__(self):
        generator = CGenerator()

        def stringify(x):
            if x is None:
                return "None"
            else:
                return generator.visit(x)

        return "Axis(start=%s, end=%s, stride=%s, leading_dim=%s)" % (
                stringify(self.start),
                stringify(self.end),
                stringify(self.stride),
                stringify(self.leading_dim))

class DimensionDecl(c_ast.Node):
    def __init__(self, name, layout, dims, coord):
        self.name = name

        self.layout = layout
        self.dims = dims

        self.coord = coord

    def children(self):
        return ()

    attr_names = ("name", "layout", "dims")





class CNdArrayParser(CParserBase):
    def __init__(self,
            yacc_debug=False):

        self.clex = CNdArrayLexer(
            error_func=self._lex_error_func,
            type_lookup_func=self._lex_type_lookup_func)

        self.clex.build()
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
            debug=yacc_debug)

    def parse(self, text, filename='', debuglevel=0,
            initial_type_symbols=set()):
        self.clex.filename = filename
        self.clex.reset_lineno()

        # _scope_stack[-1] is the current (topmost) scope.

        self._scope_stack = [set(initial_type_symbols)]
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
                           | empty
        """
        p[0] = p[1]

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

    def p_bound_expr_opt(self, p):
        """ bound_expr_opt : assignment_expression
                           | empty
        """
        p[0] = p[1]

    def p_dim_spec_1(self, p):
        """ dim_spec : assignment_expression
        """
        p[0] = (None, p[1], None, None)

    def p_dim_spec_2(self, p):
        """ dim_spec : bound_expr_opt COLON bound_expr_opt
        """
        p[0] = (p[1], p[3], None, None)

    def p_dim_spec_3(self, p):
        """ dim_spec : bound_expr_opt COLON bound_expr_opt COLON bound_expr_opt
        """
        p[0] = (p[1], p[3], p[5], None)

    def p_dim_spec_4(self, p):
        """ dim_spec : bound_expr_opt COLON bound_expr_opt COLON bound_expr_opt COLON bound_expr_opt
        """
        p[0] = (p[1], p[3], p[5], p[7])





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

            axis_numbers = range(len(indices))

            if dim_decl.layout == "c":
                dim_it = zip(indices, dim_decl.dims, axis_numbers)
            elif dim_decl.layout == "fortran":
                dim_it = zip(indices[::-1], dim_decl.dims[::-1], axis_numbers[::-1])
            else:
                raise RuntimeError("invalid  array layout '%s'" % dim_decl.layout)

            access = None
            for idx, dim, axis in dim_it:
                if access is not None:
                    if dim.leading_dim is None:
                        raise RuntimeError("missing information on length of "
                                "axis %d of array '%s', declared at %s"
                                % (axis, n.name.name, dim_decl.coord))
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





class ExecError(RuntimeError):
    pass

def call_capture_output(cmdline, cwd=None, error_on_nonzero=True):
    """
    :returns: a tuple (return code, stdout_data, stderr_data).
    """
    from subprocess import Popen, PIPE
    try:
        popen = Popen(cmdline, cwd=cwd, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        stdout_data, stderr_data = popen.communicate()
        if error_on_nonzero and popen.returncode:
            raise ExecError("status %d invoking '%s': %s"
                    % (popen.returncode, " ".join(cmdline), stderr_data))
        return popen.returncode, stdout_data, stderr_data
    except OSError, e:
        raise ExecError("error invoking '%s': %s"
                % ( " ".join(cmdline), e))




class CompileError(RuntimeError):
    def __init__(self, msg, command_line, stdout=None, stderr=None):
        self.msg = msg
        self.command_line = command_line
        self.stdout = stdout
        self.stderr = stderr

    def __str__(self):
        result = self.msg
        if self.command_line:
            try:
                result += "\n[command: %s]" % (" ".join(self.command_line))
            except Exception, e:
                print e
        if self.stdout:
            result += "\n[stdout:\n%s]" % self.stdout
        if self.stderr:
            result += "\n[stderr:\n%s]" % self.stderr

        return result




def write_temp_file(contents, suffix):
    from tempfile import mkstemp
    handle, path = mkstemp(suffix='.c')

    import os

    try:
        outf = open(path, 'w')
        try:
            outf.write(contents)
        finally:
            outf.close()
    finally:
        os.close(handle)

    return path

def preprocess_source(source, cpp, options):
    import os
    if cpp is None:
        cpp = os.environ.get("CND_CPP")
    if cpp is None:
        cpp = os.environ.get("CPP")
    if cpp is None:
        cpp = "cpp"

    cpp = cpp.split()

    from tempfile import mkstemp
    handle, source_path = mkstemp(suffix='.c')

    import os

    source_path = write_temp_file(source, ".c")
    try:
        cmdline = cpp + options + [source_path]

        result, stdout, stderr = call_capture_output(cmdline, error_on_nonzero=False)

        if result != 0:
            raise CompileError("preprocessing of %s failed" % source_path,
                               cmdline, stderr=stderr)
    finally:
        os.unlink(source_path)

    return stdout




INITIAL_TYPE_SYMBOLS = ["__builtin_va_list"]
GCC_DEFINES = [
        "#define __const const",
        "#define __restrict restrict",
        "#define __extension__ /*empty*/", # FIXME
        ]




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
            help="C preprocessor to use", metavar="COMMAND")
    parser.add_option("--ast", action="store_true", help="print syntax tree, quit")

    (options, args) = parser.parse_args()

    if not args:
        parser.print_help()
        sys.exit(1)

    in_file = args[0]

    src = open(in_file, "rt").read()

    extra_lines = GCC_DEFINES + [
        "# 1 \"%s\"" % in_file,
        ]
    src =  "\n".join(extra_lines) + "\n" + src

    if options.preprocess:
        cpp_options = []
        #cpp_options = ["-P"]
        if options.include:
            for inc_dir in options.include:
                cpp_options.extend(["-I", inc_dir])

        if options.define:
            for define in options.define:
                cpp_options.extend(["-D", define])

        src = preprocess_source(src, options.cpp, cpp_options)

    #print "preprocessed source in ", write_temp_file(src, ".c")

    parser = CNdArrayParser()
    ast = parser.parse(src, filename=in_file,
            initial_type_symbols=INITIAL_TYPE_SYMBOLS)
    if options.ast:
        ast.show()
        return

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
    import sys
    import os

    argv = sys.argv[2:]
    compiler = sys.argv[1]

    cpp_options = []

    new_argv = []

    temp_files = []

    to_object_file = False
    seen_dash_o = False

    try:
        for arg in argv:
            if arg.endswith(".c") and not arg.startswith("-"):
                src = open(arg, "rt").read()

                extra_lines = GCC_DEFINES + [
                    "# 1 \"%s\"" % arg,
                    ]
                src =  "\n".join(extra_lines) + "\n" + src

                #cpp_options.append("-P")

                src = preprocess_source(src, "cpp", cpp_options)

                #print "preprocessed source in ", write_temp_file(src, ".c")

                parser = CNdArrayParser()
                ast = parser.parse(src, filename=arg,
                        initial_type_symbols=INITIAL_TYPE_SYMBOLS)

                generator = CGenerator()

                gen_src_file = write_temp_file(generator.visit(ast), ".c")
                new_argv.append(gen_src_file)
                temp_files.append(gen_src_file)

            elif arg.startswith("-I") or arg.startswith("-D"):
                cpp_options.append(arg)
                new_argv.append(arg)
            elif arg == "-c":
                to_object_file = True
                new_argv.append(arg)
            elif arg.startswith("-o"):
                seen_dash_o = True
                new_argv.append(arg)
            else:
                new_argv.append(arg)

        if to_object_file and not seen_dash_o:
            raise RuntimeError("-o<NAME> is required with -c")

        from subprocess import call
        retcode = call([compiler] + new_argv)

        sys.exit(retcode)
    finally:
        for tempf in temp_files:
            os.unlink(tempf)
