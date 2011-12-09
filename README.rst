Cndarray is a preprocessor that makes using n-dimensional arrays in C more pleasant.
It will turn this code::

    void dgemm(float *a, float *b, float *c, int n)
    {
      dimension "fortran" a[n, n];
      dimension "fortran" b[n, n];
      dimension c[n, n];

      for (int i = 1; i <= n; ++i)
        for (int j = 1; j <= n; ++i)
        {
          float tmp = 0;

          for (int k = 1; k <= n; ++k)
            tmp += a[i,k]*b[k,j];

          c[i-1,j-1] = tmp;
        }
    }

into this::

    void dgemm(float *a, float *b, float *c, int n)
    {
      for (int i = 1; i <= n; ++i)
        for (int j = 1; j <= n; ++i)
      {
        float tmp = 0;
        for (int k = 1; k <= n; ++k)
          tmp += a[((k - 1) * ((n - 1) + 1)) + (i - 1)] * b[((j - 1) * ((n - 1) + 1)) + (k - 1)];

        c[((i - 1) * n) + (j - 1)] = tmp;
      }
    }

It understands all of C99. 

Each axis specification in a `dimension` statement has the following form::

    start:end:stride:leading_dimension

`start` may be omitted. `end` and `stride` may also be omitted, but if entries
afte them are to be specified, their colons must remain in place. For example,
the axis specification `:5` simply specifies a stride of 5. The stride simply
acts as a multiplier on the index.  No plausibility checking whatsoever is done
on the dimension statement.  You may shoot yourself in the foot any way you
like.

If the layout is given as `"c"` or not given at all, the following things are true:

* The array is laid out in row-major order.
* The `end` index is taken to be exclusive, if specified.
* The `start` index defaults to 0.

If the layout is given as `"fortran"`, the following things are true:

* The array is laid out in column-major order.
* The `end` index is taken to be inclusive, if specified.
* The `start` index defaults to 1.

Installation / Usage
--------------------

You may obtain cndarray from `github <http://github.com/inducer/cndarray>`_::

    $ git clone git://github.com/inducer/cndarray.git
    $ git sumodule init
    $ git sumodule update

To use cndarray, simply add `distribution-dir/bin` to your `PATH`.

Then simply run::

    $ cnd source.c

Note that Cndarray expects preprocessed source. You may pass the option `-E`
to have `cnd` run the preprocessor on your source for you. Run::

    $ cnd -h

to get full help on the command line interface. You may set the `CND_CPP`
environment variable to the preprocessor you wish to use.

You may also run::

    $ cndcc gcc source.c

in which case cnd will run your source files through the preprocessor, do its
source-to-source translation, and then run the compiler you specified.

Future Features
---------------

* Bounds checking.
* Generate #line directives.
* [lu]boundof(a, axis), leadof(a, axis), strideof(a, axis)

Author
------

Andreas Klöckner <inform@tiker.net>, based on discussions with Zydrunas Gimbutas.
