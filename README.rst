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

It understands all of C99. You may also take a look at a `more complete example
<https://github.com/inducer/cnd/blob/master/examples/basic.c>`_.

Each axis specification in a `dimension` statement has the following form::

    start:end:stride:leading_dimension

`start` may be omitted. `end` and `stride` may also be omitted, but if entries
after them are to be specified, their trailing colons must remain in place. For
example, the axis specification `:5` simply specifies a stride of 5. The stride
simply acts as a multiplier on the index.  No plausibility checking whatsoever
is done on the dimension statement.  You may shoot yourself in the foot any way
you like.

If the layout is given as `"c"` or not given at all, the following things are true:

* The array is laid out in row-major order.
* The `end` index is taken to be exclusive, if specified.
* The `start` index defaults to 0.

If the layout is given as `"fortran"`, the following things are true:

* The array is laid out in column-major order.
* The `end` index is taken to be inclusive, if specified.
* The `start` index defaults to 1.

(Most) of the knowledge contained in the `dimension` statement may be reobtained
programmatically by the follwing functions:

* `rankof(a)`
* `nitems(a)`
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


Future Features
---------------

* Bounds checking.
* Generate #line directives.

Author
------

Andreas Kloeckner <inform@tiker.net>, based on discussions with Zydrunas Gimbutas.
