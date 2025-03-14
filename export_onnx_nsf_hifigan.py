#!/usr/bin/env python3
import os
import subprocess
import zipfile
import shutil
import argparse

def setup_environment(conda_executable="conda"):
    """Setup conda environment for ONNX conversion"""
    env_name = "diffsinger_onnx"
    env_check = f"{conda_executable} env list | grep '^{env_name} '"

    if os.system(env_check) != 0:
        os.system(f'{conda_executable} create -n diffsinger_onnx python=3.10 -y')
        os.system(f'{conda_executable} run -n diffsinger_onnx pip install -r requirements-onnx.txt')
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
    
    if model_type != "nsf-hifigan":
        # Copy config
        shutil.copy(f'{folder_path}/config.yaml', f'checkpoints/{folder_name}')    
        
        # Update hparams
        update_hparams(folder_path)
    
    # Run export
    output_path = f"{exp_folder}/onnx/{model_type}"
    if model_type == "fir-acoustic-vocoder":
        export_cmd = f"python scripts/export.py {model_type} --exp {folder_name} --out {output_path}"
    elif model_type == "nsf-hifigan":
        export_cmd = f"{conda_executable} run -n diffsinger_onnx python scripts/export.py {model_type} --config {os.path.dirname(checkpoint_path)}/config.json --ckpt {checkpoint_path} --out {output_path} --name {os.path.basename(os.path.dirname(checkpoint_path))}"
    else:
        export_cmd = f"{conda_executable} run -n diffsinger_onnx python scripts/export.py {model_type} --exp {folder_name} --out {output_path}"
    
    if no_output:
        export_cmd += " >/dev/null 2>&1"
    
    os.system(export_cmd)
    # os.system(f"{conda_executable} run -n diffsinger_onnx python scripts/export.py --help")
    # import sys
    # sys.exit()
    
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
            if "acoustic_acoustic." in filename:
                new_filename = filename.replace("acoustic_acoustic.", "acoustic_")
            elif "variance_variance." in filename:
                new_filename = filename.replace("variance_variance.", "variance_")
            else:
                new_filename = filename
            old_path = os.path.join(folder_path, filename)
            new_path = os.path.join(folder_path, new_filename)
            # os.rename(old_path, new_path)
            shutil.move(old_path, new_path)

def main():
    parser = argparse.ArgumentParser(description='Export DiffSinger models to ONNX format')
    parser.add_argument('--acoustic', type=str, help='Path to acoustic checkpoint', default='')
    parser.add_argument('--variance', type=str, help='Path to variance checkpoint', default='')
    parser.add_argument('--fir_acoustic_vocoder', type=str, help='Path to FirSinger acoustic/vocoder checkpoint', default='')
    parser.add_argument('--nsf_hifigan', type=str, help='Path to NSF-HiFiGAN checkpoint', default='')
    parser.add_argument('--output', type=str, required=True, help='Output folder path')
    parser.add_argument('--quiet', action='store_true', help='Hide ONNX converter output')
    parser.add_argument('--conda', type=str, help='Path to conda executable', default='conda')
    args = parser.parse_args()

    # Clean up existing files
    if os.path.exists("OU_compatible_files"):
        shutil.rmtree("OU_compatible_files")
        if os.path.exists("jpn_dict.txt"):
            os.remove("jpn_dict.txt")

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
        
    if args.fir_acoustic_vocoder:
        fir_acoustic_vocoder_path = export_model('fir-acoustic-vocoder', args.fir_acoustic_vocoder, args.output, args.quiet, args.conda)
        folder_paths.append(fir_acoustic_vocoder_path)
        
    if args.nsf_hifigan:
        variance_path = export_model('nsf-hifigan', args.nsf_hifigan, args.output, args.quiet, args.conda)
        # folder_paths.append(variance_path)

    # Rename files
    if folder_paths:
        rename_files(folder_paths)
        print("\nONNX export complete! Please refer to https://github.com/xunmengshe/OpenUtau/wiki/Voicebank-Development to make your model OU compatible")

if __name__ == "__main__":
    main()
