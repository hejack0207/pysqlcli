#!/usr/bin/env python
'''
    A substitute of Ora** SQL client that doesn't s*x
    Author: Alejandro E. Brito Monedero
'''

import readline
import sys
import os
import atexit
import csv

from db_op import Database

def print_usage():
    '''Prints command usage. =( I can't use argparse'''

    # I miss argparse
    print >> sys.stderr, ('Usage: %s <oracle connection string (DSN)>' %
    sys.argv[0])


def io_loop(processor):
    '''Prompt reading loop'''

    prompt = 'pysqlcli> '
    while True:
        try:
            line = raw_input(prompt)
            processor.process_line(line)
        except(EOFError, KeyboardInterrupt):
            # Old schoold exception handling, dated python =(
            # cosmetic ending
            processor.close()
            print
            break


def _main():
    '''Main function'''

    if len(sys.argv) != 2:
        print_usage()
        sys.exit(1)
    dsn = sys.argv[1]
    database = Database(dsn)
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
    processor = Processor(database)
    db_completer = DBcompleter(database, processor.get_commands())
    readline.set_completer(db_completer.complete)
    io_loop(processor)
    database.close()


if __name__ == '__main__':
    _main()
