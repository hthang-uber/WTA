import argparse
from sentence_transformers import SentenceTransformer, util
from PIL import Image
from fuzzywuzzy import fuzz

def compare_images(first_image_path, second_image_path, threshold=0.93):
    """
    Compare the similarity of two images based on a given threshold using sentence_transformers and OpenAI's CLIP model.

    Args:
        first_image_path (str): Path to the first image.
        second_image_path (str): Path to the second image.
        threshold (float): Similarity threshold (100% similar images: threshold = 1.0).

    Returns:
        bool: True if the images are similar above the threshold, False otherwise.
    """
    try:
        # Load the pre-trained CLIP model
        model = SentenceTransformer('clip-ViT-B-32')
        
        # Open the images and encode them using the model
        first_image = Image.open(first_image_path)
        second_image = Image.open(second_image_path)
        encoded_images = model.encode([first_image, second_image], convert_to_tensor=True, show_progress_bar=False)
        
        # Compute the cosine similarity between the two image embeddings
        similarity = util.cos_sim(encoded_images[0], encoded_images[1])
        
        # Check if the similarity is above the threshold
        return similarity.item() > threshold
    except Exception as e:
        print(f"Error comparing images: {e}")
        return False

def compare_strings(first_string, second_string, threshold=95):
    """
    Compare the similarity of two strings based on a given threshold using fuzzy matching.

    Args:
        first_string (str): The first string to compare.
        second_string (str): The second string to compare.
        threshold (int): The minimum similarity threshold (default is 95).

    Returns:
        bool: True if the similarity of the two strings is greater than or equal to the threshold, False otherwise.
    """
    try:
        similarity = fuzz.partial_ratio(first_string, second_string)
        return similarity >= threshold
    except Exception as e:
        print(f"Error comparing strings: {e}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compare images or strings based on similarity thresholds.")
    parser.add_argument("compare", choices=["image", "string"], help="Specify whether to compare 'image' or 'string'.")
    parser.add_argument("arg1", help="Path to the first image or the first string to compare.")
    parser.add_argument("arg2", help="Path to the second image or the second string to compare.")
    parser.add_argument("-t", "--threshold", type=float, help="Similarity threshold [1-100], generally greater than 90", default=90)
    args = parser.parse_args()

    threshold = args.threshold / 100 if args.compare == "image" else int(args.threshold)

    if args.compare == "image":
        result = compare_images(args.arg1, args.arg2, threshold)
    else:
        str1 = """Error: Studio API request failed for URL: https://uber-studio.uberinternal.com/uber-studio/executeAction Correlation ID: studio-api-1756917962515-dimf7arp4 Request Payload: {"runID":"interactive-ef9dbc5a-3969-4389-8ab2-479a7bbcf4fa","actorID":"driver1","action":"documents_create_document","params":"""
        str2 = """Error: Studio API request failed for URL: https://uber-studio.uberinternal.com/uber-studio/executeAction Correlation ID: studio-api-1756918027632-vaj6fb1ea Request Payload: {"runID":"interactive-5448f4d1-c247-44e8-9283-7d0c63d92953","actorID":"driver1","action":"documents_approve_document","params":"""
        result = compare_strings(str1, str2, threshold)

    print("Similarity result:", result)
