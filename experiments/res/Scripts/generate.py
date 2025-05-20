from openai import OpenAI
from pydantic import BaseModel
import os
import re
import json
import PromptBuilder

client = OpenAI(api_key="KEYGOESHERE", timeout=60)

CSP_tests_folder = "../../pages/CSP"

reports_folder = "Reports"
reports = [f for f in os.listdir(reports_folder) if os.path.isfile(os.path.join(reports_folder, f))]
VALID_POCS = len(reports)

PoC_folders = [
    d for d in os.listdir(CSP_tests_folder)
    if os.path.isdir(os.path.join(CSP_tests_folder, d)) and "-" not in d
]

chromium_bugs = [bug_id for bug_id in PoC_folders if bug_id.startswith("c")]
firefox_bugs = [bug_id for bug_id in PoC_folders if bug_id.startswith("f")]

sorted_chromium_bugs = sorted(chromium_bugs, key=lambda x: int(x[1:]))
sorted_firefox_bugs = sorted(firefox_bugs, key=lambda x: int(x[1:]))

# Interleave them
sorted_PoCs = [item for pair in zip(sorted_chromium_bugs, sorted_firefox_bugs) for item in pair]

# Add remaining items from the longer list, if any
longer_tail = sorted_chromium_bugs[len(sorted_firefox_bugs):] if len(sorted_chromium_bugs) > len(sorted_firefox_bugs) else sorted_firefox_bugs[len(sorted_chromium_bugs):]
sorted_PoCs.extend(longer_tail)

# Define minimum number of examples to be used to insert in the prompt
MINIMUM_EXAMPLES = VALID_POCS // 2
# Define maximum number of examples to be insterted in prompt (should always be > MINIMUM_EXAMPLES)
MAXIMUM_EXAMPLES = MINIMUM_EXAMPLES + 1
# Define how many experiments should be generated in 1 prompt
NUM_EXPERIMENT_GENERATION_PER_PROMPT = 1

# Use URLS instead of scraped content (should be false for now as visiting links is not yet possible)
USE_URLS = False

GenAI_test_folder_name = f"GenAI-{MINIMUM_EXAMPLES}-Examples-4o-UpdatedPrompt"
GenAI_tests_folder = f"../../pages/{GenAI_test_folder_name}"

# Use JSON formatted input, if false: use plain text
USE_JSON = True
if (USE_JSON):
    prompt_builder = PromptBuilder.JSONPromptBuilder(sorted_PoCs, GenAI_test_folder_name)
else:
    prompt_builder = PromptBuilder.TextPromptBuilder(sorted_PoCs, GenAI_test_folder_name)
# Use the beta formatted output prompt structure
USE_FORMATTED_OUTPUT = False

# Debug mode, if true no prompt will be sent
DEBUG = False

# Some safety checks
if (MAXIMUM_EXAMPLES - MINIMUM_EXAMPLES <= 0):
    print(f"Maximum should always be greater than minimum, MAXIMUM_EXAMPLES >= MINIMUM_EXAMPLES + 1")
    SystemExit() 
if (MAXIMUM_EXAMPLES > VALID_POCS):
    print(f"Maximum should not be higher than number of valid tests")
    SystemExit() 

# Defenition of expected response object
class Page(BaseModel):
    file_extension: str
    file_name: str
    test_content: str
class PageFolder(BaseModel):
    page_folder_name: str
    pages: list[Page]
class DomainFolder(BaseModel):
    domain_folder_name: str
    page_folders: list[PageFolder]
class CompleteTest(BaseModel):
    bug_id: str
    domain_folders: list[DomainFolder]
    url_queue_content: str
class GenereatedTests(BaseModel):
    generated_tests : list[CompleteTest]

def extract_json_block(text):
    match = re.search(r'{[\s\S]*}', text)
    if match:
        try:
            json_data = json.loads(match.group())
            return json_data
        except json.JSONDecodeError as e:
            raise
    else:
        print("[!] No JSON block found.")
        raise ValueError("No valid JSON block found in the input.")

