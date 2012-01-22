from __future__ import division

import sys
if sys.version_info < (2, 5):
    raise RuntimeError("CnD requires Python 2.5 or newer. "
            "Try running 'python2.5 cndcc <arguments>' or "
            "'python2.6 cndcc <arguments>'.")

import ply
from pycparserext.ext_c_lexer import (
        add_lexer_keywords,
        GNUCLexer as GNUCLexerBase,
        OpenCLCLexer as OpenCLCLexerBase,
        )
from pycparser import c_ast
from pycparserext.ext_c_parser import (
        GnuCParser as GNUCParserBase,
        OpenCLCParser as OpenCLCParserBase,
        )

from pycparserext.ext_c_generator import (
        GNUCGenerator as GNUCGeneratorBase,
        OpenCLCGenerator as OpenCLCGeneratorBase,
        )

import sys





import cnd.version

CND_HELPERS = """
#define CND_ALLOC_HEAP(type, name) \
  name = malloc(nitemsof(name)*sizeof(type));

#define CND_DECL_ALLOC_HEAP(type, name) \
  type *name; \
  CND_ALLOC_HEAP(type, name)

#define CND_DECL_ALLOC_STACK(type, name) \
  type name[nitemsof(name)];

#define CND_FOR_AXIS(it_var, name, ax_index) \
  for (long it_var = lboundof(name, ax_index); it_var < puboundof(name, ax_index); ++it_var)

#define CND_VERSION_MAJOR %(major_ver)d
#define CND_VERSION_MINOR %(minor_ver)d
#define CND_VERSION_TEXT %(text_ver)s
""" % dict(
        major_ver=cnd.version.VERSION[0],
        minor_ver=cnd.version.VERSION[1],
        text_ver=cnd.version.VERSION_TEXT,
        )




# {{{ lexers

class GNUCndLexer(GNUCLexerBase):
    pass

class OpenCLCndLexer(OpenCLCLexerBase):
    pass

cnd_keywords = ("dimension",)

add_lexer_keywords(GNUCndLexer, cnd_keywords)
add_lexer_keywords(OpenCLCndLexer, cnd_keywords)

# }}}

# {{{ parenthesis insertion

def insert_parens_in_brackets(filename, s):
    lines = s.split("\n")

    new_lines = []
    li = 0
    in_string = None

    while li < len(lines):
        line = lines[li]
        li += 1

        if line.lstrip().startswith("#"):
            while True:
                new_lines.append(line)

                if li >= len(lines) or not line.endswith("\\"):
                    break

                line = lines[li]
                li += 1

            continue

        new_line = []

        i = 0

        while i < len(line):
            c = line[i]

            if c == "[" and not in_string:
                new_line.append("[(")
                i += 1
            elif c == "]" and not in_string:
                new_line.append(")]")
                i += 1
            elif c in "'\"" and not in_string:
                new_line.append(c)
                i += 1
                in_string = c
            elif c in "'\"" and in_string == c:
                new_line.append(c)
                i += 1
                in_string = None
            elif c == "\\" and in_string:
                new_line.append(c)
                i += 1
                if i < len(line):
                    new_line.append(line[i])
                    i += 1
            else:
                new_line.append(c)
                i += 1

        new_lines.append("".join(new_line))

    return "\n".join(new_lines)

# }}}





# {{{ AST helper objects

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
        generator = GNUCGenerator()

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

# }}}

# {{{ parsers

