from legiscan import LegiScan
import legiscan
import os
import pandas as pd
import swifter
import zipfile
import base64
import io
import glob
import json

class FetchData: 
    '''
    This class produces a csv with Legiscan data
    '''
    
    def __init__(self, 
                 api_key = os.environ.get('LEGISCAN_API_KEY'), 
                 num_datasets = 20, 
                 PATH_OUT = './sample-data' 
                 ): 
        self.__api_key = api_key
        self.legis = LegiScan(self.__api_key)
        self.num_datasets = num_datasets
        self.PATH_OUT = PATH_OUT
        self.check_directories()
        #self.create_test_dataset_list()
        #self.decode_test_dataset()
        self.find_json()
        self.process_json()
        self.create_dataframe()
        self.df_to_csv()
        
        
    def check_directories(self): 
        if not os.path.exists(self.PATH_OUT): 
            os.mkdir(self.PATH_OUT)
        return
        
    def create_test_dataset_list(self): 
        self.datasets = self.legis.get_dataset_list()
        self.dataset = self.legis.get_dataset(self.datasets[self.num_datasets]['session_id'], self.datasets[self.num_datasets]['access_key'])
        return 
    
    def decode_test_dataset(self): 
        #dataset = self.create_test_dataset_list()
        self.z_bytes = base64.b64decode(self.dataset['zip'])
        self.zip = zipfile.ZipFile(io.BytesIO(self.z_bytes))
        
        # extract all files in the zip file
        self.zip.extractall(self.PATH_OUT)
        return
    
    def find_json(self): 
        self.filenames = glob.glob('./sample-data/' + "/*/*/bill/*.json", recursive = True)
        return 
         
    def process_json(self): 
        self.all_bill_data = {}
        for filename in self.filenames:
            with open(filename) as file:
                self.bill_data = {}
                # We need to do a little string replacing so the 
                self.json_str = file.read().replace('"0000-00-00"', 'null')
                self.content = json.loads(self.json_str)['bill']

                self.bill_data['bill_id'] = self.content['bill_id']
                self.bill_data['bill_number'] = self.content['bill_number']
                self.bill_data['title'] = self.content['title']
                self.bill_data['description'] = self.content['description']
                self.bill_data['state'] = self.content['state']
                self.bill_data['session'] = self.content['session']['session_name']
                self.bill_data['filename'] = filename
                self.bill_data['status'] = self.content['status']
                self.bill_data['status_date'] = self.content['status_date']

                try:
                    self.bill_data['url'] = self.content['texts'][-1]['state_link']
                except:
                    self.bill_data['url'] = None
        
            self.all_bill_data[filename] = self.bill_data
        return
            
    def create_dataframe(self):
        COLUMNS = ['bill_id','bill_number','title','description','state','session','filename','status','status_date','url']
        self.dataframe_final = pd.DataFrame(columns=COLUMNS)
        keys_all_bills = list(self.all_bill_data.keys())
        for i in keys_all_bills:
            values = []
            for j in list((self.all_bill_data[i]).keys()):
                values.append(self.all_bill_data[i][j])
            self.dataframe_final.loc[i] = values
        self.dataframe_final.reset_index(inplace=True)
        try: 
            self.dataframe_final.drop(columns=['index'], axis=1, inplace=True)
        except: 
            pass
        return

    def df_to_csv(self): 
        self.dataframe_final.to_csv('./sample-data/' + '/bills-with-urls.csv', index=False)
        return 

    def get_test_datasets(self): 
        return self.datasets.copy()
    
    def get_json_filenames(self): 
        return self.filenames
    
    def get_dataframe(self): 
        return self.dataframe_final