def parse_json_to_files(data, base_path):
    def recurse(current_data, current_path):
        for key, value in current_data.items():
            if isinstance(value, str): # It's a file
                print("this is a string: " + value)
                os.makedirs(current_path, exist_ok=True)
                full_path = os.path.join(current_path, key)
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(value)
            else:  # It's a folder
                recurse(value, os.path.join(current_path, key))
    recurse(data, base_path)

def plain_response(messages, n, GenAI_tests_folder, i):
    response = client.chat.completions.create(
        model="gpt-4o", # try mini??? or gpt-4 as its said to have better code generation
        messages=messages, # type: ignore
    )
    print(response)
    response_content = response.choices[0].message.content or ""

    if (USE_JSON):
        data = extract_json_block(response_content)
        parse_json_to_files(data, GenAI_tests_folder)

    output_file = f"Prompts/Output/{GenAI_test_folder_name}"
    os.makedirs(output_file, exist_ok=True) 
    with open(f"{output_file}/output_with_{n}_examples{i}.txt", "w",) as f:
        f.write(response_content)

        f.write(f"\n\n\nPrompt tokens: {response.usage.prompt_tokens}")
        f.write(f"Completion tokens: {response.usage.completion_tokens}")
        f.write(f"Total tokens: {response.usage.total_tokens}")


def beta_formatted_response(messages, n, GenAI_tests_folder):
    response = client.beta.chat.completions.parse(
        model="gpt-4o",
        messages=messages, # type: ignore
        response_format=CompleteTest,
    )

    print(response)
    response_content = response.choices[0].message 

    if (response_content.refusal):
        print(response_content.refusal)

    else:
        print(response_content.parsed)
    
        test = response_content.parsed
        if (test is not None):
            # Save content
            # with open(f"Prompts/Output/Structured/output_bug_{test.bug_id}_with_{n}_examples.txt", "w",) as f: # also save output in file
            #     f.write(f"{test}\n")

            test_folder_path = GenAI_tests_folder + f"/{test.bug_id}" 
            os.makedirs(test_folder_path, exist_ok=True) # generate test folder

            if (test.url_queue_content.strip()): # write to URL queque if not empty
                with open(f"{test_folder_path}/url_queque.txt", "w") as q:
                    q.write(test.url_queue_content)

            for domain_folder in test.domain_folders:
                domain_folder_path = test_folder_path + f"/{domain_folder.domain_folder_name}"
                os.makedirs(domain_folder_path, exist_ok=True) # generate domain folder

                for page_folder in domain_folder.page_folders:
                    page_folder_path = domain_folder_path + f"/{page_folder.page_folder_name}"
                    os.makedirs(page_folder_path, exist_ok=True) # generate page folder

                    for page in page_folder.pages:
                        with open(f"{page_folder_path}/{page.file_name}.{page.file_extension}", "w") as t:
                            t.write(page.test_content)

            print(f"generated for bug: {test.bug_id}")



def generate_tests(start_index, n, messages):
    try:
        if (USE_FORMATTED_OUTPUT):
            os.makedirs(GenAI_tests_folder, exist_ok=True) 
            beta_formatted_response(messages, n, GenAI_tests_folder)
        else:
            os.makedirs(GenAI_tests_folder, exist_ok=True) 
            plain_response(messages, n, GenAI_tests_folder, start_index)

    except Exception as e:
        print(f"An exception occurred: {type(e).__name__} - {e}")



for n in range(MINIMUM_EXAMPLES, MAXIMUM_EXAMPLES):
    start_index = 0
    generated_pocs = []
    while (start_index < VALID_POCS):
        messages = prompt_builder.get_prompt_message(start_index, n, NUM_EXPERIMENT_GENERATION_PER_PROMPT, generated_pocs, report_input=True)

        if (not DEBUG):
            generate_tests(start_index, n, messages)

        start_index += NUM_EXPERIMENT_GENERATION_PER_PROMPT 

    
     
 

    

