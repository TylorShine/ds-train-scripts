import pyopenjtalk
import os
import glob
import argparse
import re

def g2p_openjtalk(text, dictionary_path=None, sandwich_pau=True, no_join=False, return_cleaned_text=False):
    """
    Converts Japanese text to phoneme sequences using pyopenjtalk.
    Args:
        text: The input text to be converted.
        dictionary_path: Optional path to a custom Open JTalk dictionary.
                          If None, the default dictionary is used.
        sandwich_pau: If True, inserts "pau" between each phoneme.

    Returns:
        A list of phoneme sequences.
    """
    
    try:
        # Remove any non-Japanese characters (optional, but good for cleaning)
        # text = re.sub(r'[^\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uff01-\uff5e]+', '', text)
        # Remove any non-English or non-Japanese characters (optional, but good for cleaning)
        text_cleaned = re.sub(r'[^\u3000-\u303f\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff\uff01-\uff5e\u2026\w\s]+', '', text)
        if not text_cleaned:
            print(f"WARNING: text '{text}' is empty because it contains no English or Japanese text after cleaning.")
            return ""
        
        # Replace "～" with "ー"
        text_cleaned = text_cleaned.replace("～", "ー")
        
        args = {
            "kana": False,
        }
        if dictionary_path:
            args["dialect"] = dictionary_path
        if no_join:
            args["join"] = False

        # Convert to phonemes using pyopenjtalk
        phonemes = pyopenjtalk.g2p(text_cleaned, **args)
            
        # Add a pause at the start and end of the phoneme sequence
        if sandwich_pau:
            if isinstance(phonemes, str):
                phonemes = f"pau {phonemes} pau"
            else:
                phonemes = ["pau"] + phonemes + ["pau"]
            
        if return_cleaned_text:
            return phonemes, text_cleaned
        
        return phonemes

    except Exception as e:
        print(f"An unexpected error occurred processing {text}: {e}")
    

def text_to_phonemes_openjtalk(input_dir, output_dir, dictionary_path=None, sandwich_pau=True, no_join=False, return_cleaned_text=False):
    """
    Converts Japanese text files in a directory to phoneme sequences using pyopenjtalk.

    Args:
        input_dir: The directory containing the text files.
        output_dir: The directory to save the phoneme files (.lab).
        dictionary_path: Optional path to a custom Open JTalk dictionary.
                          If None, the default dictionary is used.
    """

    if not os.path.exists(input_dir):
        print(f"Error: Input directory not found: {input_dir}")
        return

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created output directory: {output_dir}")

    # Find all .txt files in the input directory
    text_files = glob.glob(os.path.join(input_dir, "*.txt"))

    if not text_files:
        print(f"No .txt files found in {input_dir}")
        return

    file_count = 0
    for text_file in text_files:
        try:
            with open(text_file, 'r', encoding='utf-8') as infile:
                text = infile.read()

            # Remove any non-Japanese characters (optional, but good for cleaning)
            # text = re.sub(r'[^\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uff01-\uff5e]+', '', text)
            # Remove any non-English or non-Japanese characters (optional, but good for cleaning)
            # text = re.sub(r'[^\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uff01-\uff5e\w\s]+', '', text)
            # \u2026: horizontal ellipsis
            text_cleaned = re.sub(r'[^\u3000-\u303f\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff\uff01-\uff5e\u2026\w\s]+', '', text)
            if not text:
                print(f"Skipping file {text_file} because it contains no Japanese text after cleaning.")
                continue
            
            # Replace "～" with "ー"
            text_cleaned = text_cleaned.replace("～", "ー")
            
            args = {
                "kana": False,
            }
            if dictionary_path:
                args["dialect"] = dictionary_path
            if no_join:
                args["join"] = False

            # Convert to phonemes using pyopenjtalk
            # if dictionary_path:
            #     phonemes = pyopenjtalk.g2p(text_cleaned, kana=False, dialect=dictionary_path)
            # else:
            #     phonemes = pyopenjtalk.g2p(text_cleaned, kana=False)
            phonemes = pyopenjtalk.g2p(text_cleaned, **args)
                
            # Add a pause at the start and end of the phoneme sequence
            if sandwich_pau:
                # phonemes = f"pau {phonemes} pau"
                if isinstance(phonemes, str):
                    phonemes = f"pau {phonemes} pau"
                else:
                    phonemes = ["pau"] + phonemes + ["pau"]
                    phonemes = "|".join(phonemes)

            # Get the base filename (without extension)
            base_filename = os.path.splitext(os.path.basename(text_file))[0]
            output_filename = os.path.join(output_dir, f"{base_filename}.lab")  # Use .lab extension

            with open(output_filename, 'w', encoding='utf-8') as outfile:
                if return_cleaned_text:
                    outfile.write(f"{text_cleaned}\n")
                    outfile.write(phonemes)
                else:
                    outfile.write(phonemes)

            file_count += 1
            print(f"Converted {text_file} -> {output_filename}")

        except FileNotFoundError:
            print(f"Error: Text file not found: {text_file}")
        except UnicodeDecodeError:
            print(f"Error: Could not decode text in file: {text_file}.  Check file encoding (should be UTF-8).")
        except Exception as e:
            print(f"An unexpected error occurred processing {text_file}: {e}")
            
            
def main():
    parser = argparse.ArgumentParser(description="Convert Japanese text files to phoneme sequences.")
    parser.add_argument("input_dir", help="Directory containing the text files.")
    parser.add_argument("output_dir", help="Directory to save the phoneme files (.lab).")
    parser.add_argument("-d", "--dictionary", help="Optional path to a custom Open JTalk dictionary.", default=None)
    parser.add_argument("-s", "--sandwich_pau", help="Add PAU (silence) at the beginning and end of each phoneme sequence.", action="store_true")
    parser.add_argument("-n", "--no_join", help="Don't join phonemes into a single string.", action="store_true")
    parser.add_argument("-c", "--return_cleaned_text", help="Return the cleaned text as well as the phonemes.", action="store_true")
    args = parser.parse_args()

    text_to_phonemes_openjtalk(args.input_dir, args.output_dir, args.dictionary, args.sandwich_pau, args.no_join, args.return_cleaned_text)


if __name__ == "__main__":
    main()