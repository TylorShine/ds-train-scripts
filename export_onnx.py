#!/usr/bin/env python3
import os
import subprocess
import shutil
import json
import argparse

def setup_environment(conda_executable="conda"):
    """Setup conda environment for ONNX conversion"""
    env_name = "diffsinger_onnx"
    env_check = f"{conda_executable} env list | grep '^\s{env_name} '"

    if os.system(env_check) != 0:
        subprocess.run(f'{conda_executable} create -n diffsinger_onnx python=3.10 uv -y', shell=True)
        # subprocess.run(f'{conda_executable} run -n diffsinger_onnx uv pip install setuptools<81', shell=True) # cannot work on cmd.exe...
        with open("requirements-onnx.txt", "r+") as f:
            requirements = f.read().split("\n")
            requirements = [r for r in requirements if not r.startswith("setuptools") and not r.startswith("pyyaml")]
            requirements.append("setuptools<81")
            requirements.append("pyyaml")
            f.seek(0)
            f.write("\n".join(requirements))
            f.truncate()
        subprocess.run(f'{conda_executable} run -n diffsinger_onnx uv pip install -r requirements-onnx.txt', shell=True)
    else:
        print(f"Environment '{env_name}' already exists. Skipping installation.")

def update_hparams(folder_path):
    """Update hparams.py with correct work directory"""
    search_text = "        args_work_dir = os.path.join("
    replacement = f"        args_work_dir = '{folder_path}'"
    
    with open("utils/hparams.py", "r") as file:
        lines = file.readlines()
    
    for i, line in enumerate(lines):
        if search_text in line:
            lines[i] = replacement + "\n"
            break
            
    with open("utils/hparams.py", "w") as file:
        file.writelines(lines)
    
    # Handle alternative format
    search_text_alt = "        args_work_dir = '"
    replacement_alt = f"        args_work_dir = '{folder_path}'"
    
    with open("utils/hparams.py", "r") as file:
        lines = file.readlines()
    
    for i, line in enumerate(lines):
        if search_text_alt in line:
            lines[i] = replacement_alt + "\n"
            break
            
    with open("utils/hparams.py", "w") as file:
        file.writelines(lines)

def export_model(model_type, checkpoint_path, exp_folder, no_output=True, conda_executable="conda"):
    """Export model to ONNX format"""
    if not checkpoint_path:
        print(f"\n{model_type} checkpoint path not specified, not exporting {model_type} ONNX...")
        return

    print(f"\nConverting {model_type} to ONNX...")
    folder_name = f"{os.path.basename(os.path.dirname(checkpoint_path))}_{model_type}"
    folder_path = os.path.dirname(checkpoint_path)
    
    # Copy config
    custom_dict_stashed = False
    shutil.copy(f'{folder_path}/config.yaml', f'checkpoints/{folder_name}')
    if os.path.isfile(f'{folder_path}/dictionary.txt'):
        if os.path.exists(f'dictionaries/custom_dict.txt'):
            # stash it
            shutil.move(f'dictionaries/custom_dict.txt', f'dictionaries/custom_dict.txt.bak')
            custom_dict_stashed = True
        shutil.copy(f'{folder_path}/dictionary.txt', f'dictionaries/custom_dict.txt')
    
    # Update hparams
    update_hparams(folder_path)
    
    # Run export
    output_path = f"{exp_folder}/onnx/{model_type}"
    if model_type == "fir-acoustic-vocoder":
        export_cmd = f"python scripts/export.py {model_type} --exp {folder_name} --out {output_path}"
    else:
        export_cmd = f"{conda_executable} run -n diffsinger_onnx python scripts/export.py {model_type} --exp {folder_name} --out {output_path}"
    
    if no_output:
        export_cmd += " >/dev/null 2>&1"
    
    os.system(export_cmd)
    # os.system(f"{conda_executable} run -n diffsinger_onnx python scripts/export.py --help")
    # import sys
    # sys.exit()
    
    if custom_dict_stashed:
        # restore custom dict
        shutil.move(f'dictionaries/custom_dict.txt.bak', f'dictionaries/custom_dict.txt')
    
    return output_path

