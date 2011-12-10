#!/usr/bin/env python
# -*- coding: latin1 -*-

def main():
    import distribute_setup
    distribute_setup.use_setuptools()

    from setuptools import setup

    setup(name="cnd",
          version="2011.2",
          description="A preprocessor that gives C multidimensional arrays",
          long_description=open("README.rst", "rt").read(),
          author=u"Andreas Kloeckner",
          author_email="inform@tiker.net",
          license = "MIT",
          url="http://mathema.tician.de/software/cnd",
          classifiers=[

              ],
          zip_safe=False,

          install_requires=[ "pycparser", "ply"],

          scripts=["bin/cnd", "bin/cndcc"],
          packages=["cnd"]
         )

if __name__ == "__main__":
    import distribute_setup
    distribute_setup.use_setuptools()

    main()
