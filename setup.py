#!/usr/bin/env python
# -*- coding: latin1 -*-

def main():
    from setuptools import setup

    setup(name="cndarray",
          version="2011.1",
          description="A preprocessor that gives C multidimensional arrays",
          #long_description="",
          author=u"Andreas Kloeckner",
          author_email="inform@tiker.net",
          license = "MIT",
          url="http://mathema.tician.de/software/cndarray",
          classifiers=[

              ],
          zip_safe=False,

          install_requires=[ "pycparser", "ply", "pytools"],

          scripts=["bin/cnd"],
          packages=["cndarray"]
         )

if __name__ == "__main__":
    import distribute_setup
    distribute_setup.use_setuptools()

    main()
