import cx_Oracle
import sys
import os

class Database(object):
    '''Class to handle the database methods'''

    def __init__(self, dsn):
        '''Constructor, it opens the connection with the database'''

        self._dsn = dsn
        self._user = self._get_dbuser()
        #os.environ["NLS_LANG"]="SIMPLIFIED CHINESE_CHINA.UTF8"
        os.environ["NLS_LANG"]=".UTF8"
        self._connection = cx_Oracle.Connection(self._dsn)
        self._cursor = self._connection.cursor()


    def _get_dbuser(self):
        '''Extracts the user from the dsn string'''

        user = self._dsn.split('/')[0]
        return user


    def close(self):
        '''Closes the cursor and the connection'''

        self._cursor.close()
        self._connection.close()


    def run_describe(self, table):
        '''Run the describe query given a table returning a result set'''

        # The ugly query to emulate DESCRIBE of sql*plus Thx CERN
        describe = ("SELECT atc.column_name, "
            "CASE atc.nullable WHEN 'Y' THEN 'NULL' ELSE 'NOT NULL' "
            "END \"Null?\", atc.data_type || CASE atc.data_type WHEN 'DATE' "
            "THEN '' ELSE '(' || CASE atc.data_type WHEN 'NUMBER' THEN "
                "TO_CHAR(atc.data_precision) || CASE atc.data_scale WHEN 0 "
                "THEN '' ELSE ',' || TO_CHAR(atc.data_scale) END "
                "ELSE TO_CHAR(atc.data_length) END END || CASE atc.data_type "
                "WHEN 'DATE' THEN '' ELSE ')' END data_type "
            "FROM all_tab_columns atc "
            "WHERE atc.table_name = '%s' AND atc.owner = '%s' "
            "ORDER BY atc.column_id")
        rset = self.execute_query(describe % (table.upper(),
        self._user.upper()))
        return rset


    def run_list_tables(self):
        '''Run the a query that shows all the tables and returns a result set'''

        list_all = "SELECT table_name FROM user_tables"
        rset = self.execute_query(list_all)
        return rset


    def execute_query(self, query):
        '''Executes the given query and returns the result set, None if error'''

        try:
            rset = self._cursor.execute(query)
            return rset
        except cx_Oracle.DatabaseError, exc:
            error, = exc.args
            print >> sys.stderr, "Oracle-Error-Code: %s" % error.code
            print >> sys.stderr, "Oracle-Error-Message: %s" % error.message
        # reached after an exception. This is too C, better raise and Exception
        return None


