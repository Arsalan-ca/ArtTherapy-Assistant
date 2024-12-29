"""
chatbot.py

A simple chatbot that provides information about Art Therapy using regex patterns and fuzzy matching.
This program reads question-answer pairs from a file and processes user input to generate appropriate responses.

Author: Mohammad Moaddeli
Date: 2024-10-16
"""


import regex as re
from fuzzywuzzy import fuzz
import spacy
from spacy.matcher import Matcher

def read_Q_A(file_path):
    """
    Reads a question-answer file and extracts regex patterns, questions, and answers.

    Parameters:
        file_path (str): The path to the question-answer file.

    Returns:
        list: A list of regex patterns.
        list: A list of lists containing questions.
        list: A list of lists containing answers.
    """
    regEx = []
    questions = []
    answers = []

    with open(file_path, 'r') as file:
        lines = file.readlines()

    current_section = 0  # 0 = regex, 1 = questions, 2 = answers
    current_questions = []
    current_answers = []

    for line in lines:
        line = line.strip()

        # Skip empty lines
        if not line:
            continue
        
        # If the line starts with a regex-like structure, treat it as a regex
        if current_section == 0:
            regEx.append(line)
            current_section = 1

        # Collect questions (next two lines)
        elif current_section == 1:
            current_questions.append(line)
            if len(current_questions) == 2:  # After two questions, move to answers
                questions.append(current_questions)
                current_questions = []
                current_section = 2  # Move to the answers section

        # Collect the answer (single answer after questions)
        elif current_section == 2:
            current_answers.append(line)
            answers.append(current_answers)
            current_answers = []
            current_section = 0  # Reset to start collecting the next regex

    return regEx, questions, answers

# File and storage --------------------------------------------------------------------------
file_path = "QandA.txt"
regEx, questions, answers = read_Q_A(file_path)


#  Spacy Heuristics rules and methods -------------------------------------------------------
nlp = spacy.load("en_core_web_lg")

def is_asking_question(user_input):
    """
    Determines if the user's input is a question based on heuristic rules.

    Parameters:
        user_input (str): The user's input string.

    Returns:
        bool: True if the input is a question, False otherwise.
    """
    doc = nlp(user_input)
    # Heuristic rule #1 *************************
    if user_input.strip().endswith("?"):
        return True
    # Heuristic rule #2 *************************
    wh_questions = {"who", "what", "when", "where", "why", "how", "which", "whom", "whose"}
    for token in doc:
        if(token.lower_ in wh_questions):
            return True
    # Heuristic rule #3 *************************
    for token in doc:
        if token.tag_ == "MD" and token.dep_ == "aux":
            return True
    # Heuristic rule #4 *************************
    modal_verbs = {"can", "could", "would", "should", "will"}
    for token in doc:
        if(token.lower_ in modal_verbs):
            return True
    return False

def is_command(user_input):
    """
    Determines if the user's input is a command based on heuristic rules.

    Parameters:
        user_input (str): The user's input string.

    Returns:
        bool: True if the input is a command, False otherwise.
    """
    doc = nlp(user_input)
    # Heuristic rule #1 *************************
    for token in doc:
        if token.tag_ == "VB" and token.dep_ == "ROOT":
            return True
    # Heuristic rule #2 *************************
    for token in doc:
        if token.dep_ != 'nsubj':  # Corrected typo here
            return True
    # Heuristic rule #3 *************************
    command_verbs = {"open", "show", "tell", "find", "give", "go", "bring"}
    for token in doc:
        if token.pos_ == "VERB":
            if token.lemma_ in command_verbs:
                return True
    # Heuristic rule #4 *************************
    if "please" in user_input.lower() or "kindly" in user_input.lower():
        return True
    return False

def get_entities(user_utterance):
    """
    Extracts named entities from the user's utterance using spaCy.

    Parameters:
        user_utterance (str): The user's input string.

    Returns:
        list: A list of tuples containing entity text and its label.
    """
    doc = nlp(user_utterance.lower())
    entities = []
    for ent in doc.ents:
        entities.append((ent.text, ent.label_))
    return entities

def generate_google_link(text):
    """
    Generates a Google search link based on the provided text.

    Parameters:
        text (str): The search query.

    Returns:
        str: A Google search URL.
    """
    search_query = text.replace(" ", "+")
    return f"https://www.google.com/search?q={search_query}"

#  Linguistic Pattern Matching for locations ------------------------------------------------
matcher = Matcher(nlp.vocab)
pattern_location = [
    {"LEMMA": "go"},
    {"LOWER": {"IN": ["to", "into", "toward"]}},
    {"POS": "DET", "OP": "?"},  
    {"POS": "NOUN"}
]
matcher.add('location phrase', [pattern_location])

def generate_google_map_link(location):
    """
    Generates a Google Maps link for the specified location.

    Parameters:
        location (str): The location to search for.

    Returns:
        str: A Google Maps URL.
    """
    search_query = location.replace(" ", "+")
    return f"https://www.google.com/maps/search/?api=1&query={search_query}"

