#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Metadata with importlib_metadata:
# mypy: disable-error-code=no-redef
"""
duplicatefile: Main module.

DESCRIPTION:
    This module find duplicate files in a path using "-p <path>" option with
    the command line.

"""
from __future__ import annotations

import json
import logging
import os
import sys
import textwrap

try:
    from importlib import metadata
except ImportError:
    import importlib_metadata as metadata  # type: ignore

from argparse import ArgumentParser, Namespace
from collections import Counter, deque
from enum import IntEnum, unique
from logging import Logger
from time import perf_counter
from typing import Any, BinaryIO, NamedTuple, Optional

import xxhash
from rich.logging import RichHandler
from rich_argparse import RawDescriptionRichHelpFormatter

# ------------------------------------------------------------------------------
# README
# ------------------------------------------------------------------------------

EPILOG = """
COMPATIBILITY:
    Python 3.7+ - https://www.python.org/

EXIT STATUS:
    This script exits 0 on success, and >0 if an error occurs.

HISTORY:
    0.1.0:  First release
"""

# ------------------------------------------------------------------------------
# Parameters
# ------------------------------------------------------------------------------
# author and release
__pkg_name__: str = "duplicatefile"
__version__: str = metadata.version(__pkg_name__)
__author__: str = metadata.metadata(__pkg_name__)["Author"]


# exit values
@unique
class ExitStatus(IntEnum):
    """Define Exit status."""

    EX_OK: int = getattr(os, 'EX_OK', 0)
    EX_USAGE: int = getattr(os, 'EX_USAGE', 64)
    EX_CANTCREAT: int = getattr(os, 'EX_CANTCREAT', 73)
    EX_CONFIG: int = getattr(os, 'EX_CONFIG', 78)


# python
CHK_PYT_MIN: tuple[int, int, int] = (3, 7, 0)
CWD: str = os.path.abspath(os.getcwd())
PID: int = os.getpid()


# logging
class LoggingSetup(NamedTuple):
    """Define logging Parameters.

    Examples:
    >>> my_setup = LoggingSetup()
    >>> my_setup.default_level
    'INFO'

    """

    default_level: str = 'INFO'
    log_file: str = f'{CWD}/report.log'
    default_format: str = '%(message)s'
    simple_format: str = '%(levelname)s %(message)s'
    file_format: str = '%(asctime)s - %(levelname)s - %(message)s'
    json_dump: str = f'{CWD}/dump_{PID}.json'
    encoding: str = 'utf-8'


class EventMSG(NamedTuple):
    """Define Messages with different sev.

    Attributes:
        info (str): message for info ("" by default)
        warning (str): message for warning ("" by default)
        error (str): message for error ("" by default)
        debug (str): message for debug ("" by default)

    Examples:
        >>> logfile = EventMSG(info="Log file used: %s")
        >>> logfile.info
        'Log file used: %s'

    """

    info: str = ""
    warning: str = ""
    error: str = ""
    debug: str = ""


class LogMessages(NamedTuple):
    """Set standard logging messages."""

    logfile: EventMSG = EventMSG(
        info="Log file used: %s")
    args: EventMSG = EventMSG(
        debug="Arguments: %s")
    path: EventMSG = EventMSG(
        info="Path : '%s'",
        error="Path is not a folder : %s",
        debug="")
    python: EventMSG = EventMSG(
        info="Python version is supported: %s",
        error="Python version is not supported: %s",
        debug="Python: %s")
    python_import: EventMSG = EventMSG(
        info="Python modules imported.",
        error=f"Install modules. Use ./{os.path.basename(__file__)} --help",
        debug="IMPORT MSG: %s")
    dump: EventMSG = EventMSG(
        info="New report has been created: %s",
        error="New report has not been created.",
        debug="New report cannot be saved:")
    result: EventMSG = EventMSG(
        info="Result:\n%s")
    num_of_files: EventMSG = EventMSG(
        info="Number of files: %s")
    elapse_time: EventMSG = EventMSG(
        info="Elapse time: %s s")


