import readline
import os

class DBcompleter(object):
    '''Class for the autocompletion'''

    def __init__(self, database, commands_dict):
        '''Constructor'''

        self._database = database
        self._commands_dict = commands_dict
        self._commands = [key for key in self._commands_dict]
        self._sql_opers_head = ('SELECT',)
        self._sql_pretable = ('FROM', 'JOIN')
        self._sql_prefield = ('WHERE',)


    def _get_tables(self, text, state):
        '''Give the posible table alternatives'''

        if state == 0:
            # cache tables
            rset = self._database.run_list_tables()
            self._tables = [row[0] for row in rset]
        return [table + ' ' for table in self._tables if
        table.startswith(text.upper())]


    def _get_fields(self, tokens, text, state):
        ''' Give the posible table.field alternatives'''

        if state == 0:
            # cache tables and fields
            # first get all the tables written, so we can run the describe
            # then with the table and its fields, build a dictionary where
            # the keys are the tables and the data is a list of tables fields
            self._table_fields = dict()
            pre_table_readed = False
            for elem in tokens:
                if pre_table_readed:
                    # this must be a table, run describe and store fields
                    if elem.upper() in self._table_fields:
                        # It has been processed before, skip it
                        continue
                    rset = self._database.run_describe(elem.upper())
                    self._table_fields[elem.upper()] = [row[0] for row in rset]
                    pre_table_readed = False
                    continue
                if elem.upper() in self._sql_pretable:
                    pre_table_readed = True
        # Need to check if the text has the table already concatenated with a
        # dot or not
        parts = text.split('.')
        if len(parts) < 2:
            # We can't give alternatives to the field yet, so we only give the
            # table names
            return [table + '.' for table in self._table_fields if
            table.startswith(parts[0].upper())]
        if len(parts) == 2:
            # We have a table and a part of a field or a field, try to
            # give alternatives
            if parts[0].upper() not in self._table_fields:
                # This table has not been metioned before
                return list()
            return [parts[0].upper() + '.' + field + ' ' for field in
            self._table_fields[parts[0].upper()] if
            field.startswith(parts[1].upper())]
        return list()


    def _complete_command_args(self, command, text, state):
        '''Given a command returns the valid command args'''

        option = self._commands_dict.get(command, None)
        if not option:
            # Nothing to complete
            return list()
        if option == 'table':
            return self._get_tables(text, state)
        # It has an option, but I don't know how to autocomplete it
        return list()


    def _complete_command(self, text, state):
        '''Give the command autocompletion alternatives'''

        buff = readline.get_line_buffer().lstrip()
        tokens = buff.split()
        if len(tokens) == 1:
            if tokens[0] == '\\':
                # Handle this special case that confuses readline
                # Return the commands without the blackslash
                return [elem[1:] + ' ' for elem in self._commands]
            if tokens[0][1:] == text:
                # Check if we can continue autocompleting
                # Remember that readline swallows the \
                return [elem[1:] + ' ' for elem in self._commands if
                elem.startswith(tokens[0])]
            return self._complete_command_args(tokens[0], text, state)
        if (len(tokens) == 2 and not text) or len(tokens) > 2:
            # Don't complete options with more than 2 args
            # or that have two tokens and the text is empty
            return list()
        return self._complete_command_args(tokens[0], text, state)


    def _sql_complete(self, text, state):
        '''Give the sql autocompletion alternatives'''
        # Autocomplete first part, after from table, after join table after
        # where field
        buff = readline.get_line_buffer().lstrip()
        tokens = buff.split()
        if len(tokens) == 1:
            # Complete first part of the command
            if not text:
                # check if we are still autocompleting the first token
                # if we are not text is empty then there are no options
                return list()
            return [elem + ' ' for elem in self._sql_opers_head if
            elem.startswith(text.upper())]
        # there are more than one token, check if we can autocomplete the
        # tables or table fields
        # Get the previous token for checking if we need to autocomplete
        if text:
            previous = tokens[-2].upper()
        else:
            previous = tokens[-1].upper()
        if previous in self._sql_pretable:
            # Autocomplete the table names
            return self._get_tables(text, state)
        if previous in self._sql_prefield:
            # Autocomplete the field name
            return self._get_fields(tokens, text, state)
        return list()


    def complete(self, text, state):
        '''The autocompletion function that calls readline'''

        buff = readline.get_line_buffer().lstrip()
        if not buff:
            # empty, give all the options
            options = [comm + ' ' for comm in self._commands]
            options.extend([oper + ' ' for oper in self._sql_opers_head])
        else:
            if buff.startswith('\\'):
                # Command
                options = self._complete_command(text, state)
            else:
                # SQL
                options = self._sql_complete(text, state)
        options.append(None)
        return options[state]


