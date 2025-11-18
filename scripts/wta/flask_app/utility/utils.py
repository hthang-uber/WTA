import importlib.resources as pkg_resources
from PIL import Image
import json
import os
import subprocess
import shutil
import base64
import re
import yaml


def remove_path(path):
    """
    Removes the file or directory at the specified path if it exists.
    """
    if os.path.exists(path):
        if os.path.isdir(path):
            shutil.rmtree(path)
        elif os.path.isfile(path):
            os.remove(path)

def get_substring(string, delimiter, get_pre_string=True):
    """
    Retrieves a substring from the given string based on a delimiter.

    Args:
        string: The original string to extract the substring from.
        delimiter: The delimiter to search for within the string.
        get_pre_string: If True, return the substring before the delimiter; 
                        otherwise, return the substring after the delimiter.

    Returns:
        The extracted substring or the original string if the delimiter is not found.
    """
    try:
        if string is None:
            return ""
        at_index = string.lower().find(delimiter)
        if at_index == -1:
            return string[:100]
        return string[:at_index] if get_pre_string else string[at_index+1:]
    except Exception as e:
        print(f"Error getting substring: {e}")
        return string[:100] if string else ""

def format_failure_log(string):
    """
    Formats a failure log string to return the shorter substring between '.java' and '.kt'.

    Args:
        string: The log string to be formatted.

    Returns:
        The formatted substring.
    """
    java_str = get_substring(string, '.java')
    kt_str = get_substring(string, '.kt')
    return java_str if len(java_str) < len(kt_str) else kt_str