LOG_SETUP: LoggingSetup = LoggingSetup()
LOG_MSG: LogMessages = LogMessages()
ARG_STYLE: dict[str, str] = {
    'argparse.yellow': 'yellow',
    'argparse.byellow': 'yellow bold',
    'argparse.cyan': 'cyan',
    'argparse.bcyan': 'cyan bold',
    'argparse.red': 'red',
    'argparse.green': 'green',
    'argparse.bgreen': 'green bold',
    'argparse.magenta': 'magenta',
    'argparse.grey': 'grey37 bold'}
ARG_HIGHLIGHT: list[str] = [
    r'(?P<cyan>INFO)',
    r'(?P<red>ERROR)',
    r'(?P<green>DEBUG)',
    r'([$]|c:\\>) (?P<red>\S+)',
    r'\n(?P<groups>[^\s](.+:))\n',
    r'(?P<green>(\"(.+?)\"))',
    r'(?P<bgreen>✔)',
    r'(?P<byellow>(Python 3|Pip3|PEP8|Pylint|Prospector))',
    r'(?P<bcyan>(MAC OS|Windows))',
    r'(?P<grey>([$]|c:\\>))',
    r'(?P<grey>((?:#|http)\S+))',
    r'(-i|-c) (?P<metavar>[a-zA-Z0-9_. ]+)',
    r'(?P<magenta>(<\S+>|\S+==\S+))',
    r'[ \(]+(?P<bcyan>[\d]+[.][\d.]+[s+]*)']


# ------------------------------------------------------------------------------
# Windows specific
# ------------------------------------------------------------------------------
# enables ansi escape characters in Windows terminals
if os.name == "nt":
    os.system("")

# ------------------------------------------------------------------------------
# logging
# ------------------------------------------------------------------------------
current_handlers = [RichHandler(rich_tracebacks=True, show_time=False)]
current_format = LOG_SETUP.default_format

logging.basicConfig(
    level=LOG_SETUP.default_level,
    format=current_format,
    handlers=current_handlers
)

logger: Logger = logging.getLogger(__name__)


# ------------------------------------------------------------------------------
# arguments and options
# ------------------------------------------------------------------------------
def get_argparser() -> ArgumentParser:
    """Define the argument parser.

    This function define the argument parser and return it.
    Returns:
        ArgumentParser
    Examples:
        >>> a = get_argparser()
        >>> type(a)
        <class 'argparse.ArgumentParser'>
    """
    cur_formatter = RawDescriptionRichHelpFormatter
    RawDescriptionRichHelpFormatter.styles.update(ARG_STYLE)
    RawDescriptionRichHelpFormatter.highlights.extend(ARG_HIGHLIGHT)

    version: str = f'%(prog)s {__version__}'
    parser: ArgumentParser = ArgumentParser(
        description=__doc__, epilog=EPILOG, formatter_class=cur_formatter)

    parser.add_argument('--version', action='version', version=version)
    parser.add_argument(
        '--debug',
        help='print debug messages to stderr',
        default=False, action='store_true')
    parser.add_argument(
        '--logfile',
        help='generate a logfile - "report.log"',
        default=False, action='store_true')
    parser.add_argument(
        '--dump',
        help='generate a summary - "summary_<id>.json"',
        default=False, action='store_true')
    required_argument = parser.add_argument_group(
        'required arguments')
    required_argument.add_argument(
        '-p', '--path',
        help=textwrap.dedent('''
        define the /path/to/check
        '''),
        required=True)

    return parser


