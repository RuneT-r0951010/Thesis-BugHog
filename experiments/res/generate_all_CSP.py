import os
import shutil
import json
import re

# Generate CSP json with given value
def generate_CSP_json_with_value(csp_value):
    header_content = [
        {
            "key": "Content-Security-Policy",
            "value": csp_value
        }
    ]
    return json.dumps(header_content, indent=4)


# Extract the CSP value from a header.json file
def extract_csp_from_header(test_header):
    try:
        with open(test_header, 'r') as file:
            headers = json.load(file)
            for header in headers:
                if header.get("key") == "Content-Security-Policy":
                    return header.get("value")
    except Exception as e:
        print(f"Error reading header file: {e}")
    return None


def is_json_empty(file_path):
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)  # Load JSON into a Python object
        return not bool(data)  # Return True if the object is empty, False otherwise
    
    except:
        return True  # Consider invalid JSON as effectively empty
    

def remove_csp_from_header(test_header):
    try:
        with open(test_header, 'r') as file:
            headers = json.load(file)
        
        filtered_headers = [header for header in headers if header.get("key") != "Content-Security-Policy"] # Filter out entries with the specified key
       
        with open(test_header, 'w') as file:  # Save the filtered headers back to the file
            json.dump(filtered_headers, file, indent=4)

        if is_json_empty(test_header):
            os.remove(test_header)

    except Exception as e:
        print(f"Error processing header file: {e}")
        

# Excract the CSP value (content) from a meta tag in a HTML file
def extract_csp_from_meta_tag(test_index):
    with open(test_index, 'r') as file:
        content = file.read()
        match = re.search(r'<meta http-equiv="content-security-policy" content="([^"]+)"', content)
        if match:
            return match.group(1)
    return None


def insert_meta_tag(page, meta_content):
    with open(page, 'r') as file:
        content = file.read()
    # Check if <head> exists, and insert it if missing
    if not re.search(r'<head>', content, re.IGNORECASE):
        content = f"<head>\n{meta_content}\n</head>\n" + content
    else:
        # Insert meta_content inside the existing <head>
        content = re.sub(r'(<head.*?>)', f'\\1\n    {meta_content}', content, count=1)
    with open(page, 'w') as file:
        file.write(content)


# Remove content between <head></head>
def remove_head_content(page):
    with open(page, 'r') as file:
        content = file.read()
    updated_content = re.sub(r'<head>.*?</head>', '<head></head>', content, flags=re.DOTALL)
    with open(page, 'w') as file:
        file.write(updated_content)


CSP_tests_folder = "../pages/CSP"

# Iterate over all test folders
for PoC_folder in [os.path.join(CSP_tests_folder, d) for d in os.listdir(CSP_tests_folder) if os.path.isdir(os.path.join(CSP_tests_folder, d))]:
    print(f"Processing folder: {PoC_folder}")
    new_PoC_folder = f"{PoC_folder}-CSP"

    # Check if the destination folder exists
    if os.path.exists(new_PoC_folder):
        # Remove the existing destination folder and its contents
        shutil.rmtree(new_PoC_folder)
        print(f"Existing directory {new_PoC_folder} deleted.")

    os.makedirs(os.path.dirname(new_PoC_folder), exist_ok=True)
    shutil.copytree(PoC_folder, new_PoC_folder)
    os.chmod(new_PoC_folder, 0o777)

    # Iterate over subdirectories in the test folder
    for subdir in os.listdir(new_PoC_folder):  # subdir currently could be a.test or leak.test
        full_subdir_path = os.path.join(new_PoC_folder, subdir)  # Combine the parent folder with the subdirectory name
        #print(subdir)

        _, ext = os.path.splitext(subdir)

        if os.path.isdir(full_subdir_path):  # Use full path for isdir check
            #print(f"The folder {subdir} exists.")
            
            # Continue working with the folder
            if ext != ".txt":
                #print("is dir")
                os.chmod(full_subdir_path, 0o777)  # Set permissions on the folder
                for subsubdir in os.listdir(full_subdir_path):  # subsubdir in that folder there could be more folders: main, helper, ....
                    full_subsubdir_path = os.path.join(full_subdir_path, subsubdir)  # Full path of subsubdir

                    # in these files should be the index and headers if  present
                    test_index = os.path.join(full_subsubdir_path, "index.html")
                    test_header = os.path.join(full_subsubdir_path, "headers.json")

                    if os.path.exists(test_index):
                        if os.path.exists(test_header):
                            print("Header file exists, generating test for putting CSP in metadata instead of header")
                            csp_value = extract_csp_from_header(test_header)

                            remove_csp_from_header(test_header)
                            #os.remove(test_header)

                            meta_content = f'<meta http-equiv="content-security-policy" content="{csp_value}">'
                            insert_meta_tag(test_index, meta_content)

                        else:
                            print("Header file does not exist, generating test for putting CSP in header instead of metadata")

                            csp_value = extract_csp_from_meta_tag(test_index)
                            if not csp_value:
                                print("The csp_value is empty.")
                            else:
                                print("The variable is not empty.")

                                header_content = generate_CSP_json_with_value(csp_value)

                                os.makedirs(os.path.dirname(test_header), exist_ok=True)
                                with open(test_header, 'w') as file:
                                    file.write(header_content)

                                remove_head_content(test_index)
        else:
            print(f"Error: {subdir} is not a valid directory or does not exist.")
        
            
        
"""
test_main_folder = os.path.join(PoC_folder, "leak.test", "main")
if not os.path.exists(test_main_folder):
    test_main_folder = os.path.join(PoC_folder, "a.test", "main")

test_index = os.path.join(test_main_folder, "index.html")
test_header = os.path.join(test_main_folder, "headers.json")

generated_test = os.path.join(PoC_folder, "generated_tests", "CSP")
generated_test_index = os.path.join(generated_test, "index.html")
generated_test_header = os.path.join(generated_test, "headers.json")

if os.path.exists(test_header):
    print("Header file exists, generating test for putting CSP in metadata instead of header")
    
    csp_value = extract_csp_from_header(test_header)
    
    os.makedirs(os.path.dirname(generated_test_index), exist_ok=True)
    shutil.copy(test_index, generated_test_index)
    
    meta_content = f'<meta http-equiv="content-security-policy" content="{csp_value}">'
    insert_meta_tag(generated_test_index, meta_content)
else:
    print("Header file does not exist, generating test for putting CSP in header instead of metadata")
    
    csp_value = extract_csp_from_meta_tag(test_index)
    header_content = generate_CSP_json_with_value(csp_value)
    
    os.makedirs(os.path.dirname(generated_test_header), exist_ok=True)
    with open(generated_test_header, 'w') as file:
        file.write(header_content)
    
    os.makedirs(os.path.dirname(generated_test_index), exist_ok=True)
    shutil.copy(test_index, generated_test_index)
    remove_head_content(generated_test_index)

print("All tests processed.")

"""