def download_images_from_terrablob(url, local_dir_path, filename, max_retries=3):
    """
    Downloads an image from a given URL and saves it to a specified local directory.

    Args:
        url: URL of the image to be downloaded.
        local_dir_path: Local directory path to save the downloaded image.
        filename: Name of the file to save the image as.
    """
    if not os.path.exists(local_dir_path):
        os.makedirs(local_dir_path)
    
    source_path = get_substring(url, '-', False).replace("last_snapshot.png", "")
    output = subprocess.run(f'tb-cli --usso-token=$(utoken create) ls {source_path} | grep ".png"', shell=True, capture_output=True, text=True)
    img_name = output.stdout.strip()
    target_path = os.path.join(local_dir_path, filename)

    # remove_path(target_path)

    retries = 0
    while retries < max_retries:
        if not os.path.exists(target_path) or not is_image_valid(target_path):
            try:
                subprocess.run(f"tb-cli --usso-token=$(utoken create) get {source_path}{img_name} {target_path} -t 2m", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            except subprocess.CalledProcessError as e:
                print(f"Error occurred while downloading the image: {e}")
                retries += 1
                continue

            if is_image_valid(target_path):
                return target_path
            else:
                print(f"Downloaded image is corrupted. Retrying {retries + 1}/{max_retries}...")
                remove_path(target_path)
                retries += 1
        else:
            return target_path

    if retries == max_retries:
        print("Max retries reached. The image could not be downloaded or is still corrupted.")
        return False


def download_images_terrablob(url, local_dir_path, filename, max_retries=3):
    """
    Downloads an image from a given URL and saves it to a specified local directory.

    Args:
        url: URL of the image to be downloaded.
        local_dir_path: Local directory path to save the downloaded image.
        filename: Name of the file to save the image as.
    """
    if not os.path.exists(local_dir_path):
        os.makedirs(local_dir_path)
    
    source_path = url
    target_path = os.path.join(local_dir_path, filename)

    # remove_path(target_path)

    retries = 0
    while retries < max_retries:
        if not os.path.exists(target_path) or not is_image_valid(target_path):
            try:
                subprocess.run(f"tb-cli --usso-token=$(utoken create) get {source_path} {target_path} -t 2m", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            except subprocess.CalledProcessError as e:
                print(f"Error occurred while downloading the image: {e}")
                retries += 1
                continue

            if is_image_valid(target_path):
                return target_path
            else:
                print(f"Downloaded image is corrupted. Retrying {retries + 1}/{max_retries}...")
                remove_path(target_path)
                retries += 1
        else:
            return target_path

    if retries == max_retries:
        print("Max retries reached. The image could not be downloaded or is still corrupted.")
        return False

def is_image_valid(path):
    """
    Checks if an image file is valid.

    Args:
        path: The path of the image file to be checked.

    Returns:
        bool: True if the image is valid, False otherwise.
    """
    try:
        with Image.open(path) as img:
            img.verify()
        return True
    except (IOError, SyntaxError):
        return False
        
def list_to_string(items, delimiter="', '", presu="'"):
    """
    Converts a list of strings into a single string with a specified delimiter and prefix/suffix.

    Args:
        items: List of strings to be concatenated.
        delimiter: Delimiter to use between the strings.
        presu: Prefix and suffix to enclose the final string.

    Returns:
        Concatenated string.
    """
    return presu + delimiter.join(items) + presu

def create_hyperlink_for_gsheets(url, label):
    """
    Generates a hyperlink formula for Google Sheets.

    Args:
        url: URL to be linked.
        label: Display text for the hyperlink.

    Returns:
        Google Sheets hyperlink formula string.
    """
    return f"=HYPERLINK(\"{url}\",\"{label}\")"

def get_machine_email_from_usso_cli(domain='t3'):
    """
    Retrieves the machine email address using the US Secure Object (usso) CLI.

    Args:
        domain: Domain for which to retrieve the email (default is 't3').

    Returns:
        Extracted email address.
    """
    result = subprocess.run(['usso', '-utoken', 'utoken', '-aud', domain, '-print'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    if result.returncode != 0:
        raise Exception(result.stderr.decode('utf-8'))

    if result.stdout:
        jstr = result.stdout.decode('utf-8')
        utoken_json = json.loads(jstr)
        utoken_email = json.loads(base64.b64decode(
            utoken_json.get('fwd_utoken').split(".")[1] + '==')).get('email')
        return utoken_email

def get_offline_auth_token_from_usso_cli(domain='t3'):
    """
    Retrieves an offline authentication token using the US Secure Object (usso) CLI.

    Args:
        domain: Domain for which to retrieve the token (default is 't3').

    Returns:
        Retrieved authentication token.
    """
    subprocess.run(['usso', '-ussh', domain, '-force'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    result = subprocess.run(['usso', '-ussh', domain, '-print'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    if result.returncode != 0:
        raise Exception(result.stderr.decode('utf-8'))

    if result.stdout:
        return result.stdout.decode('utf-8').strip()

def insert_substring(input_string, substring, from_index, to_index):
    """
    Inserts a substring into a string at specified indices.

    Args:
        input_string: Original string.
        substring: Substring to be inserted.
        from_index: Start index for insertion.
        to_index: End index for insertion.

    Returns:
        Modified string with the substring inserted.
    """
    return input_string[:from_index] + substring + input_string[to_index:]

def get_interactiveUUID_data(interactiveUUID):
    """
    Retrieves data for an interactive UUID using the 'yab' CLI tool.

    Args:
        interactiveUUID: UUID to fetch data for.

    Returns:
        JSON data retrieved from the command output.
    """
    uuid = json.dumps({"id":interactiveUUID})
    command = (
        f"yab -s uber-studio --caller yab-spikki --request '{uuid}' --procedure 'Orchestrator::GetRun' "
        f"--header 'studio-caller:akumar577' --header 'x-uber-source:studio' "
        f"--header 'x-uber-uuid:2a2d59e8-9bbf-4c4e-97a5-4cbb85bec7fa' "
        f"--header '$tracing$jaeger-debug-id:api-explorer-akumar577' "
        f"--header '$tracing$uberctx-tenancy:uber/testing/api-explorer/a9c7-4067-b528-8c0701769db3' "
        f"--peer '127.0.0.1:5437' --timeout 30000ms -t ./orchestrator.thrift"
    )
    output = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
    output_str = output.decode()
    return json.loads(output_str) if output_str.startswith('{') else {}

def remove_tags(text):
    """
    Removes HTML tags from a given text string.

    Args:
        text: Input text with HTML tags.

    Returns:
        Text without HTML tags.
    """
    return re.sub(r'<[^>]+>', '', text)


def load_constant_yaml():
    """Load YAML from package resources."""
    with pkg_resources.open_text('src.utility', 'constants.yaml') as file:
        return yaml.safe_load(file)

def load_mapping_data():
    with pkg_resources.open_text('src.utility', 'mappings.json') as file:
        return json.load(file)

if __name__ == "__main__":
    print(get_interactiveUUID_data("interactive-5c553c5a-b53a-4232-a03a-76c457c0b72e"))