def rename_files(folder_paths):
    """Rename exported files to match OpenUtau format"""
    patterns = {
        "acoustic.onnx": "acoustic.onnx",
        "dur.onnx": "dur.onnx",
        "linguistic.onnx": "linguistic.onnx",
        "pitch.onnx": "pitch.onnx",
        "variance.onnx": "variance.onnx",
        # "fir-acoustic-vocoder.onnx": "acoustic.onnx",
        "phonemes.txt": "phonemes.txt"
    }

    for folder_path in folder_paths:
        # First rename pass
        for filename in os.listdir(folder_path):
            for pattern, new_name in patterns.items():
                if pattern in filename:
                    old_path = os.path.join(folder_path, filename)
                    new_path = os.path.join(folder_path, new_name)
                    if os.path.exists(old_path):
                        # os.rename(old_path, new_path)
                        shutil.move(old_path, new_path)
        
        # Second rename pass
        for filename in os.listdir(folder_path):
            filename :str
            if os.path.splitext(filename)[1] == ".emb":
                if "_acoustic." in filename:
                    new_filename = "".join(filename.split("_acoustic.")[1:])
                elif "_variance." in filename:
                    new_filename = "".join(filename.split("_variance.")[1:])
                else:
                    new_filename = filename
            elif "acoustic_acoustic." in filename:
                new_filename = filename.replace("acoustic_acoustic.", "acoustic_")
            elif "variance_variance." in filename:
                new_filename = filename.replace("variance_variance.", "variance_")
            else:
                new_filename = filename
            old_path = os.path.join(folder_path, filename)
            new_path = os.path.join(folder_path, new_filename)
            # os.rename(old_path, new_path)
            shutil.move(old_path, new_path)
            
            
