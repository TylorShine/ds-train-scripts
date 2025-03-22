import os
import glob
import numpy as np
import librosa
import pydomino
import argparse

from tqdm import tqdm


def pre_cleanup(text: str):
    # replace U before a, e, i, o, u, cl, N with u and replace ty with t i
    replace_list = [
        ("U a", "u a"),
        ("U e", "u e"),
        ("U i", "u i"),
        ("U o", "u o"),
        ("U u", "u u"),
        ("U cl", "u cl"),
        ("U N", "u N"),
        ("ty", "t"),
        ("kw", "k"),
        ("gw", "g"),
    ]
    
    p = text.split(" ")
    p = [p[i] for i in range(len(p)) if p[i] != ""]
    
    # merge repeated N
    offset = 0
    for i in range(len(p) - 1):
        if p[i - offset] == "N" and p[i - offset + 1] == "N":
            p.pop(i - offset + 1)
            offset += 1
    
    p = " ".join(p)
    
    for r in replace_list:
        p = p.replace(r[0], r[1])
        
    return p


def align_domino(text: str, wav_path: str, model, model_path: str, cleanup: bool = True, device: str = "cpu"):
    if model is None:
        global _DOMINO_MODEL
        _DOMINO_MODEL = pydomino.Aligner(model_path)
        model = _DOMINO_MODEL
        
    # y_sr = librosa.get_samplerate(wav_path)
    y: np.ndarray = librosa.load(wav_path, sr=16_000, mono=True, dtype=np.float32)[0]
    
    if cleanup:
        p = pre_cleanup(text)
    else:
        p = text
    
    try:
        # align
        # list[tuple[seconds_start, seconds_end, phoneme]]
        z: list[tuple[float, float, str]] = model.align(y, p, 3)
        
        # # replace pau with SP
        # z = [(a, b, "SP") if q == "pau" else (a, b, q) for a, b, q in z]
        
        # # convert seconds to samples
        # z = [(int(a * y_sr), int(b * y_sr), q) for a, b, q in z]
        
        # convert seconds to 100 nanoseconds (htk format)
        z = [(int(a * 1000 * 1000 * 10 + 0.5), int(b * 1000 * 1000 * 10 + 0.5), q) for a, b, q in z]
        
        # to string
        z = '\n'.join([f"{a}\t{b}\t{q}" for a, b, q in z])
        
        return z, model
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error processing {wav_path}, {p}: {e}")
        raise e


def main(input_dir: str, output_dir: str, model_path: str, audio_ext: list[str], phoneme_ext: str = ".lab", output_ext: str = ".domino-lab"):
    if not os.path.exists(input_dir):
        print(f"Error: Input directory not found: {input_dir}")
        return

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created output directory: {output_dir}")
        
    # Find all phoneme_ext files in the input directory
    text_files = glob.glob(os.path.join(input_dir, f"*{phoneme_ext}"))

    if not text_files:
        print(f"No {phoneme_ext} files found in {input_dir}")
        return

    file_count = 0
    for text_file in tqdm(text_files):
        wav_path = None
        for ae in audio_ext:
            _wav_path = os.path.splitext(text_file)[0] + ae
            if not os.path.exists(_wav_path):
                continue
            wav_path = _wav_path
            break
            
        if wav_path is None:
            print(f"Cannot find wav file for {text_file}, skipping...")
            continue
        
        output_file = os.path.join(output_dir, os.path.splitext(text_file)[0] + output_ext)
        
        if os.path.exists(output_file):
            with open(output_file, 'r') as f:
                if f.read() != "":
                    print(f"Skipping {text_file} because {output_file} already exists")
                    continue
        
        global aligner
        if aligner is None:
            aligner = pydomino.Aligner(model_path)

        y: np.ndarray = librosa.load(wav_path, sr=16_000, mono=True, dtype=np.float32)[0]
        
        # replace U before a, e, i, o, u, cl with u and replace ty with t i
        replace_list = [
            ("U a", "u a"),
            ("U e", "u e"),
            ("U i", "u i"),
            ("U o", "u o"),
            ("U u", "u u"),
            ("U cl", "u cl"),
            ("U N", "u N"),
            ("ty", "t"),    # 
            ("kw", "k"),
            ("gw", "g"),
        ]
        
        with open(text_file, 'r') as f:
            p: list[str] = f.read().split(' ')
        p = [p[i] for i in range(len(p)) if p[i] != ""]
        
        # merge repeated N
        offset = 0
        for i in range(len(p) - 1):
            if p[i - offset] == "N" and p[i - offset + 1] == "N":
                p.pop(i - offset + 1)
                offset += 1
        
        p = " ".join(p)
        
        for r in replace_list:
            p = p.replace(r[0], r[1])
        
        z: list[tuple[float, float, str]] = aligner.align(y, p, 3)
    
        with open(output_file, "w") as f:
            for t, d, p in z:
                f.write(f"{t:.3f}\t{d:.3f}\t{p}\n")
            
if __name__ == "__main__":
    global aligner
    aligner: pydomino.Aligner = None
    parser = argparse.ArgumentParser(description="Convert text files to phoneme files using pydomino.")
    parser.add_argument("input_dir", help="Path to the input directory containing text files.")
    parser.add_argument("output_dir", help="Path to the output directory for phoneme files.")
    parser.add_argument("model_path", help="Path to the pydomino model.")
    parser.add_argument("-a", "--audio_ext", nargs='+', default=['.wav', '.flac'], help="File extension for audio files.")
    parser.add_argument("-p", "--phoneme_ext", default=".lab", help="Path to the phoneme file.")
    parser.add_argument("-o", "--output_ext", default=".domino-lab", help="Path to the output phoneme file.")
    args = parser.parse_args()
    
    main(args.input_dir, args.output_dir, args.model_path, args.audio_ext, phoneme_ext=args.phoneme_ext, output_ext=args.output_ext)