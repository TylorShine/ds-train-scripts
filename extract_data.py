import os
import csv
import json
import shutil
import argparse

def parse_args():
    parser = argparse.ArgumentParser(description='Extract and process audio data for DiffSinger/NNSVS')
    parser.add_argument('--data_type', choices=['lab_wav', 'csv_wav', 'ds'],
                      default='lab_wav', help='Type of data to process')   # lab_wav: NNSVS format, csv_wav, ds: DiffSinger format
    parser.add_argument('--data_zip_path', type=str, required=True, help='Path to data zip file')
    parser.add_argument('--estimate_midi', choices=['False', 'parselmouth', 'harvest', 'SOME'],
                      default='False', help='MIDI estimation method')
    parser.add_argument('--segment_length', type=int, default=15, help='Segment length in seconds')
    parser.add_argument('--max_silence_phoneme', type=int, default=2, help='Maximum silence phonemes allowed')
    return parser.parse_args()

def setup_directories():
    all_shits = os.path.join(os.getcwd(), "raw_data")
    all_shits_not_wav_n_lab = os.path.join(all_shits, "diffsinger_db")
    
    if os.path.exists(all_shits):
        shutil.rmtree(all_shits)
    
    if not os.path.exists(all_shits_not_wav_n_lab):
        os.makedirs(all_shits_not_wav_n_lab)
    
    return all_shits, all_shits_not_wav_n_lab

def extract_archive(data_zip_path, extract_path):
    os.system(f'7z x "{data_zip_path}" -o{extract_path}')

def process_lab_files(root_path):
    for root, _, files in os.walk(root_path):
        for filename in files:
            if filename.endswith(".lab"):
                file_path = os.path.join(root, filename)
                with open(file_path, "r") as file:
                    file_data = file.read()
                file_data = file_data.replace("SP", "pau").replace("br", "AP")
                with open(file_path, "w") as file:
                    file.write(file_data)

def collect_phonemes(data_type, phoneme_folder_path):
    phonemes = set()
    
    def is_excluded(phoneme):
        return phoneme in ["pau", "AP", "SP", "sil", "br"]
    
    if data_type == "lab_wav":
        for root, _, files in os.walk(phoneme_folder_path):
            for file in files:
                if file.endswith(".lab"):
                    with open(os.path.join(root, file), "r") as lab_file:
                        for line in lab_file:
                            line = line.strip()
                            if line:
                                phoneme = line.split()[2]
                                if not is_excluded(phoneme):
                                    phonemes.add(phoneme)
    
    elif data_type == "csv_wav":
        for root, _, files in os.walk(phoneme_folder_path):
            for file in files:
                if file.endswith(".csv"):
                    with open(os.path.join(root, file), "r", newline="") as csv_file:
                        csv_reader = csv.DictReader(csv_file)
                        for row in csv_reader:
                            if "ph_seq" in row:
                                for phoneme in row["ph_seq"].strip().split():
                                    if not is_excluded(phoneme):
                                        phonemes.add(phoneme)
    
    else:  # ds format
        for root, _, files in os.walk(phoneme_folder_path):
            for file in files:
                if file.endswith(".ds"):
                    with open(os.path.join(root, file), "r") as json_file:
                        data = json.load(json_file)
                        for entry in data:
                            if "ph_seq" in entry:
                                for phoneme in entry["ph_seq"].strip().split():
                                    if not is_excluded(phoneme):
                                        phonemes.add(phoneme)
    
    return sorted(phonemes)

def generate_phoneme_files(phonemes, dict_path):
    vowel_types = {"a", "i", "u", "e", "o", "N", "M", "NG"}
    liquid_types = {"y", "w", "l", "r"}
    
    vowels = []
    liquids = []
    consonants = []
    
    for phoneme in phonemes:
        if phoneme[0] in vowel_types:
            vowels.append(phoneme)
        elif phoneme[0] in liquid_types:
            liquids.append(phoneme)
        else:
            consonants.append(phoneme)
    
    directory = os.path.dirname(dict_path)
    
    # Write dictionary file
    with open(dict_path, "w") as f:
        for phoneme in phonemes:
            f.write(f"{phoneme}\t{phoneme}\n")
    
    # Write component files
    for filename, data in [
        ("vowels.txt", vowels),
        ("liquids.txt", liquids),
        ("consonants.txt", consonants)
    ]:
        with open(os.path.join(directory, filename), "w") as f:
            f.write(" ".join(data))
    
    return vowels, liquids, consonants

