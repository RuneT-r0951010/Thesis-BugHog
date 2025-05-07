import os
import json
import BugReportBuilder

CSP_TESTS_FOLDER = "../../pages/CSP"
VALID_POCS = 76

# Assign a role to the GenAI
role_file = "Prompts/role.txt"
with open(role_file, "r") as f:
    role = f.read()

# Define the context the GenAI needs to follow when giving an output
context_file = "Prompts/context.txt"
with open(context_file, "r") as f:
    context = f.read()

# Specify the goal for the GenAI
goal_file = "Prompts/goal.txt"
with open(goal_file, "r") as f:
    goal = f.read()

class PromptBuilder:
    def __init__(self, sorted_PoCs):
        self.sorted_PoCs = sorted_PoCs
        self.bug_report_builder = BugReportBuilder.BugReportBuilder()
        self.report_path = None # is declared in subclasses
        
    
    def get_prompt_message(self, start_index: int, n: int, num_experiment_generation_per_prompt: int, report_input = False):
        raise NotImplementedError 

    def _write_report_to_file(self, messages, start_index, n):
        with open(f"{self.report_path}/input_start_{start_index}_with_{n}_examples.txt", "w", encoding="utf-8") as f:
            json.dump(messages, f, indent=4)
            print(f"Wrote to file: {self.report_path}/input_start_{start_index}_with_{n}_examples.txt")
    

class JSONPromptBuilder(PromptBuilder):
    def __init__(self, sorted_PoCs):
        super().__init__(sorted_PoCs)
        self.report_path = "Prompts/Input/JSON"
    

    def __get_expected_test_solution(self, experiment_path: str):
        solution_tree = {}

        for dirpath, _, filenames in os.walk(experiment_path):
            rel_path = os.path.relpath(dirpath, experiment_path)
            parts = rel_path.split(os.sep) if rel_path != "." else []
            current = solution_tree
            for part in parts:
                current = current.setdefault(part, {})
            
            for filename in filenames:
                if filename.startswith('.DS_'):
                    continue  # Ignore macOS system files like .DS_Store

                file_path = os.path.join(dirpath, filename)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                except Exception as e:
                    content = f"<<ERROR READING FILE: {e}>>"
                current[filename] = content

        experiment_name = os.path.basename(os.path.abspath(experiment_path))
        return {experiment_name: solution_tree}


    # Get n examples in JSON structure
    # [
    #   {
    #       "BugReport" : "...""
    #       "TestSolution" : "...""
    #   },
    # ]
    def __get_n_shot_examples(self, bug_index: int, n: int, seen_pocs: list):
        num_examples = 0
        n_shot_examples = []

        while (num_examples <= n):
            bug_id = self.sorted_PoCs[bug_index]
            bug_index = (bug_index + 1) % VALID_POCS

            report = self.bug_report_builder.try_get_bug_report(bug_id) # Fetch the bug report or corresponding url

            if (report):
                experiment_folder_path = os.path.join(CSP_TESTS_FOLDER, bug_id) 

                expected_test = {
                    "BugReport" : report,
                    "TestSolution" : self.__get_expected_test_solution(experiment_folder_path)
                }   

                n_shot_examples.append(expected_test) 
                num_examples += 1
                seen_pocs.append(bug_id)

        return n_shot_examples, bug_index


    def get_prompt_message(self, start_index: int, n: int , num_experiment_generation_per_prompt: int, generated_pocs: list, report_input = False):
            seen_pocs = []
            n_shot_examples, bug_index = self.__get_n_shot_examples(start_index, n, seen_pocs)
            tasks = []
            
            num_generated = 0
            while (num_generated < num_experiment_generation_per_prompt and len(seen_pocs) < VALID_POCS):
                bug_id = self.sorted_PoCs[bug_index]

                if (bug_id not in seen_pocs and bug_id not in generated_pocs and '-' not in bug_id):
                    report = self.bug_report_builder.try_get_bug_report(bug_id)

                    if (report):
                        seen_pocs.append(bug_id)
                        generated_pocs.append(bug_id)
                        num_generated += 1
                        task_prompt = {f"BugID={bug_id}": report}
                        tasks.append(task_prompt)

                bug_index = (bug_index + 1) % VALID_POCS

            result_prompt = {
                "Role" : role,
                "Context": context,
                "Goal" : goal,
                "Examples" : n_shot_examples,
            }

            messages = [
                {
                    "role": "system", 
                    "content": [
                        {
                            "type" : "text",
                            "text" : json.dumps(result_prompt)
                        }
                    ]
                }
            ]

            for task in tasks:
                for bug_id, content in task.items():
                    messages.append({
                        "role": "user",
                        "content": f"Generate a test in the same JSON format as provided and NO additional information for:{bug_id}: {content}"
                    })

            if (report_input):
                super()._write_report_to_file(messages, start_index, n)
        
            return messages
    


