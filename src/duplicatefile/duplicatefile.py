#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
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
from argparse import Namespace, ArgumentParser, RawDescriptionHelpFormatter, \
    _ArgumentGroup
from collections import Counter, deque
from logging import Logger
from time import perf_counter
from typing import Type, Optional, Union, NamedTuple, Any, BinaryIO

from xxhash import xxh3_64

IMPORT_DONE: bool = False
IMPORT_EXCEPTION: ModuleNotFoundError
try:
    import xxhash
    from rich.logging import RichHandler
    from rich_argparse import RawDescriptionRichHelpFormatter
    IMPORT_DONE = True
except ModuleNotFoundError as e:
    IMPORT_EXCEPTION = e
    IMPORT_DONE = False

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
__version__: str = '0.1.0'
__author__: str = 'Ko4la'

# exit values
EX_OK: int = getattr(os, 'EX_OK', 0)
EX_USAGE: int = getattr(os, 'EX_USAGE', 64)
EX_CONFIG: int = getattr(os, 'EX_USAGE', 78)
EX_CANTCREAT: int = getattr(os, 'EX_USAGE', 73)

# python
CHK_PYT_MIN: tuple[int, int, int] = (3, 7, 0)
ROOT_DIR: str = os.path.abspath(os.path.dirname(__file__))
PID: int = os.getpid()


# logging
class LoggingSetup(NamedTuple):
    """Logging Parameters

    Examples:
    >>> my_setup = LoggingSetup()
    >>> my_setup.default_level
    'INFO'

    """
    default_level: str = 'INFO'
    log_file: str = f'{ROOT_DIR}/report.log'
    default_format: str = '%(message)s'
    simple_format: str = '%(levelname)s %(message)s'
    file_format: str = '%(asctime)s - %(levelname)s - %(message)s'
    json_dump: str = f'{ROOT_DIR}/dump_{PID}.json'
    encoding: str = 'utf-8'


class LoggingMSG(NamedTuple):
    """Messages with different sev

    Examples:
    >>> logfile = LoggingMSG(info="Log file used: %s")
    >>> logfile.info
    'Log file used: %s'

    """
    info: str = ""
    error: str = ""
    debug: str = ""


class LoggingMSGCollection(NamedTuple):
    """All logging messages

    Examples:
        >>> log_msg = LoggingMSGCollection()
        >>> log_msg.logfile.info
        'Log file used: %s'

    """
    logfile: LoggingMSG = LoggingMSG(
        info="Log file used: %s")
    args: LoggingMSG = LoggingMSG(
        debug="Arguments: %s")
    path: LoggingMSG = LoggingMSG(
        info="Path : '%s'",
        error="Path is not a folder : %s",
        debug="")
    python: LoggingMSG = LoggingMSG(
        info="Python version is supported: %s",
        error="Python version is not supported: %s",
        debug="Python: %s")
    python_import: LoggingMSG = LoggingMSG(
        info="Python modules imported.",
        error=f"Install modules. Use ./{os.path.basename(__file__)} --help",
        debug="IMPORT MSG: %s")
    dump: LoggingMSG = LoggingMSG(
        info="New report has been created: %s",
        error="New report has not been created.",
        debug="New report cannot be saved:")
    result: LoggingMSG = LoggingMSG(
        info="Result:\n%s")
    num_of_files: LoggingMSG = LoggingMSG(
        info="Number of files: %s")
    elapse_time: LoggingMSG = LoggingMSG(
        info="Elapse time: %s s")