def get_location_from_user(user_input):
    """
    Extracts location information from the user's input using spaCy.

    Parameters:
        user_input (str): The user's input string.

    Returns:
        list: A list of extracted locations.
    """
    doc = nlp(user_input)
    matches = matcher(doc)
    locations = []

    for match_id, start, end in matches:
        locations.append(doc[start+2:end].text)
    
    if not locations:
        entities = [(ent.text, ent.label_) for ent in doc.ents if ent.label_ in ['GPE', 'LOC', 'FAC', 'ORG']]
        if entities:
            locations = [entity[0] for entity in entities]
    
    return locations


#  Understand method ------------------------------------------------------------------------
def understand(utterance1, threshold=60, max_matches_to_return=5):
    """
    Understands the user's utterance and determines the intent based on regex patterns and heuristics.

    Parameters:
        utterance1 (str): The user's input string.
        threshold (int): The minimum score for a fuzzy match to be considered valid.
        max_matches_to_return (int): The maximum number of matches to return.

    Returns:
        tuple: A tuple containing the intent index and response link (if any).
    """
    utterance = utterance1.lower().strip()
    cleaned_utterance = clean_input(utterance)


    # PHASE 1 -------------------------------------------------------------------------------
    # Check against regular expressions first
    for index, string_pattern in enumerate(regEx):
        try:
            pattern = re.compile(f"^{string_pattern}$", re.IGNORECASE)
            regex_match = pattern.search(cleaned_utterance)
            if regex_match:
                return index, None  # Returning the index of the regex match
        except re.error as e:
            print(f"Regex faild: {string_pattern} --Error {e}")
            continue
    # Finding the potential maches for the questions in case of regex doen't work properly. 
    potential_matches = []
    for index, q_pair in enumerate(questions):
        for q in q_pair:  
            score = fuzz.ratio(cleaned_utterance, q)
            if score >= 50:  
                potential_matches.append((index, q, score))

    # Sort matches by score (descending)
    potential_matches.sort(key=lambda x: (-x[2], -len(x[1])))
    if potential_matches:
        best_match_index, best_question, best_score = potential_matches[0]
        if best_score >= threshold:
            return best_match_index, None  # Return only the best match

    # PHASE 2 -------------------------------------------------------------------------------
    # If no matches, chekc the question with using the Spacy Heuristics
    if not potential_matches:
        user_utterance = clean_input(utterance1.strip())
        all_entities = get_entities(user_utterance)


        if is_asking_question(cleaned_utterance):
            if cleaned_utterance.startswith("where") or "location" in cleaned_utterance:
                locations = get_location_from_user(cleaned_utterance)
                if locations:
                    location = locations[0]
                    google_maps_link = generate_google_map_link(location)
                    return -2, f"It seems like you're asking about {location}. Here's a Google Maps link: {google_maps_link}"
            else:
                if all_entities:
                    entity_text, entity_label = all_entities[0]
                    google_link = generate_google_link(entity_text)
                    google_link_question = generate_google_link(cleaned_utterance) # Create a link with the user's question too
                    return -2, f"Sorry, I don't know about {entity_text}. You can check these links: {google_link}\n {google_link_question}"
                else:
                    return -2, "I'm not sure what you're asking. Can you please clarify?"
        
        if is_command(cleaned_utterance):
            if all_entities:  
                entity_text, entity_label = all_entities[0]
                google_link = generate_google_link(entity_text)
                return -2, f"Sorry, I don't know how to do that. You can check this link: {google_link}"
            else:
                return -2, "I'm not sure what you want me to do. Can you please clarify?"
        
    return -1, None

def response_generate(intent, responseLink):
    """
    Generates the answer for user based on the index that is passed.
    Parameters:
        intent (int): index of the array passed by understand method.
        responseLink (str): The link that is passed by understand method. 

    Returns:
        str: The matched answer with the index.
    """
    if intent == -1:
        return "Sorry, I don't know the answer to that!"
    elif intent == -2:
        return responseLink
    return ' '.join(answers[intent]).strip()

def clean_input(user_input):
    """
    Cleans the user input by removing special characters and excessive spaces.

    Parameters:
        user_input (str): The user's input string.

    Returns:
        str: The cleaned input string.
    """
    cleaned_input = re.sub(r"[^\w\s'?.]", '', user_input) # Remove special characters except for alphanumeric, spaces, and question marks
    cleaned_input = re.sub(r'\s+', ' ', cleaned_input) # Replace multiple spaces with a single space
    return cleaned_input

def main():
    print("Hello there, this is a chatbot that knows about Art Therapy.\nYou can ask any question you want...\n")
    
    while True:
        user_input = input("\n >>> ")  # Get user input
        if user_input.lower() == "goodbye":
            print("Goodbye, have a nice day!")
            break
        intent, responseLink = understand(user_input)  # Process user input
        # Generate and print response
        response = response_generate(intent, responseLink)  # Generate response
        print(response)

if __name__ == "__main__":
    main()