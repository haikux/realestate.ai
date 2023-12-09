# realestate.ai

## Note: Before you read anything else
app.py - has the APIs that bridge our front end and the PostGIS backend </br>
postgis_conn.py - script that houses all the PostgreSQL query we are performing </br>
templates/index.html - All the front-end code </br>

## Setup
Make sure you have Python 3.6x is installed.
python3 -m pip install -r requirements.txt

Clone this repo \
##### $ python3 -m pip install -r requirements.txt

Generate your OPENAI API Key, refer https://www.howtogeek.com/885918/how-to-get-an-openai-api-key/

Add the API key in app.py file \
llm = OpenAI(openai_api_key="YOUR_OPENAI_API_KEY") \\

Run Flask locally
##### $ flask run -p 8080
Visit http://localhost:8080 on your browser


![Screenshot 2023-12-07 at 11 06 36 PM](https://github.com/haikux/realestate.ai/assets/14270823/fdd7b47e-c168-42f5-a040-37c57c9f20f8)



# Dev Notes
Updates
* Housing data, AQI and Fatal accident data is ingested
* Explore mode is complete - Visualize all data at once
* Build good search experience for users with filters that displays houses only - very precisely + LLM information - Search mode - complete
* Working on implementing a good query for filter conditions - Help needed!
