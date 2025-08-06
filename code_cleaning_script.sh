#!/bin/bash

echo "📁 Assuming 'src/' and 'tests/' folders are in the same directory as this script."

# Collect files
src_files=$(find ./src -type f)
workflow_files=$(find ./.github/workflows -type f -name "*.yml")
unused_files=()

echo "🔍 Checking for unused files in src and workflow references..."

for file_path in $src_files; do
  file_name=$(basename "$file_path")
  file_stem="${file_name%.*}"  # Remove extension

  # Skip __init__.py
  if [ "$file_name" = "__init__.py" ]; then
    continue
  fi

  referenced=false

  # Check stem in other src files
  for other_path in $src_files; do
    if [ "$file_path" != "$other_path" ]; then
      if grep -q "$file_stem" "$other_path"; then
        referenced=true
        break
      fi
    fi
  done

  # Check stem in workflow files
  if [ "$referenced" = false ]; then
    for wf_file in $workflow_files; do
      if grep -q "$file_stem" "$wf_file"; then
        referenced=true
        break
      fi
    done
  fi

  if [ "$referenced" = false ]; then
    unused_files+=("$file_path")
  fi
done

# Show results
if [ ${#unused_files[@]} -eq 0 ]; then
  echo "✅ No unused src files found."
  exit 0
fi

echo "🚫 Unused src files found:"
for file in "${unused_files[@]}"; do
  echo "$file"
done

# Confirm deletion of src files
read -p "Delete these src files? (y/n): " confirm_src
if [ "$confirm_src" = "y" ]; then
  for file in "${unused_files[@]}"; do
    rm "$file"
  done
  echo "🗑️ Src files deleted."
else
  echo "❎ Skipping src deletion."
fi

# Confirm deletion of matching test files
read -p "Delete matching files from tests folder? (y/n): " confirm_test
if [ "$confirm_test" = "y" ]; then
  for file in "${unused_files[@]}"; do
    stem=$(basename "$file")
    stem="${stem%.*}"
    matching_tests=$(find ./tests -type f -name "*$stem*")
    for test_file in $matching_tests; do
      rm "$test_file"
      echo "🗑️ Deleted test file: $test_file"
    done
  done
else
  echo "❎ Skipping test file deletion."
fi

# Optionally commit and push changes
if [ "$confirm_src" = "y" ] || [ "$confirm_test" = "y" ]; then
  git add .
  git commit -m "🔧 Cleanup: removed unused src files and matching test files"
  git push
  echo "🚀 Changes committed and pushed."
fi



