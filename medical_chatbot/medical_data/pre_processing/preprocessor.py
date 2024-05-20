from fastapi import logger
from sklearn.feature_extraction import text
import re
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
import re

class DataPreprocessing:
    def __init__(self):
       nltk.download('punkt')
       nltk.download('wordnet')
       self.stop_words = set(stopwords.words('english'))
       self.lemmatizer = WordNetLemmatizer()

    def preprocess_text(self, text):
        """
        Preprocesses text by lowercasing, removing numbers, punctuations, and extra spaces.
        Args: 
            text (str): Text string to be processed.
        Returns:
            str: The processed text string.
        """
        try:
            processed_text = text.lower()
            processed_text = re.sub(r'\n', ' ', processed_text)
            #processed_text = re.sub(r'[0-9]+', '', processed_text)
            #processed_text = re.sub(r'[^\w\s]', '', processed_text)
            processed_text = re.sub(' +', ' ', processed_text)
            return processed_text
        except Exception as e:
            logger.error(f"Exception occurred while preprocessing text: {e}")
            raise e

    def remove_stop_words(self, text):
        """
        Removes stop words, including custom stop words, from the text and performs tokenization and lemmatization.

        Args:
            text (str): Text string from which stop words should be removed.

        Returns:
            str: The text string with stop words removed and lemmatized tokens.
        """
        try:
            # Tokenize the text
            words = word_tokenize(text)
            # Lemmatize tokens and remove stopwords
            processed_tokens = [self.lemmatizer.lemmatize(word) for word in words if word.lower() not in self.stop_words]
            # Combine the processed tokens back into a string
            processed_text = ' '.join(processed_tokens)
            return processed_text
        except Exception as e:
            logger.error(f"Exception occurred while removing stop words: {e}")
            raise e

