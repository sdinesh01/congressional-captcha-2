import create_database
from create_database import MyDB
from bill_text import Bill
import bill_text
import pandas as pd
import streamlit as st
import streamlit_scrollable_textbox as stx
import io
import time

class MyApp:
    def __init__(self):
        self.db = self.build_database()
        self.build_page()
        return

    # main build_page method
    def build_page(self):
        st.write('# Legislation tracker')
        
        st.sidebar.header('State and session selection')
        st.write("I'm just trying to get something to show up here!!!")
        self.select_state()
        self.select_session()
        
        main_screen = st.empty()
        with main_screen.container(): 
            self.get_bills()
            with st.spinner('Retrieving text...'): 
                if self.results.iloc[0]['content'] is None: 
                    self.get_bill_text()
                else: 
                    main_screen.empty()
                    with main_screen.container():
                        #self.build_database.clear()
                        self.get_bills()
                        self.get_bill_text()
        
        self.streamlit_defaults()
        return
    
    @st.cache_resource(show_spinner=False)
    def build_database(_self): 
        with st.spinner("Loading data from database. This may take a while..."):
            _self.db = MyDB(bills_drop=True, any_drop=True, add_data=True, table_type='bills', input_lim=200, chunk_size=500)
        success = st.success('Done!')
        time.sleep(3) # Wait for 3 seconds
        success.empty() # Clear the alert
        return _self.db
    
    def select_state(self): 
        self.states = self.db.run_query('SELECT DISTINCT state FROM tBills;')['state'].tolist()
        self.states_sorted = sorted(self.states)
        self.state_choice = st.sidebar.selectbox('Select a state:', self.states_sorted)
        return self.state_choice
    
    def select_session(self): 
        self.sessions = self.db.run_query('SELECT DISTINCT session FROM tBills WHERE state = (?);', (self.state_choice,))['session'].tolist()
        self.session_choice = st.sidebar.selectbox('Select a session:', self.sessions)
        return self.session_choice
    
    def get_bills(self): 
        self.query = """ SELECT * 
                FROM tBills
                WHERE state = (?) AND session = (?)
                ;"""
        self.results = self.db.run_query(sql=self.query, params=(self.state_choice, self.session_choice))
        return st.dataframe(self.results)
    
    def retrieve_bill_text(self):
        try:
            self.db.close()
        except:
            pass
        self.db.connect()
        still_unprocessed = pd.read_sql("""SELECT bill_id FROM tBills
                                           WHERE processed_at IS NULL AND state = (?) AND session = (?);""", 
                                        con=self.db.conn, params=(self.state_choice, self.session_choice))
        id_nums = still_unprocessed['bill_id'].tolist()
        if len(id_nums)!=0: 
            for i in id_nums: 
                bill = Bill.get(self.db.conn, i)
                bill.update_content()
        self.db.close()
        return 
    
    def get_bill_text(self):
        self.retrieve_bill_text()
        self.query = """ SELECT content 
                        FROM tBills
                        WHERE state = (?) AND session = (?)
                        ;"""
        self.errors_query = """ SELECT error, processed_at
                                FROM tBills
                                WHERE state = (?) AND session = (?)
                            ;"""
        results = self.db.run_query(sql=self.query, params=(self.state_choice, self.session_choice))
        errors = self.db.run_query(sql=self.errors_query, params=(self.state_choice, self.session_choice))
        if results.shape[0] == 1:
            if (results.iloc[0]['content'] is None):
                if errors.iloc[0]['error'] == 'connection': 
                    return st.error("We could not retreive the contents of this bill due to a connection error. Check if the from " +
                                    str(self.state_choice) + "'s " + str(self.session_choice) + " session docket has moved.") 
                elif errors.iloc[0]['error'] == 'bad_url':
                    return st.error("We could not retreive the contents of this bill due to a bad url. Check if the from " +
                                    str(self.state_choice) + "'s " + str(self.session_choice) + " session docket has moved.")
                elif errors.iloc[0]['error'] == 'timeout':
                    return st.error("We could not retreive the contents of this bill due to session timeout. Check if the from " +
                                    str(self.state_choice) + "'s " + str(self.session_choice) + " session docket has moved.")
                elif errors.iloc[0]['error'] == 'timeout':
                    try: 
                        self.retrieve_bill_text()
                    except: 
                        return st.error("We could not retreive the contents of this bill due to an Apache Tika error. Check if the from " +
                                    str(self.state_choice) + "'s " + str(self.session_choice) + " session docket has moved.")
                else: 
                    pass
            else: 
                return stx.scrollableTextbox(results.iloc[0]['content'], height=400)
        else: 
            for i in range(results.shape[0]): 
                if (results.iloc[0]['content'] is None):
                    if errors.iloc[0]['error'] == 'connection': 
                        return st.error("We could not retreive the contents of this bill due to a connection error. Check if the from " +
                                        str(self.state_choice) + "'s " + str(self.session_choice) + " session docket has moved.") 
                    elif errors.iloc[0]['error'] == 'bad_url':
                        return st.error("We could not retreive the contents of this bill due to a bad url. Check if the from " +
                                        str(self.state_choice) + "'s " + str(self.session_choice) + " session docket has moved.")
                    elif errors.iloc[0]['error'] == 'timeout':
                        return st.error("We could not retreive the contents of this bill due to session timeout. Check if the from " +
                                        str(self.state_choice) + "'s " + str(self.session_choice) + " session docket has moved.")
                    elif errors.iloc[0]['error'] == 'tika':
                        try: 
                            self.retrieve_bill_text()
                        except: 
                            return st.error("We could not retreive the contents of this bill due to an Apache Tika error. Check if the from " +
                                        str(self.state_choice) + "'s " + str(self.session_choice) + " session docket has moved.")
                    else: 
                        pass
                else: 
                    return stx.scrollableTextbox(results.iloc[0]['content'], height=400)

    def streamlit_defaults(self):
        '''
        Remove some auto-generated stuff by streamlit
        '''
        hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            </style>
            """
        st.markdown(hide_streamlit_style, unsafe_allow_html=True) 
        return