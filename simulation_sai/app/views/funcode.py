import os, base64

def fun_decode(pathdir):
    # Split the directory and filename from the provided path
    basefolder, filename = os.path.split(pathdir)
    
    # Get the current file's directory
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Move up one level from 'views'
    print('Your base directory for this project:', base_dir)
    
    # Construct the absolute path for the encoded file inside 'Temp'
    file_path = os.path.join(base_dir, "templates", "Temp", basefolder, filename)  # Correct path
    print('HTML file path:', file_path)

    # Construct the absolute path for the decoded output file
    output_html = os.path.join(base_dir, "templates", basefolder, filename)
    print('Output HTML path:', output_html)

    # Check if the encoded file exists
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"The file at {file_path} does not exist.")
    
    # Read the encoded file content
    with open(file_path, "r") as file_obj:
        text = file_obj.read()
    
    # Decode the base64 string
    encoded_string = text.encode("utf-8")
    string_bytes = base64.b64decode(encoded_string)
    
    # Write the decoded content to the output file
    with open(output_html, "wb") as f5:
        f5.write(string_bytes)
    
    # Return the relative path of the decoded file
    return os.path.join(basefolder, filename)
