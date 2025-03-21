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
def extract_csp_from_header(header):
    try:
        with open(header, 'r') as file:
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
    

def remove_csp_from_header(header):
    try:
        with open(header, 'r') as file:
            headers = json.load(file)
        
        filtered_headers = [header for header in headers if header.get("key") != "Content-Security-Policy"] # Filter out entries with the specified key

        with open(header, 'w') as file:  # Save the filtered headers back to the file
            json.dump(filtered_headers, file, indent=4)

        if is_json_empty(header):
            os.chmod(header, 0o666)  # Set deletion permission
            os.remove(header)

    except Exception as e:
        print(f"Error processing header file: {e}")
        
# Excract the CSP value (content) from a meta tag in a HTML file
def extract_csp_from_meta_tag(index):
    with open(index, 'r') as file:
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
    # Match the <head>...</head> section
    head_pattern = re.compile(r'(<head.*?>)(.*?)(</head>)', re.DOTALL)
    def remove_meta_tags(match):
        head_open = match.group(1)  # <head> or <head attributes>
        head_content = match.group(2)  # Content inside <head>
        head_close = match.group(3)  # </head>

        # Remove only <meta> tags inside the <head> section
        cleaned_head_content = re.sub(r'<meta[^>]*?>', '', head_content)

        return head_open + cleaned_head_content + head_close

    # Apply the meta removal only inside <head>
    updated_content = head_pattern.sub(remove_meta_tags, content)

    with open(page, 'w', encoding='utf-8') as file:
        file.write(updated_content)

    

# Headers.json => meta tag
def header_to_meta(index, header):
    csp_value = extract_csp_from_header(header)
    remove_csp_from_header(header)
    meta_content = f'<meta http-equiv="content-security-policy" content="{csp_value}">'
    insert_meta_tag(index, meta_content)

# meta tag => headers.json
def meta_to_header(index, header):
    csp_value = extract_csp_from_meta_tag(index)
    if csp_value:
        header_content = generate_CSP_json_with_value(csp_value)
        os.makedirs(os.path.dirname(header), exist_ok=True)
        with open(header, 'w') as file:
            file.write(header_content)
        remove_head_content(index)

# bug_id-CSP
def update_bug_id_in_content(bug_id, new_relative_path):
    try:
        with open(new_relative_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        updated_content = re.sub(re.escape(bug_id), f"{bug_id}-CSP", content, flags=re.DOTALL)
        
        with open(new_relative_path, 'w', encoding="utf-8") as f:
            f.write(updated_content)
    except:
        return


CSP_tests_folder = "../pages/CSP"
# Iterate over all test folders
for PoC_folder in [os.path.join(CSP_tests_folder, d) for d in os.listdir(CSP_tests_folder) if os.path.isdir(os.path.join(CSP_tests_folder, d))]:
    new_PoC_folder = f"{PoC_folder}-CSP"
    bug_id = os.path.basename(os.path.normpath(PoC_folder))

    # Check if the destination folder exists
    if os.path.exists(new_PoC_folder):
        # Remove the existing destination folder and its contents
        shutil.rmtree(new_PoC_folder)
        print(f"Existing directory {new_PoC_folder} deleted.")

    os.makedirs(os.path.dirname(new_PoC_folder), exist_ok=True)
    shutil.copytree(PoC_folder, new_PoC_folder)
    os.chmod(new_PoC_folder, 0o777)

    # Iterate over subdirectories in the test folder
    for domain_folder in os.listdir(new_PoC_folder):  # domain_folder currently could be a.test or leak.test
        relative_path = os.path.join(new_PoC_folder, domain_folder)  # Combine the parent folder with the subdirectory name
        _, ext = os.path.splitext(domain_folder)

        update_bug_id_in_content(bug_id, relative_path) # for when its queue.txt

        if os.path.isdir(relative_path):  # Use full path for isdir check

            for page_folder, _, files in os.walk(relative_path):
                for file in files:
                    new_relative_path = os.path.join(page_folder, file)
                    update_bug_id_in_content(bug_id, new_relative_path)
            
                index = os.path.join(page_folder, "index.html")
                header = os.path.join(page_folder, "headers.json")

                if os.path.exists(index):
                    if os.path.exists(header): 
                        # Headers.json => meta tag
                        header_to_meta(index, header)

                    else: 
                        # Meta tag => headers,json
                        meta_to_header(index, header)

        else:
            continue