#!/bin/bash

# Define the folder containing all test subfolders
parent_test_folder="../pages/CSP/"

# Check if parent folder exists
if [ ! -d "$parent_test_folder" ]; then
    echo "Error: Parent folder $parent_test_folder does not exist."
    exit 1
fi

# Use `find` to locate all `generated_tests/CSP/` directories
echo "Searching for 'generated_tests/' directories in $parent_test_folder..."
generated_folders=$(find "$parent_test_folder" -type d -path "*-CSP")

if [ -z "$generated_folders" ]; then
    echo "No 'generated_tests/' directories found. Nothing to delete."
    exit 0
fi

# Iterate over each found folder and delete it
for folder in $generated_folders; do
    echo "Deleting folder: $folder"
    rm -rf "$folder"
done

echo "Cleanup complete."