# ------------------------------------------------------------------------------
# File management
# ------------------------------------------------------------------------------
class MyFile(NamedTuple):
    """Describe a file with a NamedTuple.

    @classmethod is used to init the objects correctly.

    Notes:
        The objective is to define a file with only one NamedTuple.
        The NamedTuple will be created by the get_size function to define the
        path and size.
        Hash information consumes resources, and it will calculate later with
        get_hash function to create a new NamedTuple.

    Examples:
        >>> test = MyFile.get_size("test_fic/doc.txt")
        >>> test
        MyFile(path='test_fic/doc.txt', size=544)
        >>> test = test.get_hash()
        >>> test
        MyFile(path='test_fic/doc.txt', size=544, hash='a5cd732df22bfdbd')

    """

    path: str
    size: Optional[int] = None
    hash: Optional[str] = None

    @classmethod
    def get_size(cls, path: str) -> MyFile:
        """Define a Myfile obj with path.

        This function create the MyFile object with the file's path,
        file's size is initialized by default and hash is None by default.
        The path is not tested here, because we use os.walk to get the file
        list.

        Args:
            path: The file's path.

        Returns:
            MyFile

        Examples:
            >>> test = MyFile.get_size('test_fic/doc.txt')
            >>> test
            MyFile(path='test_fic/doc.txt', size=544)

        """
        return cls(path, os.stat(path).st_size)

    def get_hash(self, blocksize: int = 65536) -> MyFile:
        """Calculate file's hash and generate a new obj.

        This function is used on an existing Myfile obj and recreate
        a new MyFile obj.

        Args:
          blocksize:  blocksize used to read the file. (Default value = 65536)

        Returns:
            MyFile

            >>> test = MyFile.get_size('test_fic/doc.txt')
            >>> test = test.get_hash()
            >>> test
            MyFile(path='test_fic/doc.txt', size=544, hash='a5cd732df22bfdbd')

        """
        hasher: xxhash.xxh3_64 = xxhash.xxh64()
        file: BinaryIO
        with open(self.path, 'rb') as file:
            buf: bytes = file.read(blocksize)
            while len(buf) > 0:
                hasher.update(buf)
                buf = file.read(blocksize)
        # Get the hashed representation
        # pylint: disable=no-member
        return self._replace(hash=hasher.hexdigest())

    def __repr__(self) -> str:
        """Get the repr."""
        _repr: str = f"path='{self.path}', size={self.size}"
        if self.hash is not None:
            _repr = f"{_repr}, hash='{self.hash}'"
        return f'{self.__class__.__name__}({_repr})'


class DetectDuplicate:
    """Class to organize and find duplicate files."""

    __path: str
    __files: deque[MyFile]
    __hash: deque[list[MyFile]]
    __summary: dict[str, Any]

    def __init__(self, path: str) -> None:
        """Get the Path init internal attributes."""
        self.__path = path
        self.__get_files()
        self.__find_duplicate()
        self.__gen_details()

    def __str__(self) -> str:
        """Define the str function."""
        result = ""
        for cur_hash in self.__hash:
            result = "%s\n- Same files (%s):\n -> '%s'" % (
                result,
                cur_hash[0].hash,
                "'\n -> '".join([cur_file.path for cur_file in cur_hash]))
        return result

    @property
    def num_of_files(self) -> int:
        """Get the number of files.

        Returns:
            int: Number of files.

        Examples:
            >>> a = DetectDuplicate('test_fic/')
            >>> a.num_of_files
            5

        """
        return len(self.__files)

    def get_json(self) -> str:
        """Get the result (JSON format).

        Returns:
            str: result (JSON).

        Examples:
            >>> a = DetectDuplicate('test_fic/')
            >>> print(a.get_json())
            {
                "path": "test_fic/",
                ...

        """
        return json.dumps(
            self.__summary, indent=4, ensure_ascii=False)

    def __find_duplicate(self) -> None:
        count_size: Counter[int | None] = Counter(
            cur_file.size for cur_file in self.__files)
        file_redundant_size: deque[MyFile] = deque([
            cur_file.get_hash() for cur_file in self.__files
            if count_size[cur_file.size] >= 2])
        count_hash: Counter[str | None] = Counter(
            cur_file.hash for cur_file in file_redundant_size)
        self.__hash = deque([
            [file for file in file_redundant_size if file.hash == cur_hash]
            for cur_hash, count in count_hash.items() if count >= 2])

    def __get_files(self) -> None:
        self.__files = deque([
            MyFile.get_size(os.path.join(base, filename))
            for base, dirs, filenames in os.walk(self.__path)
            for filename in filenames
            if os.path.basename(filename) not in [".DS_Store"]])

    def __gen_details(self) -> None:
        self.__summary = {
            "path": self.__path,
            "duplicate": {
                cur_hash[0].hash: [cur_file.path for cur_file in cur_hash]
                for cur_hash in self.__hash},
            "files": [cur_file.path for cur_file in self.__files]
            }


