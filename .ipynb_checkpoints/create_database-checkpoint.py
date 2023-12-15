from __future__ import annotations

import os
import sqlite3
import pandas as pd
import numpy as np
import sql_queries as SQ
from traceback import print_exc as pe
from IPython.display import clear_output
import time
import glob

sqlite3.register_adapter(np.int64, lambda val: int(val))
sqlite3.register_adapter(np.int32, lambda val: int(val))

class MyDB:
    '''
    Reads in all .csv files in data/... as a Pandas dataframe and creates a SQLite3 database from a randomly sampled subset   of the dataframe (currently 5 bills per state)
    
    class parameters:
    
    add_data: add data to the database (default: bool = False)
    bills_drop: drop tBills table from legislation.db (default: bool = False)
    any_drop: if any tables is true, rebuild tables (default bool = False)
    input_lim: this parameter is currently out of use, since we are not creating a database directly with a single csv file. (default: int = None) 
    chunk_size: this parameter is currently out of use, since we are not creating a database directly with a single csv file. (default: int = None)
    
    '''
    def __init__(self,
                 add_data:bool = False,
                 table_type: str = None,
                 bills_drop: bool = False, 
                 any_drop: bool = False, 
                 input_lim: int = None, 
                 chunk_size: int = None
                ):
        
        self.path_data = os.path.join(os.path.dirname(__file__), 'data')
        self.path_db = os.path.join(self.path_data, 'legislation.db')
        self.add_data = add_data
        self.table_type = table_type
        self.bills_drop = bills_drop
        self.any_drop = any_drop
        self.input_lim = input_lim
        self.chunk_size = chunk_size
        
        self.__validate_inputs()

        if self.any_drop:
            self.build_tables()
            print("filling tables!")
            self.fill_tables()
        else:
            return
        
    def __validate_inputs(self):
        '''
        Validates the inputs passed to the class to ensure they will not cause errors.
        '''
        print('Validating Inputs...')

        if (self.add_data is False) and (self.table_type is not None):
            raise ValueError("'table_type' specified while 'add_data' is False")
      
        if (self.add_data is True) and (self.table_type is None):
            raise ValueError("Must specify 'table_type' while 'add_data' is True")
        
        if (self.any_drop is False) and (self.bills_drop is True):
            raise ValueError("Can't drop bills table while any_drop is set to False")
        
        clear_output(wait=True)
        print('Inputs Validated!')
        return
    
    def connect(self):
        ''' create connection objects to the sqlite3 database (legislation.db)'''
        self.conn = sqlite3.connect(self.path_db, isolation_level=None, check_same_thread=False)
        self.curs = self.conn.cursor()
        return 
    
    def close(self):
        'Close connection to legislation.db'
        self.conn.close()
        return
    
    def load_df(self):
        '''
        Reads in all of the .csv files in the data folder 
        and produces a single Pandas dataframe with all rows. 
        
        In this new dataframe, we add empty columns to log errors, text, and a datetime timestamp
        for when we attempt to retrieve bill texts using Tika.
        ''' 
        path = './data'
        csv_files = glob.glob(path + "/*.csv")

        # Read each CSV file into DataFrame
        # This creates a list of dataframes
        df_list = (pd.read_csv(file) for file in csv_files)

        # Concatenate all DataFrames
        df = pd.concat(df_list, ignore_index=True)
        
        df['error'] = np.nan
        df['content'] = np.nan
        df['processed_at'] = np.nan
   
        return df
    
    def build_tables(self):
        ''' 
        Builds tables in the SQLite database for bills 
        Conditional on drop conditions passed to the class
        '''
        clear_output(wait=True)
        print('Building Tables...')
        self.connect()
        self.curs.execute("PRAGMA foreign_keys=ON;")

        if self.any_drop:
            if self.bills_drop == False:
                if self.table_type.lower() == 'bills':
                        self.curs.execute("DROP TABLE IF EXISTS tBills;")
            if self.bills_drop:
                self.curs.execute("DROP TABLE IF EXISTS tBills;")
       
            if self.bills_drop:
                sql = SQ.SQL_FULL_BILLS_BUILD
                self.curs.execute(sql)

        self.close()

        clear_output(wait=True)
        print('tables built!')

        return True
    
    def get_tables(self):
        '''
        Returns the tBills table from the provided database as a Pandas dataframe
        '''
        self.connect()
        sql = 'SELECT * FROM sqlite_master WHERE type = "table"'
        self.curs = self.conn.execute(sql)
        results = self.curs.fetchall()
        print(results)
        self.close()
        return 
    
    def fill_tables(self):
        '''
        Fills the pre-built tables with the data from the dataframe created by the load_df method.
        
        After creating the concatenated dataframe, we subset the dataframe to only include rows where the url column (what Tika will use to retrieve texts) is not empty. Then we group the entries by state.

        For each row, the function checks if the bill already exists in the database before adding it.
        '''
        import traceback
        self.connect()

        df = self.load_df()
        row_counter = 0
        row_input_lim = 0
        # subset of large df with only rows that have URLs
        df_not_nan = df.loc[df['url'].notnull()]
        
        # create a SAMPLE of the full dataset to include 5 bills from each state in the database (n= n bills per state)
        # this parameter will not be hard coded in future versions
        sample_df = df_not_nan.groupby(["state"]).sample(n=5, random_state=1)

        try:
            for i, row in enumerate(sample_df.to_dict(orient='records')): # create a dict with dataframe rows
                if row_input_lim < self.input_lim:
                    # Check if Bills exists in database
                    x = pd.read_sql(SQ.SQL_CHECK_BILLS, self.conn, params=row)
                    if len(x) == 0:
                        # Insert the record if it did not
                        self.curs.execute(SQ.SQL_INSERT_TBILLS, row)
                        row_counter += 1
                        print(row_counter)
                        clear_output(wait=True)
            
            self.conn.commit() # commit changes to database
            self.close()

        except Exception:
            # Undo all changes since the last commit
            self.conn.rollback()
            print('Error at row:', i, '\n')
            print(row)
            # Print the exception information
            traceback.print_exc()

        return
    
    # this function is only intended to be used after this project is adapted
    # to accomodate the size and runtime required to process all legislation data
    def fill_table_chunks(self): 
        PATH = './data/bills-with-urls.csv' # this file does not exist on github (~2.8 million rows)
        df = pd.read_csv(PATH)
        sample_df = df.groupby(["state"]).sample(n=1, random_state=1)
        chunk_counter = 0
        self.connect()
        for c in pd.read_csv(PATH, chunksize=self.chunk_size):
            chunk_counter += 1 
            c.to_sql(name="tBills", index=False,con=self.conn, chunksize=self.chunk_size, if_exists="append")
            print(chunk_counter)
            clear_output(wait=True)
        self.close()
    
        
    def get_tBills(self):
        '''
        Returns the tBills table from the provided database as a Pandas dataframe
        '''
        sql = "SELECT * FROM tBills;"
        df = self.run_query(sql)
        return df
    
    def run_query(self, 
                  sql: str, 
                  params: tuple|dict=None
                  ) -> pd.DataFrame:
        '''Use this method to access data from the SQL database with your own query'''
        
        self.connect()
        results = pd.read_sql(sql, self.conn, params=params)
        self.close()
        return results
