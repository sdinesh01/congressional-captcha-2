import create_database
from create_database import MyDB
from bill_text import Bill
import bill_text
import pandas as pd
import streamlit as st
import streamlit_scrollable_textbox as stx
import streamlit_nested_layout
import io
import time
import spacy
#from spacy import displacy
from spacy_streamlit import visualize_ner

class MyApp:
    def __init__(self):
        self.db = self.build_database()
        self.nlp = self.build_model()
        self.build_page()
        return

    # main build_page method
    def build_page(self):
        '''
        This function builds all of the main page containers and fills them with the appropriate information
        '''
        
        # page title
        st.write('# Tracking state and federal legislation, 2012-2023') 
        
        # sidebar title
        st.sidebar.header('State and session selection')
        # descriptive text under the title
        st.write("Use the dropdown menus on the side to select a state and legislative session. The options available represent a random sample of the dataset. The final version of this application will analyze key words and topics from bill texts that the app is able to retrieve; *data from legislative sessions over two years ago may have moved or may no longer exist*.")
        # dropboxes for state and session selection
        self.select_state()
        self.select_session()
        
        # initalize the main screen by emptying all elements
        main_screen = st.empty()
        with main_screen.container(): 
            # create a dataframe showing the results of the state and session query
            self.get_bills()
            # load the text for each of the bills in the dataframe
            with st.spinner('Retrieving text...'): 
                # fetch the content if it is not already saved in the database
                if self.results.iloc[0]['content'] is None: 
                    # create the NER labels dictionary in the sidebar
                    self.create_ner_info_table()
                    # display the bill text
                    self.get_bill_text()
                
                # if bills are already in the database, empty the main screen, refresh the database and build page
                else: 
                    main_screen.empty()
                    with main_screen.container():
                        self.refresh_bills_dataframe()
                        self.create_ner_info_table()
                        self.get_bill_text()
                            
        self.streamlit_defaults()
        return
    
    @st.cache_resource(show_spinner=False)
    def build_database(_self): 
        '''
        Build the legislation database on loading the application
        '''
        # add a spinner on load 
        with st.spinner("Loading data from database. This may take a minute..."):
            _self.db = MyDB(bills_drop=True, any_drop=True, add_data=True, table_type='bills', input_lim=200, chunk_size=500)
        # display success message for 3 seconds
        success = st.success('Done!')
        time.sleep(3) # Wait for 3 seconds
        success.empty() # Clear the alert
        return _self.db
    
    @st.cache_resource(show_spinner=False)
    def build_model(_self): 
        '''
        Cache an instance of the spaCy NER model -- "_sm" indicates that we are using a smaller version of the model for runtime but other versions are available
        '''
        _self.nlp = spacy.load("en_core_web_sm")
        return _self.nlp
    
    def create_ner_info_table(_self): 
        '''
        Create a table in the sidebar with the spaCy NER entity labels for readability and user convenience
        '''
        with st.sidebar.expander('spaCy named entity recognition labels'): 
            mod_help_text = pd.DataFrame({'Label':['PERSON', 'NORP', 'FAC','ORG','GPE','LOC','PRODUCT','EVENT','WORK_OF_ART','LAW','LANGUAGE','DATE','TIME','PERCENT','MONEY','QUANTITY','ORDINAL','CARDINAL'], 'Description': ['People, including fictional','Nationalities or religious or political groups','Buildings, airports, highways, bridges, etc.','Companies, agencies, institutions, etc.','(Geopolitical entities) Countries, cities, states','Non-GPE locations, mountain ranges, bodies of water','Objects, vehicles, foods, etc. (Not services.)','Named hurricanes, battles, wars, sports events, etc.','Titles of books, songs, etc.',' Named documents made into laws','Any named language','Absolute or relative dates or periods ','Times smaller than a day','Percentage, including ”%“',' Monetary values, including unit','Measurements, as of weight or distance','“first”, “second”, etc.','Numerals that do not fall under another type']})
            st.table(mod_help_text)
            return 
    
    def select_state(self): 
        '''
        Allows users to select a state they want the legislation for. We are querying our sqlite3 database in the background to identify all distinct states, then alphabetizing the list for readability, and finally, saving the selection as a class variable. 
        '''
        self.states = self.db.run_query('SELECT DISTINCT state FROM tBills;')['state'].tolist()
        # display all states in alphabetical order
        self.states_sorted = sorted(self.states)
        self.state_choice = st.sidebar.selectbox('Select a state:', self.states_sorted)
        return self.state_choice
    
    def select_session(self): 
        '''
        Allows users to select a state they want the legislation for. We are querying our sqlite3 database in the background to identify all distinct sessions by state, then saving the selection as a class variable. 
        '''
        self.sessions = self.db.run_query('SELECT DISTINCT session FROM tBills WHERE state = (?);', (self.state_choice,))['session'].tolist()
        self.session_choice = st.sidebar.selectbox('Select a session:', self.sessions)
        return self.session_choice
    
    def get_bills(self): 
        '''
        Using the class variables self.session_choice and self.state_choice, we are running a query on the sqlite3 database to retrieve all relevant bills, which we are saving as a class variable (self.results) and displaying as a streamlit dataframe.
        '''
        self.query = """ SELECT * 
                FROM tBills
                WHERE state = (?) AND session = (?)
                ;"""
        self.results = self.db.run_query(sql=self.query, params=(self.state_choice, self.session_choice))
        return st.dataframe(self.results)
    
    def refresh_bills_dataframe(self): 
        self.query = """ SELECT * 
                FROM tBills
                WHERE state = (?) AND session = (?)
                ;"""
        results = self.db.run_query(sql=self.query, params=(self.state_choice, self.session_choice))
        return st.dataframe(results)
    
    def retrieve_bill_text(self):
        '''
        Retrieve the bill text using the functionality from bill_text.py. First, we establish a database connection, then find the bills that are still unprocessed for our chosen state and session. Finally, we update the database with the results from Tika processing.
        '''
        try: # close database connection if one already exists
            self.db.close()
        except:
            pass
        self.db.connect()
        still_unprocessed = pd.read_sql("""SELECT bill_id FROM tBills
                                           WHERE processed_at IS NULL AND state = (?) AND session = (?);""", 
                                        con=self.db.conn, params=(self.state_choice, self.session_choice))
        id_nums = still_unprocessed['bill_id'].tolist()
        if len(id_nums)!=0: # get text for any bills in the unprocessed list
            for i in id_nums: 
                bill = Bill.get(self.db.conn, i)
                bill.update_content()
        self.db.close()
        return 
    
    def get_bill_text(self):
        '''
        Retrieve the bill text for the bills in the chosen state and session, then query the database for the bill texts (or errors if the bill could not be retrieved). If there is only one bill for a given session, run the NER and visualize the summary statistics. If there are multiple bills per session per state, create nested streamlit expanders to condense the length of the webpage. Each expander contains the NER category selection box, labeled text, and summary table. Bills that errored out through Tika will display a string describing the error message.
        '''
        
        self.retrieve_bill_text()
        self.query = """ SELECT title, content 
                        FROM tBills
                        WHERE state = (?) AND session = (?)
                        ;"""
        self.errors_query = """ SELECT error, processed_at
                                FROM tBills
                                WHERE state = (?) AND session = (?)
                            ;"""
        results = self.db.run_query(sql=self.query, params=(self.state_choice, self.session_choice))
        errors = self.db.run_query(sql=self.errors_query, params=(self.state_choice, self.session_choice))
        
        # if there's one bill for a given legislative session...
        if results.shape[0] == 1:
            if (results.iloc[0]['content'] is None): # if there is no content, check for the specific errors we have handled
                if errors.iloc[0]['error'] == 'connection': 
                    return st.error("We could not retreive the contents of this bill due to a connection error. Check if the bill from " +
                                    str(self.state_choice) + "'s " + str(self.session_choice) + " session docket has moved.") 
                elif errors.iloc[0]['error'] == 'bad_url':
                    return st.error("We could not retreive the contents of this bill due to a bad url. Check if the bill from " +
                                    str(self.state_choice) + "'s " + str(self.session_choice) + " session docket has moved.")
                elif errors.iloc[0]['error'] == 'timeout':
                    return st.error("We could not retreive the contents of this bill due to session timeout. Check if the bill from " +
                                    str(self.state_choice) + "'s " + str(self.session_choice) + " session docket has moved.")
                elif errors.iloc[0]['error'] == 'timeout':
                    try: 
                        self.retrieve_bill_text()
                    except: 
                        return st.error("We could not retreive the contents of this bill due to an Apache Tika error. Check if the bill from " +
                                    str(self.state_choice) + "'s " + str(self.session_choice) + " session docket has moved.")
                else: 
                    pass
            else: 
                text = results.iloc[0]['content']
                doc = self.nlp(text)
                visualize_ner(doc, labels=self.nlp.get_pipe("ner").labels, title = ' ')
        # if there is more than one bill for a given legislative session, this block runs: 
        else: 
            for i, x in enumerate(range(results.shape[0])): 
                with st.expander(str(results.iloc[i]['title'])): # create an expander for each bill in the chosen session
                    # if there is no content, check for the specific errors we have handled and return a streamlit error box to signal the problem to the user
                    if (results.iloc[i]['content'] is None): 
                        if errors.iloc[i]['error'] == 'connection': 
                            return st.error("We could not retreive the contents of this bill due to a connection error. Check if the bill from " +
                                            str(self.state_choice) + "'s " + str(self.session_choice) + " session docket has moved.") 
                        elif errors.iloc[i]['error'] == 'bad_url':
                            return st.error("We could not retreive the contents of this bill due to a bad url. Check if the bill from " +
                                            str(self.state_choice) + "'s " + str(self.session_choice) + " session docket has moved.")
                        elif errors.iloc[i]['error'] == 'timeout':
                            return st.error("We could not retreive the contents of this bill due to session timeout. Check if the bill from " +
                                            str(self.state_choice) + "'s " + str(self.session_choice) + " session docket has moved.")
                        elif errors.iloc[i]['error'] == 'tika':
                            try: 
                                self.retrieve_bill_text()
                            except: 
                                return st.error("We could not retreive the contents of this bill due to an Apache Tika error. Check if the bill from " +
                                            str(self.state_choice) + "'s " + str(self.session_choice) + " session docket has moved.")
                        else: 
                            pass
                    else: # content is available and we can visualize it
                        try: 
                            text = results.iloc[i]['content']
                            doc = self.nlp(text)
                            visualize_ner(doc, labels=self.nlp.get_pipe("ner").labels, key=x, title= ' ')
                        except: # for any reason spaCy cannot visualize the bill content, throw this error message
                            st.error('The bill titled "' + str(results.iloc[i]['title']) + '" could not be visualized.')

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