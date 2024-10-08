##############################################
#--------------Helper Functions---------------
##############################################

# tools/hashtags_generating.py

import spacy
import logging
# Load the spaCy model for English
nlp = spacy.load('en_core_web_sm')

# Set up logging
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def generate_hashtags(query: str):
    """
    Generates contextual hashtags based on the input query.

    Args:
        query (str): The input text query for which hashtags are to be generated.

    Returns:
        list: A list of generated hashtags.
    """

    logger.info("Generating hashtags...")
    query = query.strip()

    if not query:
        return []
    try:
        doc = nlp(query)
    except Exception as e:
        logger.error(f"Error processing query with spaCy: {e}")
        return []
    
    hashtags = []

    phrase = []

    for token in doc:
        if token.pos_ in ['PROPN', 'NOUN', 'ADJ'] and not token.is_stop and not token.is_punct:
            phrase.append(token.text.lower().strip())
        else:
            if phrase:
                hashtags.append(f"#{''.join(phrase)}")
                phrase = []  

    if phrase:
        hashtags.append(f"#{''.join(phrase)}")

    hashtags = list(set(hashtags))  # Remove duplicates

    final_hashtags = [hashtag for hashtag in hashtags if not any(hashtag in h and hashtag != h for h in hashtags)]
    
    return final_hashtags