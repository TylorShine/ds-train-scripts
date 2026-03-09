import os
import csv
import json
import shutil
import re
import argparse

def parse_args():
    parser = argparse.ArgumentParser(description='Extract and process audio data for DiffSinger/NNSVS')
    parser.add_argument('--data_type', choices=['lab_wav', 'csv_wav', 'ds'],
                      default='lab_wav', help='Type of data to process')   # lab_wav: NNSVS format, csv_wav, ds: DiffSinger format
    parser.add_argument('--data_zip_path', type=str, required=True, help='Path to data zip file')
    parser.add_argument('--no_cleanup', action='store_true', help='Do not cleanup data directory')
    parser.add_argument('--estimate_midi', choices=['False', 'parselmouth', 'harvest', 'SOME'],
                      default='False', help='MIDI estimation method')
    parser.add_argument('--segment_length', type=int, default=15, help='Segment length in seconds')
    parser.add_argument('--max_silence_phoneme', type=int, default=2, help='Maximum silence phonemes allowed')
    parser.add_argument('--transcription_batch_size', type=int, default=1, help='Batch size for transcription')
    parser.add_argument('--transcription_model', type=str,
                      default='False', help='Model for transcription (when no exist it)\n ex) `openai/whisper-large`')
    parser.add_argument('--transcription_language', type=str,
                      default='ja', help='Language for transcription')
    parser.add_argument('--transcription_phoneme_model', type=str,
                        default='False', help='Model for transcription with phoneme (when no exist it)\n ex) `TylorShine/wavlm-base-plus-hiragana-ctc-v2`')
    parser.add_argument('--g2p_alignment_type', choices=['openjtalk+SOFA', 'openjtalk+domino', 'domino', 'ctc'],
                      default='openjtalk+SOFA', help='G2P alignment type')
    parser.add_argument('--g2p_model_path', type=str,
                      default='pydomino/onnx_model/phoneme_transition_model.onnx',
                      help="G2P model path")
    parser.add_argument('--sofa_model_path', type=str,
                      default="pretrain_models/sofa.japanese.test2.plus.step.100000.ckpt",
                      help="SOFA model path")
    parser.add_argument('--sofa_dict_path', type=str,
                      default="../japanese-extension-sofa-added.txt",
                      help="SOFA dictionary path")
    parser.add_argument('--keep_punctuations', action='store_true', help='Try to keep punctuations')
    parser.add_argument('--use_punctuator', action='store_true', help='Use punctuation predictor (e.g. Kotoba-Whisper-v2.1)')
    return parser.parse_args()

def setup_directories(no_cleanup=False):
    all_shits = os.path.join(os.getcwd(), "raw_data")
    all_shits_not_wav_n_lab = os.path.join(all_shits, "diffsinger_db")
    
    if not no_cleanup and os.path.exists(all_shits):
        shutil.rmtree(all_shits)
    
    if not os.path.exists(all_shits_not_wav_n_lab):
        os.makedirs(all_shits_not_wav_n_lab)
    
    return all_shits, all_shits_not_wav_n_lab

def extract_archive(data_zip_path, extract_path):
    if os.path.exists(data_zip_path):
        zip_file_name = os.path.splitext(os.path.basename(data_zip_path))[0]
        with open(os.path.join(extract_path, "..", "..", "project_name.txt"), "w") as f:
            f.write(zip_file_name)
            
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