LOGGING_SETUP: LoggingSetup = LoggingSetup()
LOGGING_MSG: LoggingMSGCollection = LoggingMSGCollection()
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
ARG_HIGHLIGHT: list = [
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
current_handlers: list[
    Union[logging.StreamHandler, RichHandler]] = [logging.StreamHandler()]
current_format: str = LOGGING_SETUP.simple_format
if IMPORT_DONE:
    current_handlers = [RichHandler(rich_tracebacks=True, show_time=False)]
    current_format = LOGGING_SETUP.default_format

logging.basicConfig(
    level=LOGGING_SETUP.default_level,
    format=current_format,
    handlers=current_handlers
)

logger: Logger = logging.getLogger(__name__)


# ------------------------------------------------------------------------------
# arguments and options
# ------------------------------------------------------------------------------
def get_argparser() -> ArgumentParser:
    """
    This function describe the argument parser and return it.

    Returns:
        ArgumentParser

    Examples:
    >>> a = get_argparser()
    >>> type(a)
    <class 'argparse.ArgumentParser'>

    >>> a.print_help()
    USAGE: pytest [-h] [--version] [--debug] [--logfile] [--dump] -p PATH
    ...

    """
    cur_formatter: Type[
        Union[
            RawDescriptionHelpFormatter,
            RawDescriptionRichHelpFormatter]] = RawDescriptionHelpFormatter
    if IMPORT_DONE:
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
    required_argument: _ArgumentGroup = parser.add_argument_group(
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
    """This class describe a file with a NamedTuple
    @classmethod is used to init the objects correctly.

    Notes:
        The objective is to define a file with only one NamedTuple.
        The NamedTuple will be created by the get_size function to define the
        path and size.
        Hash information consumes resources, and it will calculate later with
        get_hash function to create a new NamedTuple.

    """
    path: str
    size: Optional[int] = None
    hash: Optional[str] = None

    @classmethod
    def get_size(cls, path: str) -> MyFile:
        """ This function create the MyFile object with the file's path,
        file's size is initialized by default and hash is None by default.
        The path is not tested here, because we use os.walk to get the file
        list.

        Args:
            path: The file's path.

        Returns:
            MyFile

        Examples:
            >>> a = MyFile.get_size('test_fic/doc.txt')
            >>> a
            MyFile(path='test_fic/doc.txt', size=544)

        """
        return cls(path, os.stat(path).st_size)

    def get_hash(self, blocksize: int = 65536) -> MyFile:
        """ This function calculate the file's hash and create a new MyFile
        object with a MyFile object.

        Args:
          blocksize:  blocksize used to read the file. (Default value = 65536)

        Returns:
            MyFile

            >>> a = MyFile.get_size('test_fic/doc.txt')
            >>> b = a.get_hash()
            >>> b
            MyFile(path='test_fic/doc.txt', size=544, hash='a5cd732df22bfdbd')

        """
        hasher: xxh3_64 = xxhash.xxh64()
        file: BinaryIO
        with open(self.path, 'rb') as file:
            buf: bytes = file.read(blocksize)
            while len(buf) > 0:
                hasher.update(buf)
                buf = file.read(blocksize)
        # Get the hashed representation
        return self._replace(hash=hasher.hexdigest())

    def __repr__(self) -> str:
        _repr: str = f"path='{self.path}', size={self.size}"
        if self.hash is not None:
            _repr = f"{_repr}, hash='{self.hash}'"
        return f'{self.__class__.__name__}({_repr})'


class DetectDuplicate:
    """Class to organize and find duplicate files"""
    __path: str
    __files: deque[MyFile]
    __hash: deque[list[MyFile]]
    __summary: dict[str, Any]

    def __init__(self, path: str) -> None:
        self.__path = path
        self.__get_files()
        self.__find_duplicate()
        self.__gen_details()

    def __str__(self) -> str:
        result = ""
        for cur_hash in self.__hash:
            result = "%s\n- Same files (%s):\n -> '%s'" % (
                result,
                cur_hash[0].hash,
                "'\n -> '".join([cur_file.path for cur_file in cur_hash]))
        return result

    @property
    def num_of_files(self) -> int:
        """ This function return the number of files.

        Returns:
            int: Number of files.

        Examples:
            >>> a = DetectDuplicate('test_fic/')
            >>> a.num_of_files
            5

        """
        return len(self.__files)

    def get_json(self) -> str:
        """This function returns the result (JSON format).

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
    """This function check Python version, log the result and return a status
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
            LOGGING_MSG.python.error, ".".join(map(str, current_version)))
        return False
    logger.info(
        LOGGING_MSG.python.info, ".".join(map(str, current_version)))
    logger.debug(LOGGING_MSG.python.debug, sys.version)
    return True


def check_import() -> bool:
    """This function check modules import, log the result and return a status
    True/False.

    Returns:
        True if successful, False otherwise.

    Examples:
        >>> check_import()
        True

    """
    if IMPORT_DONE:
        logger.info(LOGGING_MSG.python_import.info)
        return True
    logger.error(LOGGING_MSG.python_import.error)
    logger.debug(LOGGING_MSG.python_import.debug, IMPORT_EXCEPTION)
    return False


def define_logfile() -> None:
    """
    This function set up the log to push log events in the report file.
    """
    log_formatter = logging.Formatter(LOGGING_SETUP.file_format)
    file_handler = logging.FileHandler(LOGGING_SETUP.log_file)
    file_handler.setFormatter(log_formatter)
    logger.addHandler(file_handler)
    logger.info(LOGGING_MSG.logfile.info, LOGGING_SETUP.log_file)


def check_arg(args: Namespace) -> bool:
    """This function check user's arguments, log info/error and return a status
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
    logger.debug(LOGGING_MSG.args.debug, args)

    if not os.path.isdir(args.path):
        logger.error(LOGGING_MSG.path.error, args.path)
        return False

    logger.info(LOGGING_MSG.path.info, args.path)

    return True


def dump_result(data: str) -> bool:
    """This function dump the result in a JSON file, log info/error and
    return a status True/False.

    Args:
      data: JSON str.

    Returns:
        True if successful, False otherwise.

    """
    try:
        with open(LOGGING_SETUP.json_dump, encoding=LOGGING_SETUP.encoding,
                  mode='w') as file:
            file.write(data)
    except (IOError, FileExistsError):
        logger.error(LOGGING_MSG.dump.error)
        logger.debug(LOGGING_MSG.dump.debug, exc_info=True)
        return False
    logger.info(LOGGING_MSG.dump.info, LOGGING_SETUP.json_dump)
    return True


def main() -> int:
    """
    This function is the main function.

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
    if not check_python() or not check_import():
        return EX_CONFIG
    if not check_arg(args):
        return EX_USAGE

    detect_duplicate = DetectDuplicate(os.path.abspath(args.path))
    time_stop = perf_counter()
    logger.info(LOGGING_MSG.result.info, detect_duplicate)

    if args.dump and not dump_result(detect_duplicate.get_json()):
        return EX_CANTCREAT

    logger.info(LOGGING_MSG.num_of_files.info, detect_duplicate.num_of_files)
    logger.info(LOGGING_MSG.elapse_time.info, round(time_stop-time_start, 2))
    return EX_OK


if __name__ == '__main__':
    sys.exit(main())
