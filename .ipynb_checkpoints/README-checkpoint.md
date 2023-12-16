# congressional-captcha

The long term goal of this project is to develop a user interface that can retrieve pieces of legislation from the state and federal level an run a natural language processing pipeline to calculate similarity scores and perform document labeling and topic modeling. These documents would be compared against a database of "model legislation" produced by industry groups, think tanks, and corporations to identify passed or introduced legislation that was likely not originally written by lawmakers. 

A 2019 analysis of over 1 million bills found that nearly 10,000 bills copied off of model legislation were introduced over 8 years. The goal of this project is to produce a pipeline to reproduce [this analysis](https://www.azcentral.com/in-depth/news/local/arizona-investigations/2019/04/04/abortion-gun-laws-stand-your-ground-model-bills-conservatives-liberal-corporate-influence-lobbyists/3361759002/) with updated legislative data at a smaller scale (the linked report states their analysis required ~150 computers' worth of computing power and several months of runtime).

I've pared down the scope of the above idea to develop a web application to assist with exploratory data analysis of state and federal legislation. This repo produces a streamlit web application you can use to quickly summarize keywords and topics from legislation using parts of speech selectors, dropdowns, and interactive tables. Users are able to select legislation by state (including D.C. and U.S. Congress) and by legislative session. Background processes will attempt to retreive the bill from the state website using Apache Tika. I have implemented spaCy's named entity recognition methods for text analysis.

This tool is useful for quickly scanning legislation and includes pop-ups to identify various errors that may occur in the process of text retrieval using Apache Tika. 

**You will need to have [Java 8](https://www.java.com/en/download/manual.jsp) installed to run this app.**

To run this application: 

1. Clone this repository
2. Create a virtual environment:  `pipenv shell `
3. Install dependencies: `pipenv install --ignore-pipfile`
4. Run: `python -m spacy download en_core_web_sm`
5. Run: `streamlit run main_app.py`

*The application should open in your browser*

![](https://github.com/sdinesh01/congressional-captcha-2/blob/main/main-app-Streamlit%20(2).gif?raw=true)

---
### Files in this repository

`main_app.py`: run this file to open the streamlit app

`my_app.py`: contains class `MyApp`, which includes all elements of the streamlit webpage

`legiscan.py`: code in this file is from [pylegiscan](https://github.com/poliquin/pylegiscan/tree/master/pylegiscan).     interacts with the Legiscan API. You will need to obtain an API key to fetch your own data. This file is set up to retrieve data for all available states and legislative sessions.

`fetch_data.py`: automates the process of retreiving data with `legiscan.py` and produces a .csv file. I wrote a short program, not included in this repository, to split the large file by state for the purpose of sharing data on GitHub.

`create_database.py`: reads in all .csv files in data/... as a Pandas dataframe and creates a SQLite3 database from a randomly sampled subset of the dataframe (currently 5 bills per state)  

`sql_queries.py`: SQL queries as strings. Used to create tables in the dataframe and update the entries of the table (tBills) in the database when text is accessed via `bill_text.py`.

`bill_text.py`: contains class `Bill`, which is used to retrieve bill text from state websites using Tika (Java 8 required)

`data/...` : contains .csv files of all bill titles and urls from legislative sessions from all states and U.S. Congress. The original csv files *do not* contain the actual text of the bill. The data folder also contains legislation.db, which is created by `create_database.py`.

file columns: bill_id, bill_code, bill_number, title, description, state, session, filename, status, status_date, url

| status_code | description   |
|-------------|---------------|
| 1:          | "Introduced", |
| 2:          | "Engrossed",  |
| 3:          | "Enrolled",   |
| 4:          | "Passed",     |
| 5:          | "Vetoed",     |
| 6:          | "Failed/Dead" |