def make_ou_compatible(folder_paths, output_path, chara_name, dict_path):
    """Make exported files compatible with OpenUtau"""
    # Rename files
    rename_files(folder_paths)
    
    # Some f... processing...
    
    acoustic_path = None
    variance_path = None
    
    found_emb_files = None
    found_pitch = False
    found_vocoder = False
    
    import yaml
    
    languages = {}
                    
    # first pass: find variance folders
    for folder_path in folder_paths:
        folder_files = os.listdir(folder_path)
        if "variance.onnx" in folder_files:
            # mark this folder as variance folder
            variance_path = folder_path
            # search for emb files
            found_emb_files = [f for f in folder_files if f.endswith(".emb")]

            dsdur_files = [
                "dur.onnx",
            ]
            dspitch_files = [
                "pitch.onnx",
            ]
            dsvariance_files = [
                "variance.onnx",
                "linguistic.onnx",
                "diffsinger_variance_phonemes.json",
                "diffsinger_variance_languages.json",
            ]
            dsvocoder_files = [
                "vocoder.onnx",
                "vocoder.yaml",
            ]
            # edit variance config
            with open(os.path.join(folder_path, "dsconfig.yaml"), "r") as f:
                config = yaml.safe_load(f)
                config["phonemes"] = "../dsvariance/diffsinger_variance_phonemes.json"
                config["languages"] = "../dsvariance/diffsinger_variance_languages.json"
                config["variance"] = "../dsvariance/variance.onnx"
                config["linguistic"] = "../dsvariance/linguistic.onnx"
                config["dur"] = "../dsdur/dur.onnx"
                if len(found_emb_files) > 0:
                    config["speakers"] = [f"../dsvariance/{os.path.splitext(f)[0]}" for f in found_emb_files]
            # move variance files to "dsvariance" folder
            os.makedirs(os.path.join(folder_path, "..", "dsvariance"), exist_ok=True)
            for file in dsvariance_files:
                shutil.move(os.path.join(folder_path, file), os.path.join(folder_path, "..", "dsvariance", file))
            # move emb files to "dsvariance" folder
            for file in found_emb_files:
                shutil.move(os.path.join(folder_path, file), os.path.join(folder_path, "..", "dsvariance", file))
            # move dsdur files to "dsdur" folder
            os.makedirs(os.path.join(folder_path, "..", "dsdur"), exist_ok=True)
            for file in dsdur_files:
                shutil.move(os.path.join(folder_path, file), os.path.join(folder_path, "..", "dsdur", file))
            # move dspitch files to "dspitch" folder
            for file in dspitch_files:
                if os.path.exists(os.path.join(folder_path, file)):
                    found_pitch = True
                    config["pitch"] = "../dspitch/pitch.onnx"
                    os.makedirs(os.path.join(folder_path, "..", "dspitch"), exist_ok=True)
                    shutil.move(os.path.join(folder_path, file), os.path.join(folder_path, "..", "dspitch", file))
            # move dsvocoder files to "dsvocoder" folder
            for file in dsvocoder_files:
                if os.path.exists(os.path.join(folder_path, file)):
                    found_vocoder = True
                    os.makedirs(os.path.join(folder_path, "..", "dsvocoder"), exist_ok=True)
                    shutil.move(os.path.join(folder_path, file), os.path.join(folder_path, "..", "dsvocoder", file))
            # load languages
            with open(os.path.join(folder_path, "..", "dsvariance", "diffsinger_variance_languages.json"), "r") as f:
                languages = json.load(f)
            # write new config
            with open(os.path.join(folder_path, "..", "dsvariance", "dsconfig.yaml"), "w") as f:
                yaml.dump(config, f, allow_unicode=True)
            with open(os.path.join(folder_path, "..", "dsdur", "dsconfig.yaml"), "w") as f:
                yaml.dump(config, f, allow_unicode=True)
            if found_pitch:
                with open(os.path.join(folder_path, "..", "dspitch", "dsconfig.yaml"), "w") as f:
                    yaml.dump(config, f, allow_unicode=True)
            
            # remove old config
            os.remove(os.path.join(folder_path, "dsconfig.yaml"))
            
            break
            
    # second pass: find dsmain folder
    for folder_path in folder_paths:
        folder_files = os.listdir(folder_path)
        
        if "acoustic.onnx" in folder_files:
            # mark this folder as dsmain
            acoustic_path = folder_path
            # search for emb files
            found_emb_files_ = [f for f in folder_files if f.endswith(".emb")]
            if found_emb_files is not None and len(found_emb_files_) > 0:
                if len(found_emb_files_) != len(found_emb_files):
                    print(f"WARNING: no matching emb files found for {folder_path}")
            dsmain_files = [
                "acoustic.onnx",
                "diffsinger_acoustic.languages.json",
                "diffsinger_acoustic.phonemes.json",
            ]
            # edit dsmain config
            with open(os.path.join(folder_path, "dsconfig.yaml"), "r") as f:
                config = yaml.safe_load(f)
                config["acoustic"] = "dsmain/acoustic.onnx"
                config["phonemes"] = "diffsinger_acoustic.phonemes.json"
                config["languages"] = "diffsinger_acoustic.languages.json"
                if len(found_emb_files) > 0:
                    config["speakers"] = [os.path.splitext(f)[0] for f in found_emb_files]
                if found_vocoder:
                    config["vocoder"] = "dsvocoder/vocoder.onnx"
            with open(os.path.join(folder_path, "dsconfig.yaml"), "w") as f:
                yaml.dump(config, f, allow_unicode=True)
            # move non-dsmain files to parent folder
            for file in folder_files:
                if file not in dsmain_files:
                    shutil.move(os.path.join(folder_path, file), os.path.join(folder_path, "..", file))
            # move dsmain files to dsmain folder
            os.makedirs(os.path.join(folder_path, "..", "dsmain"), exist_ok=True)
            for file in dsmain_files:
                shutil.move(os.path.join(folder_path, file), os.path.join(folder_path, "..", "dsmain", file))
            break
        
    if acoustic_path is None and variance_path is None:
        print("No acoustic model and variance model found. Exiting.")
        exit(1)
    
    # make dsdict.yaml from dict_path file and <variance_path>/dictionary.txt
    # entries:
    # - grapheme: a grapheme
    #   phonemes:
    #     - phoneme
    #     - another phoneme
    # symbols:
    # - symbol: a symbol
    #   type: symbol type (vowel, stop)
    
    entries = []
    vowel_symbols = {"a", "e", "i", "o", "u", "N"}
    vowel_list = []
    stop_list = []
    
    with open(dict_path, "r") as f:
        for line in f:
            line = line.strip()
            # if line.startswith("#"):
            #     continue
            # print(line.split("\t", 1))
            grapheme, phonemes = line.split("\t", 1)
            phonemes = phonemes.split(" ")
            entries.append({
                "grapheme": grapheme,
                "phonemes": phonemes,
            })
            
    for lang in languages.keys():
        with open(os.path.join(variance_path if variance_path is not None else os.path.join(acoustic_path, ".."), f"dictionary-{lang}.txt"), "r") as f:
            for line in f:
                line = line.strip()
                # if line.startswith("#"):
                #     continue
                phonemes = line.split("\t", 1)
                phoneme_type = "vowel" if phonemes[0] in vowel_symbols else "stop"
                if phoneme_type == "vowel":
                    vowel_list.append({"symbol": phonemes[0], "type": phoneme_type})
                else:
                    stop_list.append({"symbol": phonemes[0], "type": phoneme_type})
                
    # sort vowel_list and stop_list by symbol
    vowel_list.sort(key=lambda x: x["symbol"])
    stop_list.sort(key=lambda x: x["symbol"])
    
    symbols_list = vowel_list + stop_list
    
    # write dsdict.yaml to dsdur, dspitch and dsvariance
    dsdict_obj = {
        "entries": entries,
        "symbols": symbols_list,
    }
    dsdict_target_paths = [
        os.path.join(acoustic_path, "..", "dsdur", "dsdict.yaml"),
        os.path.join(acoustic_path, "..", "dsvariance", "dsdict.yaml"),
    ]
    if found_pitch:
        dsdict_target_paths.append(os.path.join(acoustic_path, "..", "dspitch", "dsdict.yaml"))
    for target_path in dsdict_target_paths:
        with open(target_path, "w") as f:
            yaml.dump(dsdict_obj, f, allow_unicode=True)
            
    # write character.txt
    with open(os.path.join(acoustic_path, "..", "character.txt"), "w") as f:
        f.write(f"name={chara_name}\n")
        f.write(f"image=\n")
        f.write(f"author=\n")
        f.write(f"voice=\n")
        f.write(f"web=\n")
        
    # write character.yaml
    with open(os.path.join(acoustic_path, "..", "character.yaml"), "w") as f:
        character_yaml = {
            "text_file_encoding": "utf-8",
            "portrait": None,
            "portrait_opacity": 0.67,
            "default_phonemizer": "OpenUtau.Core.DiffSinger.DiffSingerPhonemizer",
            "singer_type": "diffsinger",
        }
        if found_emb_files is not None and len(found_emb_files) > 0:
            emb_file_names = [os.path.splitext(f)[0] for f in found_emb_files]
            character_yaml["subbanks"] = [{
                "color": f"{i:02}: {emb_file_name}",
                "suffix": emb_file_name,
            } for i, emb_file_name in enumerate(emb_file_names, start=1)]
        yaml.dump(character_yaml, f, allow_unicode=True)
            
    # remove acoustic_path and variance_path trees
    if acoustic_path is not None:
        shutil.rmtree(acoustic_path)
    if variance_path is not None:
        shutil.rmtree(variance_path)
        
    # move <output_path>/onnx folder to chara_name folder
    final_output_path = os.path.join(output_path, chara_name.replace(" ", "_"))
    shutil.move(os.path.join(output_path, "onnx"), final_output_path)
    
    return final_output_path
    