# ------------------------------------------------------------------------------
# Main function / Interface: check (args/environment) and call fix_report
# ------------------------------------------------------------------------------
def check_python() -> bool:
    """Check python version.

    This function check Python version, log the result and return a status
    True/False.

    Returns:
        True if successful, False otherwise.

    Examples:
        >>> check_python()
        True

    """
    # Python __version__
    current_version: tuple[int, int, int] = sys.version_info[:3]
    if current_version < CHK_PYT_MIN:
        logger.error(
            LOG_MSG.python.error, ".".join(map(str, current_version)))
        return False
    logger.info(
        LOG_MSG.python.info, ".".join(map(str, current_version)))
    logger.debug(LOG_MSG.python.debug, sys.version)
    return True


def define_logfile() -> None:
    """Define the logfile.

    This function set up the log to push log events in the report file.

    """
    log_formatter = logging.Formatter(LOG_SETUP.file_format)
    file_handler = logging.FileHandler(LOG_SETUP.log_file)
    file_handler.setFormatter(log_formatter)
    logger.addHandler(file_handler)
    logger.info(LOG_MSG.logfile.info, LOG_SETUP.log_file)


def check_arg(args: Namespace) -> bool:
    """Check user's arguments.

    This function check user's arguments, log info/error and return a status
    True/False.

    Args:
      args: Namespace.

    Returns:
        True if successful, False otherwise.

    Examples:
        >>> myargs = Namespace(path='/etc/')
        >>> check_arg(myargs)
        True

    """
    logger.debug(LOG_MSG.args.debug, args)

    if not os.path.isdir(args.path):
        logger.error(LOG_MSG.path.error, args.path)
        return False

    logger.info(LOG_MSG.path.info, args.path)

    return True


def dump_result(data: str) -> bool:
    """Dump the result in a JSON file.

    This function dump the JSON, log info/error and return a status True/False.

    Args:
      data: JSON str.

    Returns:
        True if successful, False otherwise.

    """
    try:
        with open(LOG_SETUP.json_dump, encoding=LOG_SETUP.encoding,
                  mode='w') as file:
            file.write(data)
    except (IOError, FileExistsError):
        logger.error(LOG_MSG.dump.error)
        logger.debug(LOG_MSG.dump.debug, exc_info=True)
        return False
    logger.info(LOG_MSG.dump.info, LOG_SETUP.json_dump)
    return True


def main() -> ExitStatus:
    """Define the main function.

    Returns:
        int: exit value

    """
    time_start = perf_counter()
    parser = get_argparser()
    args = parser.parse_args()

    if args.debug:
        logger.setLevel(logging.DEBUG)
    if args.logfile:
        define_logfile()
    if not check_python():
        return ExitStatus.EX_CONFIG
    if not check_arg(args):
        return ExitStatus.EX_USAGE

    detect_duplicate = DetectDuplicate(os.path.abspath(args.path))
    time_stop = perf_counter()
    logger.info(LOG_MSG.result.info, detect_duplicate)

    if args.dump and not dump_result(detect_duplicate.get_json()):
        return ExitStatus.EX_CANTCREAT

    logger.info(LOG_MSG.num_of_files.info, detect_duplicate.num_of_files)
    logger.info(LOG_MSG.elapse_time.info, round(time_stop-time_start, 2))
    return ExitStatus.EX_OK


if __name__ == '__main__':
    sys.exit(main())
