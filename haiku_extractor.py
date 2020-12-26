#!/usr/bin/env python
# coding: utf-8

# In[91]:


import spacy
import feedparser
from string import digits
import json
from tqdm import tqdm
import time
from subprocess import run


# In[92]:


try:
    nlp = spacy.load("nb_core_news_md")
except OSError:
    run("python -m spacy download nb_core_news_md".split())
    nlp = spacy.load("nb_core_news_md")


# In[3]:


def estimate_norwegian_syllables(word):
    vokaler = "aeiouyæøå"
    num_syllables = 0
    for letter in word:
        if letter in vokaler:
            num_syllables += 1
    return num_syllables

def is_interesting(token):
    if token.is_punct:
        return False
    if token.is_space:
        return False
    return True


# In[4]:


def get_filtered_lists(doc):
    word_indices = []
    syllable_count = []
    
    for i, token in enumerate(doc):
        if is_interesting(token):
            word_indices.append(i)
            syllable_count.append(estimate_norwegian_syllables(token.text))
    
    return word_indices, syllable_count


# In[47]:


def split_haiku_lines(word_indices, cum_syllable_count):
    haiku_syllables = [5, 12, 17]
    line_end1 = cum_syllable_count.index(haiku_syllables[0])+1
    line_end2 = cum_syllable_count.index(haiku_syllables[1])+1
    line_end3 = cum_syllable_count.index(haiku_syllables[2])+1
    
    return (word_indices[:line_end1], word_indices[line_end1:line_end2], word_indices[line_end2:line_end3])
    
    
def detect_haiku_beginning(word_indices, syllable_count, doc):
    cumsum_syllable = [0]
    for syllables in syllable_count:
        cumsum_syllable.append(syllables + cumsum_syllable[-1])
    cumsum_syllable = cumsum_syllable[1:]
    
    if (17 not in cumsum_syllable or 12 not in cumsum_syllable or 5 not in cumsum_syllable):
        return None
    else:
        end_idx = cumsum_syllable.index(17)
        # Disregard if haiku contains a number
        if len(set(doc[word_indices[0]:word_indices[end_idx]].text) & set(digits)) > 0:
            return None
        
        return split_haiku_lines(word_indices, cumsum_syllable)


# In[65]:


def get_haiku(verse_indices, doc):
    haiku = ""
    for verse in verse_indices:
        for idx in verse:
            haiku += doc[idx].text.lower() + " "
        haiku += "\n"
    return haiku[:-1]
def print_extracted_haiku_words(verse_indices, doc):
    print(get_haiku(verse_indices, doc))
    return
    for verse in verse_indices:
        for idx in verse:
            print(doc[idx].text.lower(), end=' ')
        print("")


# In[49]:


def check_approved_ending(haiku_indices, doc):
    if doc[haiku_indices[0][0]].is_sent_start == False:
        return False
    ending_token = doc[haiku_indices[2][-1]]
    if ending_token.is_sent_start:
        return False
    if ending_token.pos_ == 'NOUN':
        return True
    if ending_token.pos_ == 'ADJ':
        if 'VerbForm=Fin' in ending_token.tag_:
            return True
        else:
            return False
    if ending_token.pos_ == 'VERB':
        return True
    return False


# In[50]:


def gen_haiku_season_score(verse_indices, doc):
    winter_words = ["vinter", "snø", "ski", "julefeiring", "jul", "høytid", "november", "desember", "januar", "februar"]
    spring_words = ["vår", "blomster", "løvetann", "april", "mars", "mai", "nasjonaldag", "flagg", "barnetog", "påske"]
    summer_words = ["sommer", "sol", "bade", "ferie", "havet", "øy", "juni", "juli", "august", "strand", "syden", "agurk"]
    fall_words = ["høst", "storm", "halloween", "mørkt", "hytte", "løv", "trær", "vind", "september", "oktober", "regn"]
    season_words = ["årstid", "måned", "tid", "vær"]
    all_season_words = winter_words+spring_words+summer_words+fall_words+season_words
    
    max_season_word = None
    max_season_score = 0
    max_match_word = None
    for season_word in all_season_words:
        
        for verse in verse_indices:
            for idx in verse:
                score = doc[idx].similarity(nlp(season_word))
                if score > max_season_score:
                    max_season_score = score
                    max_season_word = season_word
                    max_match_word = doc[idx]
    return max_season_score


# In[88]:


rss = feedparser.parse('https://www.nrk.no/toppsaker.rss')

while True:
    haikus = []
    for entry in tqdm(rss.entries):
        doc = nlp(entry.description)

        word_indices, syllabus_count = get_filtered_lists(doc)

        haiku_list = []

        for i in range(len(word_indices)):
            haiku_indeces = detect_haiku_beginning(word_indices[i:], syllabus_count[i:], doc)
            if haiku_indeces is not None:
                if check_approved_ending(haiku_indeces, doc):
                    haiku_list.append(haiku_indeces)

        for haiku in haiku_list:
            season_score = print_extracted_haiku_season(haiku, doc)
            if season_score>0.5:
                #print_extracted_haiku_words(haiku, doc)
                haikus.append({'haiku': get_haiku(haiku, doc), 'link': entry.link})
                #print(season_score)
                #print_extracted_haiku_season(haiku, doc)
                #print("...")

    with open("haikus.json", "w") as f:
        json.dump(haikus, f)
    
    time.sleep(3600)

