import pandas as pd
import sqlite3
import requests
import tika
from tika import parser
from IPython.display import clear_output

# Should we use OCR if normal processing fails?
USE_OCR = True

class Bill:

    def __init__(self, bill_id, url, conn):
        self.bill_id = bill_id,
        self.url = url
        try:
            # A little cleaning for URLs that have moved domains
            self.url = self.url.replace("www.rilin.state.ri.us", "webserver.rilin.state.ri.us")
            self.url = self.url.replace('legis.sd.gov', 'sdlegislature.gov')
        except:
            pass
        self.conn = conn

    def update_content(self):
        self.content = None
        self.error = None

        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
            response = requests.get(self.url, headers=headers, allow_redirects=True, timeout=2)
            print(response)

            # Send to tika
            tika_output = parser.from_buffer(response)

            # If we get nothing back, try OCR
            if USE_OCR and ('content' not in tika_output or not tika_output['content']):
                # headers = { 'X-Tika-PDFOcrStrategy': 'ocr_only' }
                headers = { 'X-Tika-PDFextractInlineImages': 'true' }
                tika_output = parser.from_buffer(response, headers=headers)

            if 'content' in tika_output and tika_output['content']:
                self.content = tika_output['content'].strip()
                self.content = str(self.content)
            else:
                self.error = 'tika'
        except requests.exceptions.MissingSchema:
            self.error = 'bad_url'
        except requests.exceptions.Timeout:
            self.error = 'timeout'
        except requests.exceptions.ConnectionError:
            self.error = 'connection'
        
        self.save()
        
    def save(self):
        self.conn.execute("""
            UPDATE tBills SET content=(?), error=(?), processed_at=(datetime('now','localtime'))
            WHERE bill_id = (?)
        """, (self.content, self.error, self.bill_id[0]));
        
    @classmethod
    def get(cls, conn, bill_id):
        results = conn.execute("""
            SELECT bill_id, url
            FROM tBills
            WHERE bill_id = (?)
            LIMIT 1;
        """, (bill_id,))
        print(results)

        result = list(results)[0]
        return Bill(result[0], result[1], conn)
        
    @classmethod
    def unprocessed(cls, conn, limit=10):
        selected_state = self.state
        selected_session = self.session
        results = conn.execute("""
            SELECT bill_id, url
            FROM tBills
            WHERE processed_at IS NULL AND state = (?) AND session = (?)
            ORDER BY RANDOM()
            LIMIT = (%s)
        ;""", (selected_state, selected_session))
        return [Bill(result[0], result[1], conn) for result in results]
    
    @classmethod
    def process_queue(cls, conn, limit=10):
        selected_state = self.state
        selected_session = self.session
        todo = Bill.unprocessed(conn, self, limit)
        for bill in todo:
            bill.update_content()
            
def connect_and_update(_):
    conn = sqlite3.connect('sample-data/legislation.db', isolation_level=None)
    Bill.process_queue(conn)
    conn.close()