def make_lab_files(args, root_path):
    if args.transcription_model == 'False' and args.transcription_phoneme_model == 'False':
        print("No transcription model or phoneme model specified. Skipping...")
        return
    
    import torch
    from transformers import pipeline, AutoProcessor
    import numpy as np
    import librosa
    from tqdm import tqdm
    if args.g2p_alignment_type.startswith('openjtalk'):
        from g2p_openjtalk import g2p_openjtalk as g2p
        
    if args.g2p_alignment_type.endswith('SOFA'):
        sofa_infer_script = "./SOFA/infer.py"
    elif args.g2p_alignment_type.endswith('domino'):
        from align_domino import align_domino as aligner
        from align_domino import pre_cleanup as aligner_pre_cleanup
        
    if args.transcription_phoneme_model != 'False':
        import torchaudio
        from transformers import AutoModel, AutoTokenizer, AutoFeatureExtractor
        
    global g2p_model
    g2p_model = None
        
    global transcription_model
    transcription_model = None
    
    global transcription_phoneme_model
    transcription_phoneme_model = None
    
    global transcription_g2p_tokenizers
    transcription_g2p_tokenizers = None
    global transcription_g2p_feature_extractor
    transcription_g2p_feature_extractor = None
        
    def make_lab_into_dir(root_path):
        global transcription_model, g2p_model, transcription_phoneme_model, transcription_g2p_tokenizers, transcription_g2p_feature_extractor
        for root, _, files in os.walk(root_path):
            wav_exists = False
            max_wav_duration = 0.0
            need_transcription_files = []
            need_phonemization_files = []
            need_alignment_files = []
            file_paths = [os.path.join(root, file) for file in files]
            for filename in files:
                file_path = os.path.join(root, filename)
                if os.path.isdir(file_path):
                    make_lab_into_dir(file_path)
                elif os.path.isfile(file_path) and file_path.endswith('.wav'):
                    wav_exists = True
                    if not os.path.splitext(file_path)[0] + '.lab' in file_paths and (args.transcription_model != 'False' or args.transcription_phoneme_model != 'False'):
                        wav_duration = librosa.get_duration(filename=file_path)
                        if wav_duration > max_wav_duration:
                            max_wav_duration = wav_duration
                        need_alignment_files.append(file_path)
                        if not os.path.splitext(file_path)[0] + '.txt' in file_paths:
                            need_transcription_files.append(file_path)
                        if not os.path.splitext(file_path)[0] + '.phonemes.txt' in file_paths:
                            need_phonemization_files.append(file_path)
            # need_alignment_files = set(need_alignment_files)
            # need_transcription_files = set(need_transcription_files)
            already_transcription_files = set(need_alignment_files) - set(need_transcription_files)
            already_phonemization_files = set(need_alignment_files) - set(need_phonemization_files)
            if wav_exists == True and len(need_alignment_files) > 0:
                # transcription and alignment
                phonemeses = {}
                all_texts = {}
                if len(need_transcription_files) + len(need_phonemization_files) > 0:
                    torch_dtype = torch.bfloat16 if torch.cuda.is_available() else torch.float32
                    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
                    if args.transcription_phoneme_model == 'False':
                        # return_timestamps = max_wav_duration > 30.0 if args.g2p_alignment_type != 'whisper+domino' else "word"
                        return_timestamps = max_wav_duration > 30.0
                        # generate_kwargs = {"language": args.transcription_language, "task": "transcribe", "return_timestamps": return_timestamps}
                        generate_kwargs = {"language": args.transcription_language, "task": "transcribe"}
                        if transcription_model is None:
                            if torch.cuda.is_available():
                                if return_timestamps == "word":
                                    model_kwargs = {"attn_implementation": "eager"}
                                else:
                                    model_kwargs = {"attn_implementation": "sdpa"}
                            else:
                                model_kwargs = {}
                                
                            pipeline_kwargs = {
                                "trust_remote_code": True,
                            }
                            if args.use_punctuator:
                                pipeline_kwargs["punctuator"] = True
                                
                            processor = AutoProcessor.from_pretrained(args.transcription_model)
                            
                            transcription_model = pipeline(
                                # "automatic-speech-recognition",
                                torch_dtype=torch_dtype,
                                device=device,
                                feature_extractor=processor.feature_extractor,
                                model=args.transcription_model,    # "openai/whisper-base", "openai/whisper-small", "openai/whisper-medium", "openai/whisper-large" etc.
                                model_kwargs=model_kwargs,
                                **pipeline_kwargs,
                            )
                        transcribed_texts = transcription_model(need_transcription_files, generate_kwargs=generate_kwargs, return_timestamps=return_timestamps, batch_size=args.transcription_batch_size)
                    else:
                        print(f"Transcription with phoneme model: {args.transcription_phoneme_model}")
                        if transcription_phoneme_model is None:
                            tokenizer_subfolders = ["kana_tokenizer", "phoneme_tokenizer"]
                            transcription_g2p_feature_extractor = AutoFeatureExtractor.from_pretrained(args.transcription_phoneme_model, trust_remote_code=True)
                            transcription_g2p_tokenizers = {
                                "kana_tokenizer": AutoTokenizer.from_pretrained(args.transcription_phoneme_model, trust_remote_code=True, subfolder=tokenizer_subfolders[0]),
                                "phoneme_tokenizer": AutoTokenizer.from_pretrained(args.transcription_phoneme_model, trust_remote_code=True, subfolder=tokenizer_subfolders[1]),
                            }
                            transcription_phoneme_model = AutoModel.from_pretrained(args.transcription_phoneme_model, trust_remote_code=True).to(device)
                        transcribed_texts = []
                        need_transcription_files_batched = [need_transcription_files[i:i+args.transcription_batch_size] for i in range(0, len(need_transcription_files), args.transcription_batch_size)]
                        
                        def get_ctc_forced_alignment(
                            logits: torch.Tensor,
                            token_ids: list[int],
                            blank_id: int = 0,
                            frame_rate: float = 50.0,  # 50 frames/sec (20ms/frame) for HuBERT
                            pad_sec: float = 0.1,      # padded silence length (sec)
                            delay_sec: float = 0.0    # calibration delay for Emission Delay of CTC (sec)
                        ):
                            if logits.ndim == 2:
                                logits = logits.unsqueeze(0)  # add batch dimension (1, frames, num_tokens)
                                
                            # targets = torch.tensor(token_ids, dtype=torch.int32, device=logits.device)
                            targets = token_ids
                            # remove blank
                            targets = targets[targets != blank_id]
                            if targets.ndim == 1:
                                targets = targets.unsqueeze(0)  # add batch dimension (1, num_tokens)
                            # print(targets)
                            
                            # Forced Alignment
                            alignments, scores = torchaudio.functional.forced_align(logits, targets, blank=blank_id)
                            alignments = alignments[0]
                            scores = scores[0].exp()  # back to probability
                            
                            # merge tokens
                            token_spans = torchaudio.functional.merge_tokens(alignments, scores)
                            
                            total_offset_sec = pad_sec + delay_sec
                            results =[]
                            for span in token_spans:
                                # frame index to sec
                                start_time_sec = span.start / frame_rate
                                end_time_sec = span.end / frame_rate
                                # correct time
                                corrected_start = max(0.0, start_time_sec - total_offset_sec)
                                corrected_end   = max(0.0, end_time_sec - total_offset_sec)
                                results.append({
                                    "token_id": span.token,
                                    "start_time": round(corrected_start, 3),
                                    "end_time": round(corrected_end, 3),
                                    "score": round(span.score, 4)
                                })
                                
                            return results, total_offset_sec
                        
                        with torch.no_grad():
                            for i, need_transcription_files_batch in enumerate(tqdm(need_transcription_files_batched, desc='transcription+g2p')):
                                wav_files = [wav for wav, _ in [librosa.load(wav_path, sr=16_000, mono=True, dtype=np.float32) for wav_path in need_transcription_files_batch]]
                                max_wav_samples = max(len(wav) for wav in wav_files)
                                max_wav_samples = max_wav_samples + 8_000   # +0.5s
                                wav_files_padded = np.array([np.pad(wav, (max_wav_samples - len(wav), 0), 'constant') for wav in wav_files])
                                features = transcription_g2p_feature_extractor(wav_files_padded, sampling_rate=16_000, return_tensors="pt", return_attention_mask=True)
                                input_values = features.input_values.to(device)
                                attention_mask = features.attention_mask.to(device)
                                outputs = transcription_phoneme_model(input_values, attention_mask=attention_mask)
                                kana_logits_argmax = outputs["kana_logits"].argmax(dim=-1)
                                phoneme_logits_argmax = outputs["phoneme_logits"].argmax(dim=-1)
                                if args.g2p_alignment_type.endswith('ctc'):
                                    for i, (phoneme_logits, filename) in enumerate(zip(outputs["phoneme_logits"], need_transcription_files_batch)):
                                        additional_padded_sec = (max_wav_samples - len(wav_files[i])) / 16_000
                                        phoneme_aligned, total_offset_sec = get_ctc_forced_alignment(phoneme_logits, phoneme_logits_argmax[i], pad_sec=additional_padded_sec, blank_id=transcription_g2p_tokenizers["phoneme_tokenizer"].pad_token_id)
                                        
                                        wav_array = wav_files[i]
                                        
                                        is_speech = np.zeros(len(wav_array), dtype=bool)
                                        non_silent_intervals = librosa.effects.split(wav_array, top_db=30)
                                        for start_samp, end_samp in non_silent_intervals:
                                            is_speech[start_samp:end_samp] = True
                                        
                                        phonemes = [["0", "0", "pau"]]
                                        current_sec = 0.0
                                        for item in phoneme_aligned:
                                            # get char from token id in phoneme_aligned
                                            phoneme = transcription_g2p_tokenizers["phoneme_tokenizer"].decode(item["token_id"])
                                            start_sec = item["start_time"]
                                            end_sec = item["end_time"]
                                            
                                            if end_sec <= start_sec:
                                                continue
                                            
                                            if start_sec > current_sec and len(phonemes) > 0:
                                                # # add silence
                                                # sil_start_htk = int(round(current_sec * 10_000_000))
                                                # sil_end_htk = int(round(start_sec * 10_000_000))
                                                # if sil_end_htk > sil_start_htk:
                                                #     phonemes.append([str(sil_start_htk), str(sil_end_htk), "pau"])
                                                
                                                # # change previous end time
                                                # phonemes[-1][1] = str(int(round(start_sec * 10_000_000)))
                                                
                                                # Analyze the gap between the last phoneme and the current CTC spike
                                                gap_start_samp = min(int(current_sec * 16_000), len(wav_array))
                                                gap_end_samp = min(int(start_sec * 16_000), len(wav_array))
                                                
                                                gap_speech = is_speech[gap_start_samp:gap_end_samp]
                                                silence_indices = np.where(~gap_speech)[0]
                                                
                                                # If we find at least 20ms of silence (320 samples at 16kHz) in this gap
                                                if len(silence_indices) > 320 and not phonemes[-1][2] == "cl":
                                                    sil_start_in_gap = silence_indices[0]
                                                    sil_end_in_gap = silence_indices[-1]
                                                    
                                                    actual_sil_start_sec = current_sec + (sil_start_in_gap / 16_000)
                                                    actual_sil_end_sec = current_sec + (sil_end_in_gap / 16_000)
                                                    
                                                    sil_start_htk = int(round(actual_sil_start_sec * 10_000_000))
                                                    sil_end_htk = int(round(actual_sil_end_sec * 10_000_000))
                                                    
                                                    if phonemes[-1][2] == "pau":
                                                        # Merge into previous pause
                                                        phonemes[-1][1] = str(sil_end_htk)
                                                    else:
                                                        # Stop previous phoneme exactly where silence starts, then insert pau
                                                        phonemes[-1][1] = str(sil_start_htk)
                                                        phonemes.append([str(sil_start_htk), str(sil_end_htk), "pau"])
                                                    
                                                    # The current phoneme effectively starts right after the silence
                                                    phoneme_start_sec = actual_sil_end_sec
                                                else:
                                                    # No significant silence detected, stretch previous phoneme
                                                    phonemes[-1][1] = str(int(round(start_sec * 10_000_000)))
                                                    phoneme_start_sec = start_sec
                                            else:
                                                phoneme_start_sec = start_sec
                                                
                                            phoneme_end_sec = max(end_sec, phoneme_start_sec)
                                                    
                                            # start_htk = int(round(start_sec * 10_000_000))
                                            # end_htk = int(round(end_sec * 10_000_000))
                                            
                                            # phonemes.append([str(start_htk), str(end_htk), phoneme])
                                            # current_sec = end_sec
                                            
                                            start_htk = int(round(phoneme_start_sec * 10_000_000))
                                            end_htk = int(round(phoneme_end_sec * 10_000_000))
                                            
                                            phonemes.append([str(start_htk), str(end_htk), phoneme])
                                            current_sec = phoneme_end_sec
                                            
                                        # add silence
                                        wav_sec = wav_files[i].shape[0] / 16_000
                                        sil_start_htk = int(round(current_sec * 10_000_000))
                                        sil_end_htk = int(round(wav_sec * 10_000_000))
                                        if len(phonemes) > 1 and sil_end_htk > sil_start_htk:
                                            # # detect end of silence
                                            # _, index = librosa.effects.trim(wav_files[i], top_db=30)
                                            # detected_end_sec = index[1] / 16_000
                                            # last_phoneme_end_sec = max(current_sec + 0.05, detected_end_sec)
                                            # last_phoneme_end_htk = int(round(last_phoneme_end_sec * 10_000_000))
                                            # last_phoneme_end_htk = min(last_phoneme_end_htk, sil_end_htk)
                                            # phonemes[-1][1] = str(last_phoneme_end_htk)
                                            # phonemes.append([str(last_phoneme_end_htk), str(sil_end_htk), "pau"])
                                            
                                            # Find the last moment of speech in the file
                                            speech_indices = np.where(is_speech)[0]
                                            if len(speech_indices) > 0:
                                                detected_end_sec = speech_indices[-1] / 16_000
                                            else:
                                                detected_end_sec = current_sec
                                                
                                            last_phoneme_start_sec = int(phonemes[-1][0]) / 10_000_000
                                            last_phoneme_end_sec = max(last_phoneme_start_sec + 0.05, detected_end_sec)
                                            last_phoneme_end_sec = min(last_phoneme_end_sec, wav_sec)
                                            
                                            last_phoneme_end_htk = int(round(last_phoneme_end_sec * 10_000_000))
                                            phonemes[-1][1] = str(last_phoneme_end_htk)
                                            
                                            if sil_end_htk > last_phoneme_end_htk:
                                                if phonemes[-1][2] == "pau":
                                                    phonemes[-1][1] = str(sil_end_htk)
                                                else:
                                                    phonemes.append([str(last_phoneme_end_htk), str(sil_end_htk), "pau"])
                                            
                                            
                                        # save aligned phonemes
                                        with open(os.path.splitext(filename)[0] + '.phonemes_aligned.txt', 'w') as f:
                                            f.write('\n'.join('\t'.join(p) for p in phonemes))
                                            
                                        phonemeses[filename] = '\n'.join('\t'.join(p) for p in phonemes)
                                            
                                    # phoneme_aligned = get_ctc_forced_alignment(outputs["phoneme_logits"], phonemes, blank_id=transcription_g2p_tokenizers["phoneme_tokenizer"].pad_token_id)
                                kanas = [transcription_phoneme_model.ctc_decode(kana_logits.to("cpu").tolist(), transcription_g2p_tokenizers["kana_tokenizer"], is_kana=True) for kana_logits in kana_logits_argmax]
                                phonemes = [transcription_phoneme_model.ctc_decode(phoneme_logits.to("cpu").tolist(), transcription_g2p_tokenizers["phoneme_tokenizer"]) for phoneme_logits in phoneme_logits_argmax]
                                kanas = ["…" if kana.strip() == "" else kana for kana in kanas]
                                phonemes = ["…" if phoneme.strip() == "" else phoneme for phoneme in phonemes]
                                transcribed_texts.extend([{"text": kana, "phoneme": phoneme} for kana, phoneme in zip(kanas, phonemes)])
                                
                                del features, input_values, attention_mask, outputs, kana_logits_argmax, phoneme_logits_argmax, kanas, phonemes
                                del wav_files, wav_files_padded
                                if device.type == "cuda":
                                    torch.cuda.empty_cache()
                
                # save transcripted texts
                for i in range(len(need_transcription_files)):
                    text_file = os.path.splitext(need_transcription_files[i])[0] + '.txt'
                    if not os.path.exists(text_file):
                        all_texts[need_transcription_files[i]] = transcribed_texts[i]["text"]
                        with open(text_file, 'w') as f:
                            f.write(transcribed_texts[i]["text"])
                    if args.transcription_phoneme_model != 'False':
                        if need_transcription_files[i] in already_phonemization_files:
                            continue
                        phoneme_file = os.path.splitext(need_transcription_files[i])[0] + '.phonemes.txt'
                        if not args.g2p_alignment_type.endswith('ctc'):
                            phonemeses[need_transcription_files[i]] = transcribed_texts[i]["phoneme"]
                        with open(phoneme_file, 'w') as f:
                            f.write(transcribed_texts[i]["phoneme"])
                # read existing text files
                for t in already_transcription_files:
                    with open(os.path.splitext(t)[0] + '.txt', 'r') as f:
                        all_texts[t] = f.read()
                for t in already_phonemization_files:
                    with open(os.path.splitext(t)[0] + '.phonemes.txt', 'r') as f:
                        phonemeses[t] = f.read()
                if args.g2p_alignment_type.endswith('SOFA'):
                    # g2p
                    # phonemeses = {k: g2p(text) for k, text in tqdm(all_texts.items(), desc='g2p')}
                    should_be_phonemized = [k for k in all_texts.keys() if k not in phonemeses.keys()]
                    added_phonemeses = {k: g2p(text, args.transcription_language) for k, text in tqdm([all_texts[k] for k in should_be_phonemized], desc='g2p')}
                    phonemeses.update(added_phonemeses)
                    
                    empty_phoneme_keys = []
                    for k, p in phonemeses.items():
                        if p == 'pau  pau' or p == '':
                            # no phonemes, skip
                            # p = 'pau'
                            empty_phoneme_keys.append(k)
                    for k in empty_phoneme_keys:
                        del phonemeses[k]
                elif args.g2p_alignment_type.endswith('domino'):
                    # g2p
                    if args.keep_punctuations:
                        # try to keep punctuations
                        phonemeses = {}
                        # cleaning text
                        # Replace some common half-width punctuation marks with their full-width equivalents
                        replace_list = [
                            ("!", "！"),
                            ("?", "？"),
                            ("...", "…"),
                        ]
                        texts = {k: text for k, text in all_texts.items()}
                        for half, full in replace_list:
                            texts = {k: text.replace(half, full) for k, text in texts.items()}
                        # make punctuations list
                        punctuations_re = re.compile(r'[！？…]+')
                        # vowel_re = re.compile(r"([aiueo])\1{1,}")
                        vowel_list = ["a", "i", "u", "e", "o", 'N', "cl"]
                        extracted_punctuations = []
                        # count pause and punctuation(s, the number of pauses should be equal to the number of punctuation. repeated punctuation will be merged to one)
                        for i, (k, text) in tqdm(enumerate(texts.items()), desc='g2p and alignment', total=len(texts)):
                            extracted_punctuations.append([])
                            if punctuations_re.search(text):
                                extracted_punctuations[i] = punctuations_re.findall(text)
                                
                            split_by_punctuation = punctuations_re.split(text)
                            start_with_punctuation = False
                            if split_by_punctuation[0] == '' and len(split_by_punctuation) > 1:
                                # text starts with punctuation. prefix the text with a 'ん'
                                split_by_punctuation[1] = 'ん' + split_by_punctuation[1]
                                split_by_punctuation.pop(0)
                                start_with_punctuation = True
                            end_with_punctuation = split_by_punctuation[-1] == '' and len(split_by_punctuation) > 1
                            if end_with_punctuation:
                                split_by_punctuation.pop(-1)
                            # g2p split by punctuation
                            phonemeses_list = [g2p(split_text, sandwich_pau=False, no_join=True) for split_text in split_by_punctuation]
                            # remove duplicated vowels
                            for j, ps in enumerate(phonemeses_list):
                                offset = 0
                                for c, phoneme in enumerate(ps):
                                    if phoneme in vowel_list:
                                        if c == 0:
                                            # no process if the first phoneme is a vowel
                                            continue
                                        elif phoneme == ps[c-1-offset] and phoneme in vowel_list:
                                            # remove duplicated vowels
                                            phonemeses_list[j][c] = ''
                                            offset += 1
                                        else:
                                            # reset offset
                                            offset = 0
                            # remove empty phonemes
                            for j, ps in enumerate(phonemeses_list):
                                phonemeses_list[j] = [p for p in ps if p != '']
                            if end_with_punctuation:
                                # text ends with punctuation.
                                # # 1. if the last phoneme is vowel, repeat the last phoneme
                                # 2. if the last phoneme is consonant, add a 'cl' to the last phoneme
                                
                                # if vowel_re.search(phonemeses_list[-1][-1]):
                                #     phonemeses_list = phonemeses_list + [phonemeses_list[-1]]
                                # else:
                                # print(phonemeses_list[-2])
                                # phonemeses_list[-2] = phonemeses_list[-2] + ['cl']
                                phonemeses_list[-1] = phonemeses_list[-1] + ['cl']
                            
                            # sandwich pause
                            phonemeses_list[0] = ['pau'] + phonemeses_list[0]
                            phonemeses_list[-1] = phonemeses_list[-1] + ['pau']
                                
                            # cleanup phonemeses_list and join them with ' pau '
                            phonemes_joined = ' pau '.join([aligner_pre_cleanup(' '.join(phoneme)) for phoneme in phonemeses_list])
                                                        
                            # save phonemes
                            with open(os.path.splitext(k)[0] + '.phonemes.txt', 'w') as f:
                                f.write(phonemes_joined)
                                
                            # align
                            phonemes_timestamped, g2p_model = aligner(phonemes_joined, k, g2p_model, model_path=args.g2p_model_path)
                            # phonemes_timestamped: list of phonemes with timestamps split by '\n'
                            # <start>\t<end>\t<phoneme>\n
                            # ...
                            
                            phonemes_timestamped_split = [p.split('\t', 2) for p in phonemes_timestamped.split('\n')]
                            
                            # restore punctuation
                            phonemes = []
                            phonemeses_list_index = 0
                            is_last_punctuation = phonemeses_list_index == (len(extracted_punctuations[i]) - 1)
                            next_punctuation_insert_index = len(phonemeses_list[0]) - (1 if end_with_punctuation and is_last_punctuation else 0)
                            for j, phoneme in enumerate(phonemes_timestamped_split):
                                if j == 0:
                                    # first pause
                                    phonemes.append(phoneme)
                                elif j == 1:
                                    # first phoneme
                                    if extracted_punctuations[i] and start_with_punctuation:
                                        # if start with punctuation, replace the first phoneme with punctuation
                                        phoneme[2] = extracted_punctuations[i][0]
                                        phonemes.append(phoneme)
                                        # and pop the first punctuation
                                        extracted_punctuations[i].pop(0)
                                    else:
                                        phonemes.append(phoneme)
                                else:
                                    # not first phoneme
                                    if phonemeses_list_index < len(extracted_punctuations[i]):
                                        if j == next_punctuation_insert_index:
                                            # if phonemeses_list_index < len(extracted_punctuations[i]) - (2 if end_with_punctuation and len(extracted_punctuations[i]) > 1 or is_last_punctuation else 1):
                                            if phonemeses_list_index <= len(extracted_punctuations[i]) - (1 if end_with_punctuation else 0):
                                                if phoneme[2] != 'pau' and phoneme[2] != 'SP':
                                                    # maybe mismatch
                                                    print(f"WARNING: punctuation alignment maybe mismatch[{j}]: {phoneme[2]}, {extracted_punctuations[i][phonemeses_list_index]}")
                                                    print(phoneme)
                                            else:
                                                if phoneme[2] != 'cl':
                                                    # maybe mismatch
                                                    print(f"WARNING: punctuation alignment maybe mismatch[{j}]: {phoneme[2]}, {extracted_punctuations[i][phonemeses_list_index]}")
                                                    print(phoneme)
                                            phoneme[2] = extracted_punctuations[i][phonemeses_list_index]
                                            phonemes.append(phoneme)
                                            phonemeses_list_index += 1
                                            if not is_last_punctuation:
                                                is_last_punctuation = phonemeses_list_index == (len(extracted_punctuations[i]) - 1)
                                                next_punctuation_insert_index += len(phonemeses_list[phonemeses_list_index]) + 1    # +1 for the pause
                                        else:
                                            phonemes.append(phoneme)
                                    else:
                                        phonemes.append(phoneme)
                            # save phonemes_aligned
                            with open(os.path.splitext(k)[0] + '.phonemes_aligned.txt', 'w') as f:
                                f.write('\n'.join('\t'.join(p) for p in phonemes))
                            # with open(os.path.splitext(need_transcription_files[i])[0] + '.phonemes_aligned.txt', 'w') as f:
                            #     f.write('\n'.join('\t'.join(p) for p in phonemes))
                                
                            
                            phonemeses[k] = '\n'.join('\t'.join(p) for p in phonemes)
                    else:
                        # phonemeses = [g2p(transcribed_text["text"]) for transcribed_text in tqdm(transcribed_texts, desc='g2p')]
                        # phonemeses = {k: g2p(text) for k, text in tqdm(all_texts.items(), desc='g2p')}
                        should_be_phonemized = [k for k in all_texts.keys() if k not in phonemeses.keys()]
                        added_phonemeses = {k: g2p(text) for (k, text) in tqdm([(j, all_texts[j]) for j in should_be_phonemized], desc='g2p')}
                        phonemeses.update(added_phonemeses)
                        # phonemeses = [g2p(transcribed_text["text"]) for transcribed_text in tqdm(transcribed_texts, desc='g2p')]
                        # save phonemes
                        for k, p in added_phonemeses.items():
                            with open(os.path.splitext(k)[0] + '.phonemes.txt', 'w') as f:
                                f.write(p)
                        # align
                        empty_phoneme_keys = []
                        for k, p in tqdm(phonemeses.items(), desc='align'):
                            if p == 'pau  pau' or p == '':
                                # no phonemes, skip
                                empty_phoneme_keys.append(k)
                                # p = 'pau'
                                continue
                            phonemes, g2p_model = aligner(p, k, g2p_model, model_path=args.g2p_model_path)
                            phonemeses[k] = phonemes
                        # remove empty phonemes
                        for k in empty_phoneme_keys:
                            del phonemeses[k]
                        # phonemes, g2p_model = aligner(phonemes, file_path, g2p_model, model_path=args.g2p_model_path)
                        # phonemes, g2p_model = g2p(transcribed_text, file_path, g2p_model, model_path=args.g2p_model_path)
                # save aligned phonemes
                # for i in range(len(need_alignment_files)):
                for k, text in all_texts.items():
                    if k not in phonemeses:
                        continue
                    with open(os.path.splitext(k)[0] + '.lab', 'w') as f:
                        f.write(phonemeses[k])
                # with open(os.path.splitext(file_path)[0] + '.lab', 'w') as f:
                #     f.write(phonemes)
            if wav_exists == True and args.g2p_alignment_type == 'openjtalk+SOFA':
                # align phonemes by SOFA
                cmd = f"python {sofa_infer_script} --ckpt {args.sofa_model_path} --folder {root} --dictionary {args.sofa_dict_path} --out_formats htk"
                os.system(cmd)
                # copy alined phonemes to lab file
                for file in os.listdir(os.path.join(root, 'htk', 'phones')):
                    if file.endswith('.lab'):
                        # os.rename(os.path.join(root, file), os.path.join(root, os.path.splitext(file)[0] + '.lab'))
                        shutil.copy(os.path.join(root, 'htk', 'phones', file), os.path.join(root, os.path.splitext(file)[0] + '.lab'))
                                
    for folder_name in os.listdir(root_path):
        folder_path = os.path.join(root_path, folder_name)
        print(f"Processing folder: {folder_path}")
        if os.path.isdir(folder_path):
            make_lab_into_dir(folder_path)


