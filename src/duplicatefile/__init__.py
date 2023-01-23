#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# noqa: D205,D400
"""
Duplicate file finder:
    [![badge](https://forthebadge.com/images/badges/made-with-python.svg)]()
    ![](./doc/pycodestyle-passing.svg)
    ![](./doc/pylint-passing.svg)
    ![](./doc/mypy-passing.svg)

Description:

    Yes, another duplicate file finder with Python...

    There are various approaches to finding duplicate files using Python, but
    when working with a large number of files, such as 2400 files, a simple
    script may be inefficient and may consume a large amount of memory,
    potentially causing the environment to crash. In this case, we tried using
    a tool, but found that the analysis process was time-consuming and the user
    interface was not very efficient.

    In my opinion, a duplicate file is one that has the same content as another
    file, which can be determined by comparing its size and hash value. As a
    solution, we decided to use Python to filter the files by size and to
    enhance the hash step using the xxhash library. This allowed us to
    effectively identify and handle duplicate files in a more efficient manner.


    Whats this script do:
    - file duplicate analysis
    - report through the ssh
    - dump a JSON file

    What this script dont do:
    - delete files
    - make the cofee
    - bitcoin analysis

Use:
    ```shell
    $ find-duplicate
    USAGE: find-duplicate [-h] [--version] [--debug] [--logfile]
                          [--dump] -p PATH

    DESCRIPTION:
        This module find duplicate files in a path using "-p <path>" option
        with the command line.

    OPTIONS:
      -h, --help            show this help message and exit
      --version             show program's version number and exit
      --debug               print debug messages to stderr
      --logfile             generate a logfile - "report.log"
      --dump                generate a summary - "summary_<id>.json"

    REQUIRED ARGUMENTS:
      -p, --path PATH       define the /path/to/check

    COMPATIBILITY:
        Python 3.7+ - https://www.python.org/

    EXIT STATUS:
        This script exits 0 on success, and >0 if an error occurs.
    ```

Compatibility:
    Python 3.7+

Setup:
    - User:

    Get the package:
    ```shell
    $ git clone https://github.com/francois-le-ko4la/duplicate-file-finder.git
    ```
    Enter in the directory:
    ```shell
    $ cd duplicate-file-finder
    ```
    Install with make on Linux/Unix/MacOS or use pip3 otherwise:
    ```shell
    $ make install
    ```

    - Dev environment:

    Get the package:
    ```shell
    $ git clone https://github.com/francois-le-ko4la/duplicate-file-finder.git
    ```
    Enter in the directory:
    ```shell
    $ cd duplicate-file-finder
    ```
    Create your environment with all dev prerequisites and install the package:
    ```shell
    make venv
    source venv/bin/activate
    make dev
    ```

Test:
    This module has been tested and validated on Ubuntu.
    Test is available if you set up the package with dev environment.
    ```shell
    make test
    ```

License:
    This package is distributed under the [GPLv3 license](./LICENSE)

"""