def main():
    parser = argparse.ArgumentParser(description='Export DiffSinger models to ONNX format')
    parser.add_argument('--acoustic', type=str, help='Path to acoustic checkpoint', default='')
    parser.add_argument('--variance', type=str, help='Path to variance checkpoint', default='')
    parser.add_argument('--output', type=str, required=True, help='Output folder path')
    parser.add_argument('--quiet', action='store_true', help='Hide ONNX converter output')
    parser.add_argument('--conda', type=str, help='Path to conda executable', default='conda')
    parser.add_argument('--make_ou_compatible', action='store_true', help='Make files compatible with OpenUtau')
    parser.add_argument('--dict_file', type=str, default='../../jpn_dict_stops.txt', help='Path to dictionary file')
    parser.add_argument('--chara_name', type=str, default='your diffsinger voice bank', help='Character name')
    args = parser.parse_args()

    # Setup environment
    setup_environment(conda_executable=args.conda)

    # Export models
    folder_paths = []
    
    if args.acoustic:
        acoustic_path = export_model('acoustic', args.acoustic, args.output, args.quiet, args.conda)
        folder_paths.append(acoustic_path)
        
    if args.variance:
        variance_path = export_model('variance', args.variance, args.output, args.quiet, args.conda)
        folder_paths.append(variance_path)

    # Rename files
    if folder_paths:
        if args.make_ou_compatible:
            final_output_path = make_ou_compatible(folder_paths, args.output, args.chara_name, args.dict_file)
            print(f"\nONNX export complete: {final_output_path}.\nEdit character.txt to finalize your model before publish it!\n Please refer to https://github.com/xunmengshe/OpenUtau/wiki/Voicebank-Development for more information")
        else:
            rename_files(folder_paths)
            print("\nONNX export complete! Please refer to https://github.com/xunmengshe/OpenUtau/wiki/Voicebank-Development to make your model OU compatible")

if __name__ == "__main__":
    main()
