.. note::

    I was surprised to see there were this many (about 150) downloads of CnD in
    the few (2) days since its initial release. As you may have noticed, we've
    gone through a number of syntax changes since Friday, finally ending up
    back where we started. I promise that this will be the last syntax change,
    just in case you were wondering.

CnD is a source-to-source translator that makes using n-dimensional arrays
in C more pleasant.  It will turn this code::

    void sgemm(float *a, float *b, float *c, int n)
    {
      dimension "fortran" a[n, n];
      dimension "fortran" b[n, n];
      dimension c[n, n];

      for (int i = 1; i <= n; ++i)
        for (int j = 1; j <= n; ++j)
        {
          float tmp = 0;

          for (int k = 1; k <= n; ++k)
            tmp += a[i,k]*b[k,j];

          c[i-1,j-1] = tmp;
        }
    }

into this::

    void sgemm(float *a, float *b, float *c, int n)
    {
      for (int i = 1; i <= n; ++i)
        for (int j = 1; j <= n; ++j)
      {
        float tmp = 0;
        for (int k = 1; k <= n; ++k)
          tmp += a[((k - 1) * ((n - 1) + 1)) + (i - 1)] * b[((j - 1) * ((n - 1) + 1)) + (k - 1)];

        c[((i - 1) * n) + (j - 1)] = tmp;
      }
    }

You may also take a look at a `more comprehensive example
<https://github.com/inducer/cnd/blob/master/examples/basic.c>`_
that shows a few extra bells and whistles.

The only effect of a `dimension` declaration is to modify the interpretation of
the `array(idx)` subscript operator. `dimension` declarations obey regular C
scoping rules.

I'd also like to note that CnD is a robust, parser-based translator, not a flaky
text replacement tool.  It understands all of C99, plus many GNU extensions.

Each axis specification in a `dimension` declaration has the following form::

    start:end:stride:leading_dimension

`start` may be omitted. `end` and `stride` may also be omitted, but if entries
after them are to be specified, their trailing colons must remain in place. For
example, the axis specification `:5` simply specifies a stride of 5. The stride
simply acts as a multiplier on the index.  No plausibility checking whatsoever
is done on the dimension declaration.  You may shoot yourself in the foot any way
you like.

If the layout is given as `"c"` or not given at all, the following things are true:

* The array is laid out in row-major order.
* The `end` index is taken to be exclusive, if specified.
* The `start` index defaults to 0.

If the layout is given as `"fortran"`, the following things are true:

* The array is laid out in column-major order.
* The `end` index is taken to be inclusive, if specified.
* The `start` index defaults to 1.

(Most) of the knowledge contained in the `dimension` declaration may be reobtained
programmatically by the follwing functions:

* `rankof(a)`
* `nitemsof(a)`
* `lboundof(a, axis)`
* `uboundof(a, axis)` (returns the user-specified upper bound)
* `puboundof(a, axis)` (returns the index just past the end of axis)
* `ldimof(a, axis)`
* `strideof(a, axis)`

In each case, `axis` must be a constant integer (not a constant expression, a
plain integer).

Installation / Usage
--------------------

You may obtain CnD by downloading the tarball from the `package index
<http://pypi.python.org/pypi/cnd>`_, or from `github
<http://github.com/inducer/cnd>`_::

    $ git clone git://github.com/inducer/cnd.git
    $ cd cnd
    $ git submodule init
    $ git submodule update

To use CnD, simply add `distribution-dir/bin` to your `PATH`.

To get started, simply run (from within the `cnd` root)::

    $ cd examples
    $ ../bin/cndcc gcc -std=c99 basic.c
    $ ./a.out

If you would like more fine-grained control over the translation process, the
`cnd` command exposes just the source-to-source translation.  Note that `cnd`
expects preprocessed source. You may pass the option `-E` to have `cnd` run the
preprocessor on your source for you. Run::

    $ cnd -h

to get full help on the command line interface. You may set the `CND_CPP`
environment variable to the preprocessor you wish to use.

FAQ
---

But isn't there a preprocessor issue with this syntax?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Great point. Consider the following stiuation::

    #define MY_MACRO(a) /* something rather */

    MY_MACRO(array[i,j])

The preprocessor sees the comma and rips our array access apart into two macro
arguments, and then complains that `MY_MACRO` takes only one argument.  Not
very smart, but such is life. (Credit for discovering this goes to Zydrunas
Gimbutas.)

The easiest fix is to use the following syntax::

    MY_MACRO(array[(i,j)])

This is guaranteed to work, always. Some C standard 'functions' may also turn
out to be macros, so in principle you are obliged to use this syntax whenever
you pass the result of a multi-D array access to a function that you haven't
declared yourself. That's obviously inconvienient, so there's one more plot
twist. CnD will rewrite your main source file (but not any included headers!)
by inserting parentheses within brackets (in non-string, non-char-constant,
non-preprocessor contexts). This is a no-op as far as C99 is concerned. As a
result, you are obliged to use the parenthesized syntax only in files that are
not top-level compiled files and only in contexts where the array access might
be part of a macro expansion.

Version History
---------------

2011.4
^^^^^^

(December 11, 2012)

* Syntax change from `a[i;j]` to `a[i,j]`.
* Still more parser support for real-life headers.

2011.3
^^^^^^

(December 10, 2012)

* Syntax change from `a(i,j)` to `a[i;j]`.
* Parser support for many more GNU extensions, `tgmath.h`
  now works on OS X (10.7) and Linux.

2011.2
^^^^^^

(December 10, 2012)

* Syntax change from `a[i,j]` to `a(i,j)`.
* Fixes for OS X and two bugs.
* Generate #line directives.

2011.1
^^^^^^

(December 9, 2012)

Initial release.

Future Features
^^^^^^^^^^^^^^^

* Caching of lexer/parser tables (faster startup)
* Bounds checking.

Author
------

Andreas Kloeckner <inform@tiker.net>, based on discussions with Zydrunas Gimbutas.
