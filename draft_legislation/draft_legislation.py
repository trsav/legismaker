import datetime
from draft_legislation_utils import *
import ast
from tqdm import tqdm 
import json 
import concurrent.futures
import multiprocessing






def create_legislation(proposed_act):

    legislation = {}
    # initialise metadata
    metadata = {}
    # initialise sections of legislation
    sections = []
    # current year
    metadata["modified"] = str(datetime.datetime.now(datetime.UTC))
    metadata["group"] = "Group 29"
    metadata["type"] = "text"
    metadata["format"] = "text/xml"
    metadata["language"] = "en"

    # read in proposed proposed_act
    with open(proposed_act) as f:
        proposed_act = f.read()

    # model = "claude-3-haiku-20240307"
    # model = "claude-3-opus-20240229"
    # model = "claude-3-opus-20240229"

    print('Deciding on what this act is about...')
    concept = get_concept(proposed_act,"claude-3-haiku-20240307")
    # capitalise each word in concept
    concept = " ".join([word.capitalize() for word in concept.split()])
    metadata["title"] = f"{concept} (Regulation) Act {str(datetime.datetime.now().year)}"

    try:
        os.mkdir(f"data/{metadata['title']}")
    except:
        pass


    print('Structuring the act...')
    headings_explanations,prompt,context = get_structure(proposed_act,"claude-3-opus-20240229")
    section_headings = [heading_explanation[0] for heading_explanation in headings_explanations]

    # save headings and explanations as JSON 
    with open(f"data/{metadata['title']}/structure.json", "w") as f:
        f.write(json.dumps(headings_explanations, indent=4))
    
    with open(f"data/{metadata['title']}/structure.json", "r") as f:
        headings_explanations = json.load(f)
    
    section_headings = [heading_explanation[0] for heading_explanation in headings_explanations]


    create_draft_document(headings_explanations,metadata,prompt,context)

    def process_section(heading_explanation, i):

        section_name = heading_explanation[0]
        explanation = heading_explanation[1]
        print(section_name, explanation)
        
        print(f'Drafting the section on {section_name}...')

        if 'interpretative' in section_name.lower():
            print(f'Thinking about the ways {concept} can be interpreted...')
            draft_section,draft_prompt,draft_context = get_interpretation(concept,"claude-3-opus-20240229")
            tuned_prompt = None
            tuned_context = None
            first_section = {
                "title": "Main interpretative provisions",
                "content": draft_section,
            }
            print('Proofreading the interpretative provisions...')
            complete_section,proofed_prompt,proofed_context = proofread_section(None,first_section,"claude-3-opus-20240229")
            complete_section['name'] = f"Section {i+1}."

            tuned_prompt = None
            tuned_context = None
            tuned_section = None
            return draft_section,tuned_section,complete_section,draft_prompt,tuned_prompt,proofed_prompt,draft_context,tuned_context,proofed_context

        else:
            draft_section,draft_prompt,draft_context = draft_section_call(proposed_act, section_name, explanation,headings_explanations, "claude-3-opus-20240229")
            print(f'Passing the draft on {section_name} onto the copywriter...')
            tuned_section,tuned_prompt,tuned_context = finetune_section(proposed_act, section_name, draft_section,heading_explanation,explanation, "claude-3-opus-20240229")
            tuned_section = f"""
            title: {section_name}\\n""" + tuned_section
            
            augmented_headings = [f"Section {j+2}. {section_headings[j]}" for j in range(len(section_headings))]
            
            print(f'Getting legal to proofread the section on {section_name}...')
            complete_section,proofed_prompt,proofed_context  = proofread_section(augmented_headings, tuned_section, "claude-3-opus-20240229")

            complete_section['name'] = f"Section {i+1}."
            return draft_section,tuned_section,complete_section,draft_prompt,tuned_prompt,proofed_prompt,draft_context,tuned_context,proofed_context

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = []
        for i, section_info in enumerate(headings_explanations):
            future = executor.submit(process_section, section_info, i)
            futures.append(future)
        
        sections = [future.result() for future in concurrent.futures.as_completed(futures)]



    sections_done = [section[2] for section in sections]
    sections_done_text = [str(section[2]) for section in sections]
    sections_tuned = [str(section[1]) for section in sections]
    sections_draft = [str(section[0]) for section in sections]

    draft_prompts = [section[3] for section in sections]
    tuned_prompts = [section[4] for section in sections]
    proofed_prompts = [section[5] for section in sections]
    draft_contexts = [section[6] for section in sections]
    tuned_contexts = [section[7] for section in sections]
    proofed_contexts = [section[8] for section in sections]

    str_date = datetime.datetime.now().strftime("%d %B %Y")

    commencement = {
        "title": "Citation, commencement and extent",
        "name": "Section 1.",
        "content":[
            {
                "subsection": "(1)",
                "text": "This Act may be cited as the " + metadata["title"] + "."
            },
            {
                "subsection": "(2)",
                "text": f"This Act comes into force on {str_date}."
            },
            {
                "subsection": "(3)",
                "text": "This Act extends to England and Wales."
            }
        ]
    }

    for section in sections_done:
        # get int from section_name
        num = int(section['name'].split('.')[0].split('Section ')[-1])
        num += 1
        section['name'] = f"Section {num}."
    
    # add commencement to start
    sections_done.insert(0, commencement)

    legislation["sections"] = sections_done
    legislation["metadata"] = metadata

    print('Done!')
    # save as JSON
    with open(f"data/{metadata['title']}/act.json", "w") as f:
        f.write(json.dumps(legislation, indent=4))

    section_titles = [section['title'] for section in legislation['sections']]
    
    print('Writing report...')

    create_document(legislation, "final")
    path = f"data/{metadata['title']}/draft_interpretable.pdf"
    create_intermediary_document(section_titles,sections_draft, draft_prompts, draft_contexts, path,metadata['title'],'Drafted')
    path = f"data/{metadata['title']}/tuned_interpretable.pdf"
    create_intermediary_document(section_titles,sections_tuned, tuned_prompts, tuned_contexts, path,metadata['title'],'Tuned')
    path = f"data/{metadata['title']}/proofed_interpretable.pdf"
    create_intermediary_document(section_titles,sections_done_text, proofed_prompts, proofed_contexts, path,metadata['title'],'Proofed')

    return legislation


# import time 
# start = time.time()
# proposed_act_path = "data/skateboard.txt"
# create_legislation(proposed_act_path)
# proposed_act_path = "data/ice_cream.txt"
# create_legislation(proposed_act_path)
proposed_act_path = "data/coffee.txt"
create_legislation(proposed_act_path)
# proposed_act_path = "data/legislation.txt"
# create_legislation(proposed_act_path)
# proposed_act_path = "data/robot.txt"
# create_legislation(proposed_act_path)
# end = time.time()

# print(f"Time taken: {end-start} seconds")
# print(f"Time taken: {(end-start)/60} minutes")

# # read JSON 
# with open("skateboard_act.json") as f:
#     legislation = json.load(f)

# create_document(legislation)