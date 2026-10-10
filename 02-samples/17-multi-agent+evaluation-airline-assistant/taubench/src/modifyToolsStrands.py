#!/usr/bin/env python3
"""
Script to add required code to tool files:
1. 'from strands import Agent, tool' import if not present
2. '@tool' decorator if not present
3. Direct data loading code if not present
4. Comment out 'data = get_data()' line

The script first creates a copy of the tools folder named 'tools_strands' and then makes changes to the tools in the new folder.
"""

import os
import re
import shutil

def update_tool_file(file_path, domain):
    """
    Update a tool file with required changes.
    
    Args:
        file_path: Path to the file to modify
        domain: The domain name (e.g., 'airline' or 'retail')
    
    Returns:
        bool: True if the file was modified, False otherwise
    """
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Check what we need to add
    import_present = re.search(r'from\s+strands\s+import\s+tool', content) is not None
    decorator_present = re.search(r'@tool', content) is not None
    get_data_call = re.search(r'data\s*=\s*get_data\(\)', content)
    data_loading_present = re.search(fr'from\s+mabench\.environments\.{domain}\.data\s+import\s+load_data', content) is not None
    
    # If everything is already set up correctly, nothing to do
    if import_present and decorator_present and data_loading_present and not get_data_call:
        print(f"No changes needed for {file_path}")
        return False
    
    # Prepare the modified content
    new_content = content
    
    # Add import if needed
    if not import_present:
        # Find a good place to add the import - after other imports but before code
        import_match = re.search(r'((?:^|\n)(?:from|import)[^\n]*(?:\n(?:from|import)[^\n]*)*)', content)
        if import_match:
            # Add after the last import statement
            import_block = import_match.group(1)
            new_content = new_content.replace(import_block, 
                                             f"{import_block}\nfrom strands import tool\nfrom mabench.environments.{domain}.data import load_data\n")
        else:
            # No imports found, add at the top (after docstring if present)
            docstring_match = re.match(r'(""".*?"""|\'\'\'.*?\'\'\')\s*', 
                                      new_content, re.DOTALL)
            if docstring_match:
                docstring_end = docstring_match.end()
                new_content = (new_content[:docstring_end] + 
                              f"\nfrom strands import tool\nfrom mabench.environments.{domain}.data import load_data\n" + 
                              new_content[docstring_end:])
            else:
                new_content = f"from strands import tool\nfrom mabench.environments.{domain}.data import load_data\n\n" + new_content
    
    # Add data loading code if needed and replace get_data() with load_data()
    if get_data_call:
        # Replace get_data() with load_data()
        new_content = new_content.replace(get_data_call.group(0), "data = load_data()")
    
    # Add decorator if needed
    if not decorator_present:
        # Find the first function definition
        func_match = re.search(r'(\ndef\s+\w+\s*\()', new_content)
        if func_match:
            # Add decorator before the function definition
            func_def = func_match.group(1)
            indentation = re.match(r'(\s*)', func_def).group(1)
            new_content = new_content.replace(func_def, f"{indentation}@tool\n{func_def}")
    
    # Write the modified content back to the file
    if new_content != content:
        with open(file_path, 'w') as f:
            f.write(new_content)
        print(f"Updated {file_path}")
        return True
    
    return False

def copy_tools_directory(domain):
    """
    Create a copy of the tools directory for the given domain with the name 'tools_strands'.
    
    Args:
        domain: The domain name (e.g., 'airline')
    
    Returns:
        str: Path to the copied tools directory
    """
    # Original tools directory
    original_tools_dir = os.path.join("..", "data", "ma-bench", "mabench", "environments", domain, "tools")
    
    # Create a copy with the fixed name 'tools_strands'
    copy_tools_dir = os.path.join("..", "data", "ma-bench", "mabench", "environments", domain, "tools_strands")
    
    print(f"Creating a copy of tools directory: {copy_tools_dir}")
    
    if not os.path.exists(original_tools_dir):
        print(f"Original directory not found: {original_tools_dir}")
        return None
    
    # Remove the copy directory if it already exists
    if os.path.exists(copy_tools_dir):
        print(f"Removing existing copy directory: {copy_tools_dir}")
        shutil.rmtree(copy_tools_dir)
    
    # Create the copy
    shutil.copytree(original_tools_dir, copy_tools_dir)
    print(f"Copy created successfully at: {copy_tools_dir}")
    
    return copy_tools_dir

def process_tools_directory(domain, custom_tools_dir=None):
    """
    Process all tool files in the given domain's tools directory.
    
    Args:
        domain: The domain name (e.g., 'airline')
        custom_tools_dir: Optional path to a custom tools directory
    
    Returns:
        tuple: (number of files processed, number of files modified)
    """
    # Use custom directory if provided, otherwise use the default path
    tools_dir = custom_tools_dir if custom_tools_dir else os.path.join("..", "data", "ma-bench", "mabench", "environments", domain, "tools")
    
    print(f"Looking for tools in: {os.path.abspath(tools_dir)}")
    
    if not os.path.exists(tools_dir):
        print(f"Directory not found: {tools_dir}")
        return 0, 0
    
    processed = 0
    modified = 0
    
    # Get all Python files in the directory
    for filename in os.listdir(tools_dir):
        if filename.endswith('.py') and not filename.startswith('__'):
            file_path = os.path.join(tools_dir, filename)
            processed += 1
            
            if update_tool_file(file_path, domain):
                modified += 1
    
    return processed, modified

if __name__ == "__main__":
    import sys
    
    # Default to 'airline' domain if not specified
    domain = sys.argv[1] if len(sys.argv) > 1 else "airline"
    
    print(f"Processing tools for domain: {domain}")
    
    # First create a copy of the tools directory
    copied_tools_dir = copy_tools_directory(domain)
    
    if copied_tools_dir:
        # Then process the copied directory
        processed, modified = process_tools_directory(domain, copied_tools_dir)
        print(f"Processed {processed} files, modified {modified} files in the copied directory: {os.path.basename(copied_tools_dir)}")
    else:
        print("Failed to create a copy of the tools directory. Process aborted.")
