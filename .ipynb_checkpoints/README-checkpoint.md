# congressional-captcha

I have pared down the scope of the original project to only focus on state and federal legislation (no longer looking at ALEC) for the time being. This repo produces a streamlit web application you can use to quickly summarize keywords and topics from legislation. Users are able to select legislation by state (including D.C. and U.S. Congress) and by legislative session. Background processes will attempt to retreive the bill from the state website using Apache Tika. 

**You will need to have [Java 8](https://www.java.com/en/download/manual.jsp) installed to run this app.**

To run this application: 

1. Clone this repository
2. Create a virtual environment:  `pipenv shell `
3. Install dependencies: `pipenv install --ignore-pipfile`
4. Run: `python -m spacy download en_core_web_sm`
5. Run: `streamlit run main_app.py`
*The application should open in your browser*

The full version of this project will include the text processing and visualization elements.

***

Model legislation written by industry groups, think tanks, and corporations are introduced by state lawmakers every legislative session. A 2019 analysis of over 1 million bills found that nearly 10,000 bills copied off of model legislation were introduced over 8 years. The goal of this project is to produce a pipeline to reproduce [this analysis](https://www.azcentral.com/in-depth/news/local/arizona-investigations/2019/04/04/abortion-gun-laws-stand-your-ground-model-bills-conservatives-liberal-corporate-influence-lobbyists/3361759002/) with updated legislative data at a smaller scale (the linked report states their analysis required ~150 computers' worth of computing power and several months of runtime). 

Tentative steps for this project (updated 11/17 12:30 AM): 
1. Obtain legislative data using the [LegiScan]([url](https://legiscan.com/legiscan)https://legiscan.com/legiscan) API. LegiScan updates legislative information in real-time and tracks bills from all statehouses and U.S. Congress. Obtain model bill data from [ALEC](https://alec.org/model-policy/?alec_search_term=&alec_post_type%5B%5D=model-policy&alec_year=&alec_p2p%5B%5D=&alec_meta%5B%5D=&alec_meta%5B%5D=&alec_term%5B%5D=&in_page_search=1). Create a database. ✔️
2. Discover that data is indeed stored as .docx, HTML, PDFs, and other weird file types. Use the [Apache Tika](https://github.com/chrismattmann/tika-python) library to extract text from unstructured documents. The most recent test of this step is in `text_from_web_extraction.ipynb`. ~~Plan to standardize data/extract text. I'm sure that different states upload bills as PDFs, Word files, web pages, etc.~~ ✔️
3. Scrape a dataset off of ALEC for text comparison purposes 
4. Choose a method for analyzing text similarity for a subset of bills (same topic, keywords, etc.). The current idea is to use TF-IDF to identify keywords from each piece of legislation in my database and the ALEC dataset, then come up with some metric to pair ALEC model bills with their most similar legislative counterparts. From there, I will consider a Count Vectorizer to identify n-grams that are identical across both bills. Another approach to narrow down legislation is to use topic modeling to categorize or label texts before searching with a Count Vectorizer (e.g. LDA with parameter tuning via Grid Search).
5. Visualize semantic similarity (interactively?) across different topics -- perhaps a heatmap to show similarity between an ALEC bill and a set of other legislation? 
