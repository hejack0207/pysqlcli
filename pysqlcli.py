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

    # Yes, I know there is a shortcut but I don't like the C++ like syntax XD

    stdout = sys.stdout
    sys.stdout = sys.stderr
    print(data)
    sys.stdout = stdout


def usage():
    '''Prints command usage. =( I can't use argparse'''

    # I miss argparse
    _print_to_stderr('Usage: %s <oracle connection string (DSN)>' % sys.argv[0])


def build_string(start_token, sep_token, end_token, *strings):
    '''Returns a string starting with start_token followed by string separator
    and finalized by end_token'''

    n_strings = len(strings)
    val = start_token
    for idx, elem in enumerate(strings):
        val += elem
        # is this the last element?
        if idx + 1 == n_strings:
            val += end_token
        else:
            val += sep_token
    return val


def print_help():
    '''Print internal system help'''

    message = ('Usage:\n'
        'Prints this help:  \\h\n'
        'Lists all tables:  \\d\n'
        'Describes a table: \\d <table>\n'
        'Exits:             \\q\n'
        'Executes SQL:      <sql command>')

    _print_to_stderr(message)


def process_line(cursor, user, readed_line):
    '''Process the line accordingly'''

    num_args_err = "Invalid number of arguments, use \\h for help"

    line = readed_line.strip()

    if not line:
        # Empty line
        return

    if line.startswith('\\'):
        # its a command
        command = line.split()
        if command[0] == '\\h':
            if len(command) != 1:
                _print_to_stderr(num_args_err)
                return
            print_help()
            return
        elif command[0] == '\\d':
            if len(command) > 2:
                _print_to_stderr(num_args_err)
                return
            if len(command) == 1:
                rset = run_list_tables(cursor)
            elif len(command) == 2:
                rset = run_describe(cursor, user, command[1])
        elif command[0] == '\\q':
            # A cheap trick to exit
            raise EOFError
        else:
            _print_to_stderr("Unknown command, use \\h for help")
            return
    else:
        # SQL
        rset = execute_query(cursor, line)

    if rset:
        print_result_set(rset)


def io_loop(cursor, user):
    '''Prompt reading loop'''

    prompt = 'pysqlcli> '
    while True:
        try:
            line = raw_input(prompt)
            process_line(cursor, user, line)
        except(EOFError, KeyboardInterrupt):
            # Old schoold exception handling, dated python =(
            # cosmetic ending
            print
            break


def execute_query(cursor, query):
    '''Executes the given query and returns the result set, None if error'''

    try:
        rset = cursor.execute(query)
        return rset
    except cx_Oracle.DatabaseError, exc:
        error, = exc.args
        _print_to_stderr("Oracle-Error-Code: %s" % error.code)
        _print_to_stderr("Oracle-Error-Message: %s" % error.message)

    # reached after an exception. TODO: excess of C style
    return None


def print_result_set(rset):
    '''Prints the result set'''

    nfields = len(rset.description)
    max_lengths = list()
    headers = list()
    rows = list()
    null = 'NULL'

    # TODO: needs some improvement, I must read about print and stuff

    # Get the max length of each field and initialize the headers and rows lst
    for f in rset.description:
        headers.append(f[0])
        max_lengths.append(len(f[0]))

    for row in rset:
        rows.append(row)
        for i, e in enumerate(row):
            if e is None:
                if len(null) > max_lengths[i]:
                    max_lengths[i] = len(null)
            else:
                e = str(e)
                if len(e) > max_lengths[i]:
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
            if e is None:
                e = null
            e = str(e)
            sc = ''
            # First field doesn't starts with a |
            if i != 0:
                sc = '|'
            print '%s %s %s' % (sc, e, ' ' * (max_lengths[i] - len(e))),
        print

    # num of rows affected
    print '(%d rows)' % rset.rowcount


def run_describe(cursor, user, table):
    """Run the describe query given an user and table returning a result set"""

    # The ugly query to emulate DESCRIBE of sql*plus Thx CERN
    describe = ("SELECT atc.column_name, "
        "CASE atc.nullable WHEN 'Y' THEN 'NULL' ELSE 'NOT NULL' END \"Null?\","
        "atc.data_type || CASE atc.data_type WHEN 'DATE' THEN '' ELSE '(' "
            "|| CASE atc.data_type WHEN 'NUMBER' THEN "
            "TO_CHAR(atc.data_precision) || CASE atc.data_scale WHEN 0 "
            "THEN '' ELSE ',' || TO_CHAR(atc.data_scale) END "
            "ELSE TO_CHAR(atc.data_length) END END || CASE atc.data_type "
            "WHEN 'DATE' THEN '' ELSE ')' END data_type "
        "FROM all_tab_columns atc "
        "WHERE atc.table_name = '%s' AND atc.owner = '%s' "
        "ORDER BY atc.column_id")

    rset = execute_query(cursor, describe % (table.upper(), user.upper()))
    return rset


def run_list_tables(cursor):
    """Run the a query that shows all the tables and returns a result set"""

    list_all = "SELECT table_name FROM user_tables"

    rset = execute_query(cursor, list_all)

    return rset


def get_dbuser(dsn):
    '''Extracts the user from the dsn string'''

    user = dsn.split('/')[0]

    return user


def _main():
    '''Main function'''

    if len(sys.argv) != 2:
        usage()
        sys.exit(1)

    dsn = sys.argv[1]
    connection = cx_Oracle.Connection(dsn)
    user = get_dbuser(dsn)
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

    io_loop(cursor, user)

    cursor.close()
    connection.close()


if __name__ == '__main__':
    _main()