class TextPromptBuilder(PromptBuilder):
    def __init__(self, sorted_PoCs):
        super().__init__(sorted_PoCs)
        self.report_path = "Prompts/Input/Plain"
    

    def get_prompt_message(self, start_index: int, n: int, num_experiment_generation_per_prompt: int, report_input = False):
        n_shot_examples, bug_index = self.__get_n_shot_examples(start_index, n)
        result_prompt = role + context + goal + n_shot_examples
        generated_pocs = []
        
        num_generated = 0
        messages = [
            {"role": "system", "content": f"{result_prompt}\nNow follow the framework and examples to generate a test for new bug reports."}
        ]

        while (num_generated < num_experiment_generation_per_prompt and len(generated_pocs) < VALID_POCS):
            bug_id = self.sorted_PoCs[bug_index]

            if ('-' not in bug_id): # these are duplicates
                report = self.bug_report_builder.try_get_bug_report(bug_id)

                if (report):
                    generated_pocs.append(bug_id)
                    num_generated += 1
                    messages.append({"role": "user", "content": f"Generate a test for the following bug report (ID: {bug_id}):\n-START REPORT-\n{report}\n-END REPORT-\n\n"})
            
            bug_index = (bug_index + 1) % VALID_POCS

        # Save content prompt
        
        if (report_input):
            super()._write_report_to_file(messages, start_index, n)

        return messages
    


    # Function to generate the expected file structure in plain text
    # [experiment]
    # -domain1
    # --page1
    # ---index.html
    # ---headers.json
    # --page2
    # ---...
    # -url_queue.txt
    def __get_test_structure(self, experiment_path: str):
        bug_id = os.path.basename(os.path.normpath(experiment_path))
        prompt_file_structure = f"Expected solution:\nFolder structure:\n[{bug_id}]\n"

        for domain_name in os.listdir(experiment_path):  # loop over domain folders, could be a.test, leak.test ...
            domain_path = os.path.join(experiment_path, domain_name) 
            prompt_file_structure += f"-{domain_name}\n"

            if (not os.path.isfile(domain_path)):         # if not url_queue.txt (not file)
                for page_name in os.listdir(domain_path): # loop over page folders, could be main, helper, worker ...
                    page_path = os.path.join(domain_path, page_name)
                    prompt_file_structure += f"--{page_name}\n"

                    for file in os.listdir(page_path): # loop of files, could be index.html, headers.json, ...
                        prompt_file_structure += f"---{file}\n"
                    
        prompt_file_structure += "\n"
        return prompt_file_structure


    def __get_expected_test_solution(self, experiment_path: str):
        prompt_file_structure = self.__get_test_structure(experiment_path)
        solution = prompt_file_structure

        for domain_name in os.listdir(experiment_path):  # domain folder be a.test, leak.test ...
            domain_path = os.path.join(experiment_path, domain_name) 

            # if domain element is a file, it's the URL queue
            if (os.path.isfile(domain_path)):
                with open(domain_path, "r") as f:
                    url_queue_content = f.read()
                    solution += f"/url_queue.txt:\n{url_queue_content}\n\n"

            # else it is a page folder
            else:
                for page_name in os.listdir(domain_path): # loop over page folders, could be main, helper, worker ...
                    page_path = os.path.join(domain_path, page_name)

                    for file_name in os.listdir(page_path): # loop over files
                        file_path = os.path.join(page_path, file_name) 
                        with open(file_path, "r") as f:
                            file_content = f.read()
                            solution += f"/{domain_name}/{page_name}/{file_name}:\n{file_content}\n\n"
        return solution
    

    def __get_n_shot_examples(self, bug_index: int, n: int):
        num_examples = 0    # Number of examples added to the prompt
        n_shot_prompt = ""  # resulting prompt with n examples

        while(num_examples <= n):
            bug_id = self.sorted_PoCs[bug_index]
            bug_index = (bug_index + 1) % VALID_POCS

            poc_folder_path = os.path.join(CSP_TESTS_FOLDER, bug_id) 

            bug_report = self.bug_report_builder.try_get_bug_report(bug_id)

            report = f"-START REPORT-\n{bug_report}\n-END REPORT-\n" # Fetch the bug report or corresponding url
            if (bug_report):
                expected_test = self.__get_expected_test_solution(poc_folder_path)   # Generate the expected test solution for the bug that was reported
                n_shot_prompt += report + expected_test
                num_examples += 1
        
        return n_shot_prompt, bug_index
    
    

    

        