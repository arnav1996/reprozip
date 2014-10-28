# Copyright (C) 2014 New York University
# This file is part of ReproZip which is released under the Revised BSD License
# See file LICENSE for full license details.

"""Entry point for the reprozip utility.

This contains :func:`~reprozip.main.main`, which is the entry point declared to
setuptools. It is also callable directly.

It dispatchs to other routines, or handles the testrun command.
"""

from __future__ import unicode_literals

import argparse
import codecs
import locale
import logging
import os
from rpaths import Path
import sqlite3
import sys

from reprozip import __version__ as reprozip_version
from reprozip import _pytracer
from reprozip.common import setup_logging, \
    setup_usage_report, submit_usage_report, record_usage_report
import reprozip.pack
import reprozip.tracer.trace
from reprozip.utils import PY3


def print_db(database):
    """Prints out database content.
    """
    if PY3:
        # On PY3, connect() only accepts unicode
        conn = sqlite3.connect(str(database))
    else:
        conn = sqlite3.connect(database.path)
    conn.row_factory = sqlite3.Row

    cur = conn.cursor()
    processes = cur.execute(
            '''
            SELECT id, parent, timestamp, exitcode
            FROM processes;
            ''')
    print("\nProcesses:")
    header = "+------+--------+-------+------------------+"
    print(header)
    print("|  id  | parent |  exit |     timestamp    |")
    print(header)
    for r_id, r_parent, r_timestamp, r_exit in processes:
        f_id = "{0: 5d} ".format(r_id)
        if r_parent is not None:
            f_parent = "{0: 7d} ".format(r_parent)
        else:
            f_parent = "        "
        if r_exit & 0x0100:
            f_exit = " sig{0: <2d} ".format(r_exit)
        else:
            f_exit = "    {0: <2d} ".format(r_exit)
        f_timestamp = "{0: 17d} ".format(r_timestamp)
        print('|'.join(('', f_id, f_parent, f_exit, f_timestamp, '')))
        print(header)
    cur.close()

    cur = conn.cursor()
    processes = cur.execute(
            '''
            SELECT id, name, timestamp, process, argv
            FROM executed_files;
            ''')
    print("\nExecuted files:")
    header = ("+--------+------------------+---------+------------------------"
              "---------------+")
    print(header)
    print("|   id   |     timestamp    | process | name and argv              "
          "           |")
    print(header)
    for r_id, r_name, r_timestamp, r_process, r_argv in processes:
        f_id = "{0: 7d} ".format(r_id)
        f_timestamp = "{0: 17d} ".format(r_timestamp)
        f_proc = "{0: 8d} ".format(r_process)
        argv = r_argv.split('\0')
        if not argv[-1]:
            argv = argv[:-1]
        cmdline = ' '.join(repr(a) for a in argv)
        if argv[0] != os.path.basename(r_name):
            cmdline = "(%s) %s" % (r_name, cmdline)
        f_cmdline = " {0: <37s} ".format(cmdline)
        print('|'.join(('', f_id, f_timestamp, f_proc, f_cmdline, '')))
        print(header)
    cur.close()

    cur = conn.cursor()
    processes = cur.execute(
            '''
            SELECT id, name, timestamp, mode, process
            FROM opened_files;
            ''')
    print("\nFiles:")
    header = ("+--------+------------------+---------+------+-----------------"
              "---------------+")
    print(header)
    print("|   id   |     timestamp    | process | mode | name                "
          "           |")
    print(header)
    for r_id, r_name, r_timestamp, r_mode, r_process in processes:
        f_id = "{0: 7d} ".format(r_id)
        f_timestamp = "{0: 17d} ".format(r_timestamp)
        f_proc = "{0: 8d} ".format(r_process)
        f_mode = "{0: 5d} ".format(r_mode)
        f_name = " {0: <30s} ".format(r_name)
        print('|'.join(('', f_id, f_timestamp, f_proc, f_mode, f_name, '')))
        print(header)
    cur.close()

    conn.close()


def testrun(args):
    """testrun subcommand.

    Runs the command with the tracer using a temporary sqlite3 database, then
    reads it and dumps it out.

    Not really useful, except for debugging.
    """
    fd, database = Path.tempfile(prefix='reprozip_', suffix='.sqlite3')
    os.close(fd)
    try:
        if args.arg0 is not None:
            argv = [args.arg0] + args.cmdline[1:]
        else:
            argv = args.cmdline
        logging.debug("Starting tracer, binary=%r, argv=%r",
                      args.cmdline[0], argv)
        c = _pytracer.execute(args.cmdline[0], argv, database.path,
                              args.verbosity)
        print("\n\n-----------------------------------------------------------"
              "--------------------")
        print_db(database)
        if c != 0:
            if c & 0x0100:
                print("\nWarning: program appears to have been terminated by "
                      "signal %d" % (c & 0xFF))
            else:
                print("\nWarning: program exited with non-zero code %d" % c)
    finally:
        database.remove()


