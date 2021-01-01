# Extracting haikus from the news

Lately, the news have made us more and more anxious, and we have caught ourselves *doomscrolling* a bit too much. Therefore, we decided to change how we consume news, and do it through haikus instead of headlines. You can read the haikus [here](https://nyhetshaiku.herokuapp.com), and this repo contains the sourcecode for that app.

We decided to give ourselves one day to make a haiku detection algorithm and figure out how to serve a webpage with Python. To analyse the text and find haikus, we use Spacy. This way, we can make sure that we don't split noun chunks, which increases the chance that the haikus make sense. Then, we count the number of vowels, which is a good heuristic to count Norwegian syllables. 

To serve the webpage, we have two concurrent processes: A simple flask server to serve the HTML, and a background process that fetches the news and extracts haikus once every hour. The extracted haikus are stored in a JSON file. For each web request, this JSON file is loaded and a random haiku is selected.