class CndParserBase(object):

    # {{{ hack around [()]

    def p_direct_no_dim_array_declarator_with_parens(self, p):
        """ direct_declarator   : direct_declarator LBRACKET LPAREN RPAREN RBRACKET
        """
        arr = c_ast.ArrayDecl(
            type=None,
            dim=None,
            coord=p[1].coord)

        p[0] = self._type_modify_decl(decl=p[1], modifier=arr)

    def p_direct_abstract_no_dim_array_declarator_with_parens(self, p):
        """ direct_abstract_declarator  : direct_abstract_declarator LBRACKET LPAREN RPAREN RBRACKET
        """
        arr = c_ast.ArrayDecl(
            type=None,
            dim=None,
            coord=p[1].coord)

        p[0] = self._type_modify_decl(decl=p[1], modifier=arr)

    def p_direct_abstract_no_dim_array_declarator_with_parens_2(self, p):
        """ direct_abstract_declarator  : LBRACKET LPAREN RPAREN RBRACKET
        """
        p[0] = c_ast.ArrayDecl(
            type=c_ast.TypeDecl(None, None, None),
            dim=None,
            coord=self._coord(p.lineno(1)))

    # }}}

    def p_declaration(self, p):
        """ declaration : decl_body SEMI
                        | dimension_decl SEMI
        """
        p[0] = p[1]

    def p_dimension_decl(self, p):
        """ dimension_decl : DIMENSION dim_layout_opt ID LBRACKET lparen_opt dim_spec_mult rparen_opt RBRACKET
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
            SingleDim(layout, *args) for args in p[6]], coord)

    def p_lparen_opt(self, p):
        """ lparen_opt : LPAREN
                       | empty
        """
        p[0] = None

    def p_rparen_opt(self, p):
        """ rparen_opt : RPAREN
                       | empty
        """
        p[0] = None

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


class GNUCndParser(CndParserBase, GNUCParserBase):
    lexer_class = GNUCndLexer

class OpenCLCndParser(CndParserBase, OpenCLCParserBase):
    lexer_class = OpenCLCndLexer

# }}}




class SyntaxError(RuntimeError):
    pass

# {{{ generators

class CndGeneratorMixin(object):
    def __init__(self):
        self.dim_decl_stack = [{}]
        self.generate_line_directives = True

    def visit_DimensionDecl(self, n):
        decl_stack = self.dim_decl_stack[-1]
        if n.name in decl_stack:
            raise SyntaxError("may not redimension array '%s' at %s"
                    % (n.name, n.coord))
        decl_stack[n.name] = n
        return ""

    # overrides base to treat dim_decl_stack
    def visit_Compound(self, n):
        s = self._make_indent() + '{\n'
        self.indent_level += 2

        dim_decls = self.dim_decl_stack[-1].copy()
        self.dim_decl_stack.append(dim_decls)
        for stmt in n.block_items:
            if self.generate_line_directives:
                s += "# %d \"%s\"\n" % (
                    stmt.coord.line, stmt.coord.file)

            s += ''.join(self._generate_stmt(stmt))

        self.dim_decl_stack.pop()

        self.indent_level -= 2
        s += self._make_indent() + '}\n'
        return s

    def generate_array_ref(self, dim_decl, name, indices, coord):
        if len(indices) != len(dim_decl.dims):
            raise SyntaxError("invalid number of indices in "
                    "array reference to '%s' at %s (given: %d, needed: %d)"
                    % (name, coord, len(indices), len(dim_decl.dims)))

        axis_numbers = range(len(indices))

        if dim_decl.layout == "c":
            dim_it = zip(indices, dim_decl.dims, axis_numbers)
        elif dim_decl.layout == "fortran":
            dim_it = zip(indices[::-1], dim_decl.dims[::-1], axis_numbers[::-1])
        else:
            raise SyntaxError("invalid  array layout '%s'" % dim_decl.layout)

        access = None
        for idx, dim, axis in dim_it:
            if access is not None:
                if dim.leading_dim is None:
                    raise SyntaxError("missing information on length of "
                            "axis %d of array '%s', declared at %s"
                            % (axis, name, dim_decl.coord))
                access = c_ast.BinaryOp("*", access, dim.leading_dim)

            if dim.stride is not None:
                idx = c_ast.BinaryOp("*", idx, dim.stride)

            if dim.start is not None:
                idx = c_ast.BinaryOp("-", idx, dim.start)

            if access is not None:
                access = c_ast.BinaryOp("+", access, idx)
            else:
                access = idx

        return "%s[%s]" % (name, self.visit(access))

    def visit_ArrayRef(self, n):
        if isinstance(n.name, c_ast.ID):
            if isinstance(n.name, c_ast.ID):
                dim_decl = self.dim_decl_stack[-1].get(n.name.name)
            else:
                dim_decl = None

            if isinstance(n.subscript, c_ast.ExprList):
                indices = n.subscript.exprs
            else:
                indices = (n.subscript,)

            if dim_decl is not None:
                return self.generate_array_ref(dim_decl, n.name.name, indices, n.coord)

        return self.generator_base_class.visit_ArrayRef(self, c_ast.ArrayRef(
            n.name, n.subscript, n.coord))

    def visit_FuncCall(self, n):
        if isinstance(n.name, c_ast.ID) and isinstance(n.args, c_ast.ExprList):
            name = n.name.name
            args = n.args.exprs

            def check_arg_count(needed):
                if len(args) != needed:
                    raise SyntaxError("%s takes exactly %d argument(s), "
                            "%d given at %s"
                            % (name, needed, len(args), n.coord))

            def get_dim_decl():
                if not isinstance(args[0], c_ast.ID):
                    raise SyntaxError("may not call '%s' "
                            "on undimensioned expression '%s' at %s"
                            % (name, args[0], n.coord))

                dim_decl = self.dim_decl_stack[-1].get(args[0].name)

                if dim_decl is None:
                    raise SyntaxError("no dimension statement found for '%s' at %s"
                            % (args[0].name, n.coord))

                return dim_decl

            def is_an_int(s):
                try:
                    int(s)
                except TypeError:
                    return False
                else:
                    return True

            if name == "rankof":
                check_arg_count(1)
                dim_decl = get_dim_decl()
                return str(len(dim_decl.dims))

            if name == "nitemsof":
                check_arg_count(1)
                dim_decl = get_dim_decl()
                result = None
                for i, axis in enumerate(dim_decl.dims):
                    if axis.leading_dim is None:
                        raise SyntaxError("no length information for axis %d "
                                "of %s at %s" % (i, args[0].name, n.coord))

                    if result is None:
                        result = axis.leading_dim
                    else:
                        result = c_ast.BinaryOp("*", result, axis.leading_dim)

                return self.visit(result)

            elif name in ["lboundof", "uboundof", "puboundof", "ldimof", "strideof"]:
                check_arg_count(2)
                dim_decl = get_dim_decl()

                if not (isinstance(args[1], c_ast.Constant) and
                        is_an_int(args[1].value)):
                    raise SyntaxError("second argument of '%s' "
                            "at %s is not a constant integer"
                            % (name, n.coord))

                axis = int(args[1].value)

                if name == "lboundof":
                    result = dim_decl.dims[axis].start
                elif name == "uboundof":
                    result = dim_decl.dims[axis].end
                elif name == "puboundof":
                    if dim_decl.layout == "c":
                        result = dim_decl.dims[axis].end
                    elif dim_decl.layout == "fortran":
                        result = c_ast.BinaryOp("+",
                                dim_decl.dims[axis].end, c_ast.Constant("int", 1))
                    else:
                        raise SyntaxError("invalid array layout '%s'" % dim_decl.layout)

                elif name == "ldimof":
                    result = dim_decl.dims[axis].leading_dim
                elif name == "strideof":
                    result = dim_decl.dims[axis].leading_dim
                else:
                    raise SyntaxError("invalid dim query '%s'" % name)

                if result is None:
                    raise SyntaxError("no value available for '%s' at %s" % (
                        self.generator_base_class.visit_FuncCall(self, n), n.coord))

                return self.visit(result)

        return self.generator_base_class.visit_FuncCall(self, n)




class GNUCGenerator(CndGeneratorMixin, GNUCGeneratorBase):
    generator_base_class = GNUCGeneratorBase
    def __init__(self):
        GNUCGeneratorBase.__init__(self)
        CndGeneratorMixin.__init__(self)

class OpenCLCGenerator(CndGeneratorMixin, OpenCLCGeneratorBase):
    generator_base_class = OpenCLCGeneratorBase
    def __init__(self):
        OpenCLCGeneratorBase.__init__(self)
        CndGeneratorMixin.__init__(self)

# }}}

# {{{ run helpers

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
        import sys
        if sys.platform.startswith("darwin"):
            cpp = "gcc -E"
        else:
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
        pass
        #os.unlink(source_path)

    return stdout




PREAMBLE = [
        CND_HELPERS,
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
    src = insert_parens_in_brackets(in_file, src)

    if options.preprocess:
        extra_lines = PREAMBLE + [
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

    parser = GNUCndParser()
    ast = parser.parse(src, filename=in_file)
    if options.ast:
        ast.show()
        return

    generator = GNUCGenerator()

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
                src = insert_parens_in_brackets(arg, src)

                extra_lines = PREAMBLE + [
                    "# 1 \"%s\"" % arg,
                    ]
                src =  "\n".join(extra_lines) + "\n" + src

                #cpp_options.append("-P")

                src = preprocess_source(src, None, cpp_options)

                #print "preprocessed source in ", write_temp_file(src, ".c")

                parser = GNUCndParser()
                ast = parser.parse(src, filename=arg)

                generator = GNUCGenerator()

                gen_src_file = write_temp_file(generator.visit(ast), ".c")
                new_argv.append(gen_src_file)
                temp_files.append(gen_src_file)

            elif arg.startswith("-I") or arg.startswith("-D") or arg.startswith("-std="):
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
        try:
            retcode = call([compiler] + new_argv)
        except:
            print>>sys.stderr, "%s: compiler execution failed. (Note: compiler " \
                    "command must be the first argument--used '%s')" % (sys.argv[0], compiler)
            sys.exit(1)
        else:
            sys.exit(retcode)

    finally:
        for tempf in temp_files:
            os.unlink(tempf)




def transform_cl(src, filename=None):
    parser = OpenCLCndParser()
    ast = parser.parse(src, filename=filename)

    generator = OpenCLCGenerator()
    generator.generate_line_directives = False
    return generator.visit(ast)


# }}}

# vim: fdm=marker
