import itertools
import json
import time
from string import digits
from typing import List, Optional, Tuple

import feedparser
import spacy
from tqdm import tqdm


__author__ = "Marie Roald & Yngve Mardal Moe"


with open("seasonal_words.json") as f:
    SEASONAL_WORDS = list(itertools.chain(*json.load(f).values()))


def estimate_norwegian_syllables(word: str):
    """Simply count the number of norwegian vowels in the word."""
    vokaler = "aeiouyæøå"
    num_syllables = 0
    for letter in word.lower():
        if letter in vokaler:
            num_syllables += 1
    return num_syllables


def is_interesting(token: spacy.tokens.token.Token) -> bool:
    """Disregard puctuation and spaces."""
    if token.is_punct:
        return False
    if token.is_space:
        return False
    return True


def get_filtered_index_lists(doc: spacy.tokens.doc.Doc) -> Tuple[List[int], List[int]]:
    """Get list of indices that represent interesting tokens."""
    word_indices = []
    syllable_count = []

    for i, token in enumerate(doc):
        if is_interesting(token):
            word_indices.append(i)
            syllable_count.append(estimate_norwegian_syllables(token.text))

    return word_indices, syllable_count


def split_haiku_lines(
    word_indices: List[int], cum_syllable_count: List[int]
) -> Tuple[List[int], List[int], List[int]]:
    """Get haiku as list of strings."""
    haiku_syllables = [5, 12, 17]
    line_end1 = cum_syllable_count.index(haiku_syllables[0]) + 1
    line_end2 = cum_syllable_count.index(haiku_syllables[1]) + 1
    line_end3 = cum_syllable_count.index(haiku_syllables[2]) + 1

    return (
        word_indices[:line_end1],
        word_indices[line_end1:line_end2],
        word_indices[line_end2:line_end3],
    )


def detect_haiku_beginning(
    word_indices: List[int], syllable_count: List[int], doc: spacy.tokens.doc.Doc
) -> Optional[Tuple[List[int], List[int], List[int]]]:
    """Find a Haiku in the beginning of the text."""
    cumsum_syllable = [0]
    for syllables in syllable_count:
        cumsum_syllable.append(syllables + cumsum_syllable[-1])
        if cumsum_syllable[-1] > 17:
            break
    cumsum_syllable = cumsum_syllable[1:]

    # The haiku must include a 5-7-5 sequence of syllables
    # if 17 not in cumsum_syllable or 12 not in cumsum_syllable or 5 not in cumsum_syllable:
    if (set(cumsum_syllable) & {5, 12, 17}) != {5, 12, 17}:
        return None

    end_idx = cumsum_syllable.index(17)
    # Disregard if haiku contains a number
    if len(set(doc[word_indices[0] : word_indices[end_idx]].text) & set(digits)) > 0:
        return None

    return split_haiku_lines(word_indices, cumsum_syllable)


def get_haiku(
    verse_indices: Tuple[List[int], List[int], List[int]], doc: spacy.tokens.doc.Doc
) -> str:
    """Combine the tokes from a haiku into a string."""
    haiku = ""
    for verse in verse_indices:
        for idx in verse:
            haiku += doc[idx].text.lower() + " "
        haiku += "\n"
    return haiku[:-1]


def check_approved_ending(
    verse_indices: Tuple[List[int], List[int], List[int]], doc: spacy.tokens.doc.Doc
) -> bool:
    """Filter out uninteresting Haikus."""
    if not doc[verse_indices[0][0]].is_sent_start:
        return False

    ending_token = doc[verse_indices[2][-1]]
    if ending_token.is_sent_start:
        return False
    if ending_token.pos_ == "NOUN":
        return True
    if ending_token.pos_ == "ADJ":
        if "VerbForm=Fin" in ending_token.tag_:
            return True
        else:
            return False
    if ending_token.pos_ == "VERB":
        return True
    return False


def get_haiku_season_score(
    verse_indices: Tuple[List[int], List[int], List[int]], doc: spacy.tokens.doc.Doc
) -> float:
    """Haikus should have a theme connected to seasons. This is a heuristic to check this.

    Use word vectors to compare the similarities between all tokens in the Haiku and words representing seasons.

    Output between 0 and 1.
    """
    max_season_score = 0
    for season_word in SEASONAL_WORDS:
        for verse in verse_indices:
            for idx in verse:
                score = doc[idx].similarity(nlp(season_word))
                max_season_score = max(max_season_score, score)
    return max_season_score


if __name__ == "__main__":
    rss = feedparser.parse("https://www.nrk.no/toppsaker.rss")

    nlp = spacy.load("nb_core_news_sm")

    merge_noun_chunks = nlp.create_pipe("merge_noun_chunks")
    nlp.add_pipe(merge_noun_chunks)
    merge_entities = nlp.create_pipe("merge_entities")
    nlp.add_pipe(merge_entities)
    ENFORCE_SEASONAL_THEME = False

    while True:
        haikus = []
        for entry in tqdm(rss.entries):
            doc = nlp(entry.description)

            word_indices, syllabus_count = get_filtered_index_lists(doc)

            haiku_list = []

            for i in range(len(word_indices)):
                haiku_indeces = detect_haiku_beginning(
                    word_indices[i:], syllabus_count[i:], doc
                )
                if haiku_indeces is not None:
                    if check_approved_ending(haiku_indeces, doc):
                        haiku_list.append(haiku_indeces)

            for haiku in haiku_list:
                if ENFORCE_SEASONAL_THEME and get_haiku_season_score(haiku, doc) < 0.5:
                    continue
                current_haiku = get_haiku(haiku, doc)
                haikus.append(
                    {
                        "haiku": current_haiku,
                        "link": entry.link,
                    }
                )

        with open("static/haikus.json", "w") as f:
            json.dump(haikus, f)

        print("Saved haikus")
        print("Waiting for one hour...", flush=True)
        time.sleep(3600)
