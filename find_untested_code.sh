#!/bin/bash

src_dir="./src"
test_dir="./tests"
missing_count=0

echo "📂 Confirm that this script is in the same directory as the 'src' and 'tests' folders."
echo "👉 Press Enter (or any key) to continue..."
read -n 1 -s

echo "🔍 Scanning for missing unit tests..."

# Loop through all Python files in src directory
find "$src_dir" -type f -name "*.py" | while read -r src_file; do
    filename="$(basename "$src_file")"

    # Skip __init__.py files
    if [[ "$filename" == "__init__.py" ]]; then
        continue
    fi

    rel_path="${src_file#$src_dir/}"
    test_filename="test_${filename}"

    # Determine expected test path
    if [[ "$rel_path" == "$filename" ]]; then
        test_path="${test_dir}/${test_filename}"
    else
        folder_path="$(dirname "$rel_path")"
        test_path="${test_dir}/${folder_path}/${test_filename}"
    fi

    if [ ! -f "$test_path" ]; then
        echo "🚫 Missing test for core file: $filename"
        echo "   ➤ Core file path: $src_file"
        echo "   ➤ Expected test path: $test_path"
        echo
        ((missing_count++))
    fi
done

if [[ "$missing_count" -eq 0 ]]; then
    echo "✅ All core code files have their corresponding unit tests. Nicely done!"
fi



