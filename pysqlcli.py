#!/usr/bin/env python
'''
    A substitute of Ora** SQL client that doesn't s*x
    Author: Alejandro E. Brito Monedero
'''

import readline
import sys
import cx_Oracle
import os
import atexit


def _print_to_stderr(data):
    '''Prints data to stderr'''

    stdout = sys.stdout
    sys.stdout = sys.stderr

    print(data)

    sys.stdout = stdout


def usage():
    '''Prints command usage. =( I can't use argparse'''

    _print_to_stderr('Usage: %s <oracle connection string (DSN)>' % sys.argv[0])


def io_loop(cursor):
    '''Prompt reading loop'''

    prompt = 'pysqlcli> '
    while True:
        try:
            line = raw_input(prompt)
            execute_query(cursor, line)
        except(EOFError, KeyboardInterrupt):
            # Old schoold exception handling, dated python =(
            # cosmetic ending
            print
            break


def execute_query(cursor, query):
    '''Executes the given query'''

    try:
        rset = cursor.execute(query)
        print_result_set(rset)
    except cx_Oracle.DatabaseError, exc:
        error, = exc.args
        _print_to_stderr("Oracle-Error-Code: %s" % error.code)
        _print_to_stderr("Oracle-Error-Message: %s" % error.message)


def print_result_set(rset):
    '''Prints the result set'''

    nfields = len(rset.description)
    max_lengths = list()
    headers = list()
    rows = list()

    # TODO: needs some improvement, read about print and stuff

    # Get the max length of each field and initialize the headers and rows lst
    for f in rset.description:
        headers.append(f[0])
        max_lengths.append(len(f[0]))

    for row in rset:
        rows.append(row)
        for i, e in enumerate(row):
            if e is not None and len(e) > max_lengths[i]:
                max_lengths[i] = len(e)

    # print header
    for i, h in enumerate(headers):
        sc = ''
        # First field doesn't starts with a |
        if i != 0:
            sc = '|'
        print '%s %s %s' % (sc, h, ' ' * (max_lengths[i] - len(h))),
    print

    # build and print separator
    sep = ''
    for i in xrange(nfields):
        if i != 0:
            sep += '+'
        sep += '-' * (max_lengths[i] + 3)
    print sep

    # print fields
    for row in rows:
        for i, e in enumerate(row):
            sc = ''
            # First field doesn't starts with a |
            if i != 0:
                sc = '|'
            print '%s %s %s' % (sc, e, ' ' * (max_lengths[i] - len(e))),
        print

    # num of rows affected
    print '(%d rows)' % rset.rowcount


def _main():
    '''Main function'''

    if len(sys.argv) != 2:
        usage()
        sys.exit(1)

    dsn = sys.argv[1]
    connection = cx_Oracle.Connection(dsn)
    cursor = connection.cursor()

    # Enables tab completion and the history magic
    readline.parse_and_bind("tab: complete")
    # load the history file if it exists
    histfile = os.path.join(os.path.expanduser("~"), ".pysqlcli_history")
    try:
        readline.read_history_file(histfile)
    except IOError:
        pass
    # register the function to save the history at exit. THX python examples
    atexit.register(readline.write_history_file, histfile)

    io_loop(cursor)

    cursor.close()
    connection.close()


if __name__ == '__main__':
    _main()
