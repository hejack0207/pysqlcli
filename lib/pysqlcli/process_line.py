import sys
import os
import csv
import click
import io

class Processor(object):
    '''Class for processing the lines'''

    def __init__(self, database):
        '''Constructor'''
        self._database = database
        self._printer = Printer()
        # construct the commands list
        # The extructure is:
        # a list where each elements is a tuple containing
        # a string for comparing, the help string to print
        # and the function to execute.
        # All the functions recieves as args a line
        self._commands = [
            ('\\h',   '\\h:            Prints this help', self._do_help),
            ('\\d',   ('\\d:            Lists all tables\n'
            '\\d <table>:    Describes a table'),
            self._do_describe),
            ('\\c', ('\\c:            desactivates csv output\n'
            '\\c <filename>: Activates csv output'), self._do_csv),
            ('\\q',   '\\q:            Exits the program', self._do_quit),
            ('',      '<SQL command>: Executes SQL', None),
        ]


    def get_commands(self):
        '''Returns a dict with internal commands

        The estructure is a dict, where each element has a field indicating if
        the commands receives parameters'''

        comms = dict()
        for elem in self._commands:
            if elem[0]:
                if elem[0] == '\\d':
                    comms['\\d'] = 'table'
                elif elem[0] == '\\c':
                    comms['\\c'] = 'filename'
                else:
                    comms[elem[0]] = None
        return comms


    def _print_help(self):
        '''Prints commands help'''
        for line in self._commands:
            print >> sys.stderr, line[1]


    def _do_help(self, line):
        '''Prints the help'''

        command = line.split()

        if len(command) != 1:
            print >> sys.stderr, ('Invalid number of arguments,'
            'use \\h for help')
            return
        self._print_help()


    def _do_quit(self, line):
        '''Function to exit the line processor'''

        # A cheap trick to exit
        raise EOFError


    def _do_describe(self, line):
        '''Execute the describe operation'''

        command = line.split()
        if len(command) > 2:
            print >> sys.stderr, ('Invalid number of arguments,'
            'use \\h for help')
            return
        if len(command) == 1:
            return self._database.run_list_tables()
        elif len(command) == 2:
            return self._database.run_describe(command[1])


    def _do_csv(self, line):
        '''Execute the csv operation'''

        command = line.split()
        if len(command) > 2:
            print >> sys.stderr, ('Invalid number of arguments,'
            'use \\h for help')
            return
        if len(command) == 1:
            return self._printer.deactivate_csv()
        elif len(command) == 2:
            return self._printer.activate_csv(command[1])


    def process_line(self, line_readed):
        '''Process the line accordingly'''

        line = line_readed.strip()
        if not line:
            # Empty line
            return
        if line.startswith('\\'):
            # its a command
            command = line.split()
            for comm in self._commands:
                if comm[0] == command[0]:
                    # Command match, run associated function
                    rset = comm[2](line)
                    break
                if comm[0] == '':
                    # No command match, we reach SQL
                    print >> sys.stderr, 'Unknown command, use \\h for help'
                    rset = None
                    break
        else:
            # SQL
            rset = self._database.execute_query(line)
        if rset:
            self._printer.print_result_set(rset)


    def close(self):
        '''Close csv file'''

        # close csv file
        if self._printer.csv_mode:
            self._printer.deactivate_csv()


class Printer(object):
    '''Class for printing the result sets'''

    def __init__(self):
        '''Constructor, sets the csv output option to false'''

        self.csv_mode = False
        self._file = None


    def deactivate_csv(self):
        '''Deactivate csv mode and close the file opened'''

        if self.csv_mode:
            self._file.close()
            self.csv_mode = False
            print >> sys.stderr, 'CSV output deactivated'


    def activate_csv(self, filename):
        '''Activate the csv mode'''

        if not self.csv_mode:
            try:
                self._file = open(filename, 'wb')
                self.csv_mode = True
                print >> sys.stderr, 'CSV output activated'
            except IOError, exc:
                print >> sys.stderr, 'There was a problem activating csv mode'
                print >> sys.stderr, exc


    def print_result_set(self, rset):
        '''Prints the result set'''

        max_lengths = list()
        headers = list()
        rows = list()
        null = 'NULL'
        # Get the max length of each field and initialize the headers and
        # rows list
        for fields in rset.description:
            headers.append(fields[0])
            max_lengths.append(len(fields[0]))
        for row in rset:
            rows.append(row)
            for idx, elem in enumerate(row):
                if elem is None:
                    if len(null) > max_lengths[idx]:
                        max_lengths[idx] = len(null)
                else:
                    elem = str(elem)
                    if len(elem) > max_lengths[idx]:
                        max_lengths[idx] = len(elem)
        # call the apropiate function
        if self.csv_mode:
            self._print_to_csv(headers, rows)
        else:
            #self._print_to_stdout(max_lengths, headers, rows)
            self._print_csv_to_stdout(headers, rows)


    def _print_to_csv(self, headers, rows):
        '''Prints the result set to a csv file'''

        writer = csv.writer(self._file)
        writer.writerow(headers)
        writer.writerows(rows)
        writer.writerow('')


    def _print_csv_to_stdout(self, headers, rows):
        '''Prints the result set to stdout'''

        output = io.BytesIO()
        #output = io.StringIO()
        #output.encoding = 'utf-8'
        cw = csv.writer(output)

        cw.writerow(headers)
        cw.writerows(rows)
        #writer.writerow('(%d rows)' % len(rows) + '\n')

        #click.echo_via_pager(output.getvalue().encode('utf-8').strip('\r\n'))
        click.echo_via_pager(output.getvalue().strip('\r\n'))
        #print output.getvalue().strip('\r\n')

    def _print_to_stdout(self, max_lengths, headers, rows):
        '''Prints the result set to stdout'''

        nfields = len(max_lengths)
        # build and print header
        header = self._build_string(' ', ' | ', '',
        *[field.ljust(max_lengths[idx]) for idx, field in enumerate(headers)])
        output = ''
        output += header + '\n'
        # build and print separator
        sep = self._build_string('', '+', '',
            *['-' * (max_lengths[idx] + 2) for idx in xrange(nfields)])
        output += sep + '\n'
        # build and print fields
        for elem in rows:
            row = self._build_string(' ', ' | ', '',
            *[self._normalize(field).ljust(max_lengths[idx]) for idx, field in
            enumerate(elem)])
            output += row + '\n'
        # num of rows affected
        output += '(%d rows)' % len(rows) + '\n'
        print output


    def _normalize(self, data):
        '''Normalize data for printing'''

        null = 'NULL'
        if data is None:
            return str(null)
        else:
            return str(data)


    def _build_string(self, start_token, sep_token, end_token, *strings):
        '''Returns a string starting with start_token followed by string
        separator and finalized by end_token'''

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