def process_data(args, all_shits, all_shits_not_wav_n_lab):
    if args.data_type == "lab_wav":
        db_converter_script = "./nnsvs-db-converter/db_converter.py"
        for folder_name in os.listdir(all_shits_not_wav_n_lab):
            folder_path = os.path.join(all_shits_not_wav_n_lab, folder_name)
            if os.path.isdir(folder_path):
                # Convert to DS format
                cmd = f"python {db_converter_script} -s {args.max_silence_phoneme} -l {args.segment_length} -D"
                if args.estimate_midi != "False":
                    cmd += " -m -c"
                cmd += f' -L "./nnsvs-db-converter/lang.sample.json" {folder_path}'
                os.system(cmd)
                
                # load transcriptions.csv
                csv_path = os.path.join(folder_path, "transcriptions.csv")
                if os.path.exists(csv_path):
                    # read with csv
                    with open(csv_path, 'r') as f:
                        reader = csv.reader(f)
                        rows = list(reader)
                    full_rest_files = [row[0] for row in rows[1:] if all(col == "rest" for col in row[4].split(" "))]
                    if len(full_rest_files) > 0:
                        print(f"Removing full rest files from list: {full_rest_files}")
                        # remove row with full of rest notes
                        rows = [rows[0]] + [row for row in rows[1:] if any(col != "rest" for col in row[4].split(" "))]
                        # write to csv
                        with open(csv_path, 'w', newline='') as f:
                            writer = csv.writer(f)
                            writer.writerows(rows)
                
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
    if args.no_cleanup:
        all_shits, all_shits_not_wav_n_lab = setup_directories(no_cleanup=True)
    else:
        all_shits, all_shits_not_wav_n_lab = setup_directories()
    
    # Extract archive
    extract_archive(args.data_zip_path, all_shits_not_wav_n_lab)
    
    # Make lab files
    make_lab_files(args, all_shits_not_wav_n_lab)
    
    if args.data_type != "lab_wav":
        process_lab_files(all_shits)
    
    # Generate phoneme dictionary and related files
    phonemes = collect_phonemes(args.data_type, all_shits if args.data_type == "lab_wav" else all_shits_not_wav_n_lab)
    
    # TODO: support merge same language files
    vowels, liquids, consonants = generate_phoneme_files(phonemes, "./DiffSinger/dictionaries/custom_dict.txt")
    
    # Generate language JSON
    liquid_list = {liquid: True for liquid in liquids}
    phones4json = {"vowels": vowels, "liquids": liquid_list}
    with open("./nnsvs-db-converter/lang.sample.json", "w") as f:
        json.dump(phones4json, f, indent=4)
    
    global transcription_model
    transcription_model = None
    # Process data based on type
    process_data(args, all_shits, all_shits_not_wav_n_lab)
    
    # Fix initial SP in CSV files
    fix_initial_sp(all_shits_not_wav_n_lab)
    
    print("Extraction complete!")
    print("Dictionary and data conversion completed successfully.")

if __name__ == "__main__":
    main()