def process_data(args, all_shits, all_shits_not_wav_n_lab):
    if args.data_type == "lab_wav":
        db_converter_script = "./nnsvs-db-converter/db_converter.py"
        for folder_name in os.listdir(all_shits_not_wav_n_lab):
            folder_path = os.path.join(all_shits_not_wav_n_lab, folder_name)
            if os.path.isdir(folder_path):
                # for song_folder in os.listdir(folder_path):
                #     song_folder_path = os.path.join(folder_path, song_folder)
                #     if os.path.isdir(song_folder_path):
                cmd = f"python {db_converter_script} -s {args.max_silence_phoneme} -l {args.segment_length} -D"
                if args.estimate_midi != "False":
                    cmd += " -m -c"
                cmd += f' -L "./nnsvs-db-converter/lang.sample.json" {folder_path}'
                os.system(cmd)
                
                # Cleanup and reorganize files
                # for file in os.listdir(folder_path):
                for root, _, files in os.walk(folder_path):
                    if root.endswith("wavs"):
                        continue
                    for file in files:
                        if file.endswith(('.wav', '.lab')):
                            os.remove(os.path.join(root, file))
                    # if file.endswith(('.wav', '.lab')):
                    #     os.remove(os.path.join(folder_path, file))
                
                diffsinger_db_path = os.path.join(folder_path, "diffsinger_db")
                if os.path.exists(diffsinger_db_path):
                    for item in os.listdir(diffsinger_db_path):
                        src = os.path.join(diffsinger_db_path, item)
                        dst = os.path.join(folder_path, item)
                        # if os.path.isfile(src):
                        shutil.move(src, dst)
                    shutil.rmtree(diffsinger_db_path)
                
                if args.estimate_midi == "SOME":
                    os.system(f'python ./SOME/batch_infer.py --model "./DiffSinger/checkpoints/SOME/0119_continuous256_5spk/model_ckpt_steps_100000_simplified.ckpt" --dataset {folder_path} --overwrite')
    
    elif args.data_type == "ds":
        for folder_name in os.listdir(all_shits_not_wav_n_lab):
            folder_path = os.path.join(all_shits_not_wav_n_lab, folder_name)
            if os.path.isdir(folder_path):
                ds_exp_path = os.path.join(folder_path, "ds")
                csv_exp_path = os.path.join(folder_path, "transcriptions.csv")
                os.system(f"python ./ghin_shenanigans/scripts/ds_segmentor.py {folder_path} --export_path {ds_exp_path}")
                for file in os.listdir(folder_path):
                    if file.endswith('.ds'):
                        os.remove(os.path.join(folder_path, file))
                os.system(f"python ./MakeDiffSinger/variance-temp-solution/convert_ds.py ds2csv {ds_exp_path} {csv_exp_path}")
                
def fix_initial_sp(folder_path):
    for root, _, files in os.walk(folder_path):
        for file in files:
            if file.endswith(".csv"):
                file_path = os.path.join(root, file)
                with open(file_path, "r", newline="") as input_file:
                    csv_reader = csv.reader(input_file)
                    data = list(csv_reader)
                    if len(data) > 1 and "ph_seq" in data[0]:
                        ph_seq_index = data[0].index("ph_seq")
                        if len(data[1]) > ph_seq_index:
                            data[1][ph_seq_index] = data[1][ph_seq_index].replace("SP", "AP", 1)
                
                with open(file_path, "w", newline="") as output_file:
                    csv.writer(output_file).writerows(data)

def main():
    args = parse_args()
    all_shits, all_shits_not_wav_n_lab = setup_directories()
    
    # Extract archive
    extract_archive(args.data_zip_path, all_shits_not_wav_n_lab)
    
    if args.data_type != "lab_wav":
        process_lab_files(all_shits)
    
    # Generate phoneme dictionary and related files
    phonemes = collect_phonemes(args.data_type, all_shits if args.data_type == "lab_wav" else all_shits_not_wav_n_lab)
    vowels, liquids, consonants = generate_phoneme_files(phonemes, "./DiffSinger/dictionaries/custom_dict.txt")
    
    # Generate language JSON
    liquid_list = {liquid: True for liquid in liquids}
    phones4json = {"vowels": vowels, "liquids": liquid_list}
    with open("./nnsvs-db-converter/lang.sample.json", "w") as f:
        json.dump(phones4json, f, indent=4)
    
    # Process data based on type
    process_data(args, all_shits, all_shits_not_wav_n_lab)
    
    # Fix initial SP in CSV files
    fix_initial_sp(all_shits_not_wav_n_lab)
    
    print("Extraction complete!")
    print("Dictionary and data conversion completed successfully.")

if __name__ == "__main__":
    main()