def trace(args):
    """trace subcommand.

    Simply calls reprozip.tracer.trace() with the arguments from argparse.
    """
    if args.arg0 is not None:
        argv = [args.arg0] + args.cmdline[1:]
    else:
        argv = args.cmdline
    reprozip.tracer.trace.trace(args.cmdline[0],
                                argv,
                                Path(args.dir),
                                args.append,
                                args.verbosity)
    reprozip.tracer.trace.write_configuration(Path(args.dir),
                                              args.identify_packages,
                                              overwrite=False)


def reset(args):
    """reset subcommand.

    Just regenerates the configuration (config.yml) from the trace
    (trace.sqlite3).
    """
    reprozip.tracer.trace.write_configuration(Path(args.dir),
                                              args.identify_packages,
                                              overwrite=True)


def pack(args):
    """pack subcommand.

    Reads in the configuration file and writes out a tarball.
    """
    target = Path(args.target)
    if not target.unicodename.lower().endswith('.rpz'):
        target = Path(target.path + '.rpz')
        logging.warning("Changing output filename to %s", target.unicodename)
    reprozip.pack.pack(target, Path(args.dir), args.identify_packages)


def main():
    """Entry point when called on the command-line.
    """
    # Locale
    locale.setlocale(locale.LC_ALL, '')

    # Encoding for output streams
    if str == bytes:  # PY2
        writer = codecs.getwriter(locale.getpreferredencoding())
        o_stdout, o_stderr = sys.stdout, sys.stderr
        sys.stdout = writer(sys.stdout)
        sys.stdout.buffer = o_stdout
        sys.stderr = writer(sys.stderr)
        sys.stderr.buffer = o_stderr

    # http://bugs.python.org/issue13676
    # This prevents reprozip from reading argv and envp arrays from trace
    if sys.version_info < (2, 7, 3):
        sys.stderr.write("Error: your version of Python, %s, is not "
                         "supported\nVersions before 2.7.3 are affected by "
                         "bug 13676 and will not work with ReproZip\n" %
                         sys.version.split(' ', 1)[0])
        sys.exit(1)

    # Parses command-line

    # General options
    options = argparse.ArgumentParser(add_help=False)
    options.add_argument('--version', action='version',
                         version="reprozip version %s" % reprozip_version)
    options.add_argument('-v', '--verbose', action='count', default=1,
                         dest='verbosity',
                         help="augments verbosity level")
    options.add_argument('-d', '--dir', default='.reprozip',
                         help="where to store database and configuration file "
                         "(default: ./.reprozip)")
    options.add_argument(
            '--dont-identify-packages', action='store_false', default=True,
            dest='identify_packages',
            help="do not try identify which package each file comes from")

    parser = argparse.ArgumentParser(
            description="reprozip is the ReproZip component responsible for "
                        "tracing and packing the execution of an experiment",
            epilog="Please report issues to reprozip-users@vgc.poly.edu",
            parents=[options])
    subparsers = parser.add_subparsers(title="commands", metavar='',
                                       dest='selected_command')

    # trace command
    parser_trace = subparsers.add_parser(
            'trace', parents=[options],
            help="Runs the program and writes out database and configuration "
            "file")
    parser_trace.add_argument(
            '-a',
            dest='arg0',
            help="argument 0 to program, if different from program path")
    parser_trace.add_argument(
            '-c', '--continue', action='store_true', dest='append',
            help="add to the previous run instead of replacing it")
    parser_trace.add_argument('cmdline', nargs=argparse.REMAINDER,
                              help="command-line to run under trace")
    parser_trace.set_defaults(func=trace)

    # testrun command
    parser_testrun = subparsers.add_parser(
            'testrun', parents=[options],
            help="Runs the program and writes out the database contents")
    parser_testrun.add_argument(
            '-a',
            dest='arg0',
            help="argument 0 to program, if different from program path")
    parser_testrun.add_argument('cmdline', nargs=argparse.REMAINDER)
    parser_testrun.set_defaults(func=testrun)

    # reset command
    parser_reset = subparsers.add_parser(
            'reset', parents=[options],
            help="Resets the configuration file")
    parser_reset.set_defaults(func=reset)

    # pack command
    parser_pack = subparsers.add_parser(
            'pack', parents=[options],
            help="Packs the experiment according to the current configuration")
    parser_pack.add_argument('target', nargs='?', default='experiment.rpz',
                             help="Destination file")
    parser_pack.set_defaults(func=pack)

    args = parser.parse_args()
    setup_logging('REPROZIP', args.verbosity)
    setup_usage_report('reprozip', reprozip_version)
    if 'cmdline' in args and not args.cmdline:
        parser.error("missing command-line")
    record_usage_report(command=args.selected_command)
    try:
        args.func(args)
    except Exception as e:
        submit_usage_report(result=type(e).__name__)
    else:
        submit_usage_report(result='success')
    sys.exit(0)


if __name__ == '__main__':
    main()
