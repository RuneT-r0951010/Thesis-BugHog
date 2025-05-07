import os

def replace_csp_with_foldername(base_path):
    foldername = os.path.basename(os.path.abspath(base_path))

    for root, _, files in os.walk(base_path):
        for filename in files:
            if filename.endswith(('.html', '.js', '.json', '.txt')):  # files likely to contain /CSP/
                file_path = os.path.join(root, filename)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    new_content = content.replace('/CSP/', f'/{foldername}/')

                    if new_content != content:  # Only write if changes occurred
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(new_content)
                        print(f"Updated: {file_path}")
                except Exception as e:
                    print(f"Skipped {file_path} due to error: {e}")

# Usage example
replace_csp_with_foldername('experiments/pages/GenAI-38-Examples-4o')
