import datetime
import sys
sys.path.append('..')
from draft_notes_utils import *
import ast
from tqdm import tqdm 
import json 
import concurrent.futures
import uuid



def create_background(document_path):
    # Give context and prompt instructions
    initial_messages, system_prompt = policy_background_initial_prompt()

    # Extract text from input document
    # Not necessary unless you want to explore document
    # document_text = extract_text(document_path)

    # Create document submission prompt
    document_submission_prompt = document_submission_message(document_path)
    print('Document has been processed')

    # Get LLM response 
    post_document_messages, search_strings = document_submission_response(initial_messages, system_prompt, document_submission_prompt)
    print('Generate search strings for the APIs')
    # Get search strings
    legislation_search_string, newscatcher_search_string = extract_search_strings(search_strings)
    print('Split the search string')
    print(newscatcher_search_string)
    # Prompt Newscatcher API
    newscatcher_submission_prompt = newscatcher_api_call(newscatcher_search_string)
    post_newscatcher_messages     = add_news_data(post_document_messages, system_prompt, newscatcher_submission_prompt)

    # Draft the explanatory notes
    final_messages, policy_background = draft_policy_background(post_newscatcher_messages, system_prompt)
    policy_background = "{" + policy_background

    return policy_background


def create_explanatory(legislation_path,type='local'):

    if type == 'local':
        # read JSON
        with open(legislation_path) as f:
            legislation = json.load(f)

    
        name = legislation['metadata']['title'] + ' (Explanatory Notes)'

    if type == 'local':
        titles,text, section_numbers = parse_act(legislation_path)
    else:
        titles,text = get_legislation(legislation_path)
    
    def explain_section(title, text_item, section_number):
        print(f"Explaining section {title}...")
        explained_section = get_commentary(title, section_number, text_item, "claude-3-sonnet-20240229")
        return explained_section

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = []
        for title, text_item, section_number in zip(titles,text,section_numbers):
            future = executor.submit(explain_section, title,text_item,section_number)
            futures.append(future)
        
        explained_sections = [future.result() for future in concurrent.futures.as_completed(futures)]

    if type != 'local':
        doc_path = legislation_path.replace('/','_') + ' (Explanatory Notes)'
        title = doc_path
    else:
        doc_path = name
        title = name

    document_path = './Data/Skateboard Act 2024 (Explanatory Notes).pdf'
    policy_background = create_background(document_path)
    filename = 'policy_background.txt'
    with open(filename,'w', encoding='utf-8') as file:
        file.write(policy_background)
    print('Saved to policy_background.txt')

    section_title = [section_number + " " + title for section_number, title in zip(section_numbers, titles)]
    section_title_sorted = sorted(section_title, key=sort_sections)
    explained_sections_sorted = sorted(explained_sections, key=sort_sections)   

    doc_path = 'data/' + doc_path

    create_explanation_document(doc_path, section_title_sorted, explained_sections_sorted ,title, policy_background)

# file_path = "data/Skateboard (Regulation) Act 2024/act.json"
# create_legislation(file_path,'local')

url_path = "Documents/act.json"
create_explanatory(url_path,'local')






# # read JSON 
# with open("skateboard_act.json") as f:
#     legislation = json.load(f)

# create_document(legislation)