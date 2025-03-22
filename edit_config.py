#!/usr/bin/env python3
import re
import os
import shutil
import yaml
import random
import argparse
from pathlib import Path

def parse_args():
    parser = argparse.ArgumentParser(description='DiffSinger configuration editor')
    parser.add_argument('--model-type', choices=['acoustic', 'variance'], default='acoustic', help='Model type to train')
    parser.add_argument('--diffusion-type', choices=['ddpm', 'reflow'], default='reflow', help='Diffusion type')
    parser.add_argument('--diff-accelerator', choices=['ddim', 'pndm', 'dpm-solver', 'unipc'], default='ddim', help='Diffusion accelerator')
    parser.add_argument('--loss-type', choices=['l1', 'l2'], default='l2', help='Loss type')
    parser.add_argument('--data-dir', required=True, help='Directory containing raw data')
    parser.add_argument('--use-shallow-diffusion', choices=['false', 'true_aux_val', 'true_gt_val'], default='true_gt_val', help='Shallow diffusion training mode')
    parser.add_argument('--precision', choices=['32-true', 'bf16-mixed', '16-mixed', 'bf16', '16'], default='16-mixed', help='Training precision')
    parser.add_argument('--save-dir', required=True, help='Model save directory')
    parser.add_argument('--enable-finetuning', action='store_true', help='Enable finetuning')
    parser.add_argument('--base-model-path', help='Path to custom base model')
    parser.add_argument('--selected-param', choices=['energy_breathiness', 'tension', 'voicing', 'none'], default='tension', help='Model embeds selection')
    parser.add_argument('--parameter-extraction', choices=['vr', 'world'], default='vr', help='Parameter extraction method')
    parser.add_argument('--pitch-training', choices=['false', 'standard', 'melody_encoder'], default='false', help='Pitch training mode')
    parser.add_argument('--f0-extractor', choices=['parselmouth', 'rmvpe', 'harvest'], default='parselmouth', help='F0 extractor algorithm')
    parser.add_argument('--sampling-algorithm', choices=['euler', 'rk2', 'rk4', 'rk5'], default='euler', help='Sampling algorithm')
    parser.add_argument('--acoustic-hidden-size', type=int, default=256, help='Acoustic hidden size')
    parser.add_argument('--acoustic-num-layers', type=int, default=6, help='Acoustic number of layers')
    parser.add_argument('--acoustic-num-channels', type=int, default=1024, help='Acoustic number of channels')
    parser.add_argument('--variance-hidden-size', type=int, default=256, help='Variance hidden size')
    parser.add_argument('--duration-hidden-size', type=int, default=512, help='Duration hidden size')
    parser.add_argument('--melody-encoder-hidden-size', type=int, default=128, help='Melody encoder hidden size')
    parser.add_argument('--pitch-num-layers', type=int, default=6, help='Pitch number of layers')
    parser.add_argument('--pitch-num-channels', type=int, default=512, help='Pitch number of channels')
    parser.add_argument('--variance-num-layers', type=int, default=6, help='Variance number of layers')
    parser.add_argument('--variance-num-channels', type=int, default=384, help='Variance number of channels')
    return parser.parse_args()

def get_speaker_info(data_dir):
    spk_names = [folder_name for folder_name in os.listdir(data_dir) if os.path.isdir(os.path.join(data_dir, folder_name))]
    num_spk = len(spk_names)
    raw_dir = [os.path.join(data_dir, folder_name) for folder_name in spk_names]
    return spk_names, num_spk, raw_dir

def get_test_files(num_spk, raw_dir, data_dir, model_type):
    if num_spk == 1:
        singer_type = "SINGLE-SPEAKER"
        use_spk_id = False
        all_wav_files = []
        for root, _, files in os.walk(data_dir):
            for file in files:
                if file.endswith((".wav", ".ds")):
                    all_wav_files.append(os.path.join(root, file))
        random.shuffle(all_wav_files)
        random_test_files = [os.path.splitext(os.path.basename(file))[0] for file in all_wav_files[:3]]
    else:
        singer_type = "MULTI-SPEAKER"
        use_spk_id = True
        folder_to_id = {os.path.basename(folder): i for i, folder in enumerate(raw_dir)}
        random_test_files = []
        for folder_in_raw_dir in raw_dir:
            folder_name =  os.path.basename(folder_in_raw_dir)
            all_wav_files = []
            for root, _, files in os.walk(folder_in_raw_dir):
                for file in files:
                    if file.endswith(".ds"):
                        folder_id = folder_to_id.get(folder_name, -1)
                        all_wav_files.append(os.path.join(root, file))
            random.shuffle(all_wav_files)
            random_test_files.extend([f"{folder_id}:{os.path.splitext(os.path.basename(file))[0]}" for file in all_wav_files[:1]])
        # random_test_files = [os.path.splitext(os.path.basename(file))[0] for file in all_wav_files[:3]]
    return singer_type, use_spk_id, random_test_files

def main():
    args = parse_args()
    
    spk_names, num_spk, raw_dir = get_speaker_info(args.data_dir)
    print(f"Number of speakers: {num_spk}", raw_dir)
    singer_type, use_spk_id, random_test_files = get_test_files(num_spk, raw_dir, args.data_dir, args.model_type)
    
    binary_save_dir = os.path.join(args.save_dir, "binary")
    os.makedirs(args.save_dir, exist_ok=True)
    
    # Copy configs from `configs` to `../configs`
    shutil.copytree("configs", "../configs", dirs_exist_ok=True)

    # Update base config
    with open("../configs/base.yaml", "r") as config:
        base_config = yaml.safe_load(config)
    base_config["pl_trainer_precision"] = args.precision
    with open("../configs/base.yaml", "w") as config:
        yaml.dump(base_config, config)

    # Load and update model specific config
    config_path = f"../configs/{args.model_type}.yaml"
    with open(config_path, "r") as config:
        model_config = yaml.safe_load(config)
        
    data_aug = True # forcing data augmentation on TODO: make it a parameter if can good learning with data augmentation
    # data_aug = False if args.model_type == "acoustic_vocoder" else True
    
    if args.use_shallow_diffusion == "false":
        use_shallow = False
        gt_shallow = False
    elif args.use_shallow_diffusion == "true_aux_val":
        use_shallow = True
        gt_shallow = False
    else:
        use_shallow = True
        gt_shallow = True
        
    if args.enable_finetuning:
        pretrain = True
        if args.base_model_path is not None:
            pretrain_ckpt = args.base_model_path
        else:
            pretrain_ckpt = f"pretrain_models/{args.model_type}_pretrain.ckpt"
        finetune_strict_shapes = False
        finetune_ckpt_path = pretrain_ckpt
    else:
        pretrain = False
        finetune_strict_shapes = True
        finetune_ckpt_path = None
    
    if args.selected_param == "energy_breathiness":
        tension_training = False
        energy_training = True
        breathiness_training = True
        voicing_training = True
    elif args.selected_param == "tension":
        tension_training = True
        energy_training = False
        breathiness_training = False
        voicing_training = False
    elif args.selected_param == "voicing":
        tension_training = False
        energy_training = False
        breathiness_training = False
        voicing_training = True
    else:
        tension_training = False
        energy_training = False
        breathiness_training = False
        voicing_training = False
        
    parameter_extraction_method = args.parameter_extraction
    
    if args.pitch_training == "false":
        pitch_training = False
        use_melody_encoder = False
        use_glide_embed = False
    elif args.pitch_training == "standard":
        pitch_training = True
        use_melody_encoder = False
        use_glide_embed = False
    else:
        pitch_training = True
        use_melody_encoder = True
        use_glide_embed = False
        
    duration_training = True

    # Update common configurations
    model_config.update({
        "speakers": spk_names,
        "test_prefixes": random_test_files,
        "raw_data_dir": raw_dir,
        "num_spk": num_spk,
        "use_spk_id": use_spk_id,
        "diffusion_type": args.diffusion_type,
        "diff_accelerator": args.diff_accelerator,
        "main_loss_type": args.loss_type,
        "binary_data_dir": binary_save_dir,
        "dictionary": "dictionaries/custom_dict.txt",
        "pe": args.f0_extractor,
        "pe_ckpt": "checkpoints/rmvpe/model.pt" if args.f0_extractor == "rmvpe" else None,
        "finetune_enabled": args.enable_finetuning,
        "finetune_ckpt_path": finetune_ckpt_path,
        "finetune_strict_shapes": finetune_strict_shapes,
        "hnsep": parameter_extraction_method,
        "hnsep_ckpt": "checkpoints/vr/model.pt",
        "sampling_algorithm": args.sampling_algorithm,
        "hidden_size": args.acoustic_hidden_size,
        "backbone_type": "lynxnet",
        "pl_trainer_precision": args.precision,
    })
    
    prefer_ds = False   # TODO: set true if you use ds (DiffSinger format)
    
    if args.model_type.startswith("acoustic"):
        model_config.update({
            "use_key_shift_embed": data_aug,
            "use_speed_embed": data_aug,
            "use_energy_embed": energy_training,
            "use_breathiness_embed": breathiness_training,
            "use_tension_embed": tension_training,
            "use_voicing_embed": voicing_training,
            "use_shallow_diffusion": use_shallow,
        })
        model_config["backbone_args"].update({
            "num_layers": args.acoustic_num_layers,
            "num_channels": args.acoustic_num_channels,
        })
        model_config["augmentation_args"]["random_pitch_shifting"].update({
            "enabled": data_aug
        })
        model_config["augmentation_args"]["random_time_stretching"].update({
            "enabled": data_aug
        })
        if "shallow_diffusion_args" in model_config.keys():
            model_config["shallow_diffusion_args"].update({
                "val_gt_start": data_aug
            })
    else:
        model_config.update({
            "predict_energy": energy_training,
            "predict_breathiness": breathiness_training,
            "predict_tension": tension_training,
            "predict_pitch": pitch_training,
            "predict_voicing": voicing_training,
            "use_melody_encoder": use_melody_encoder,
            "use_glide_embed": use_glide_embed,
            "predict_dur": duration_training,
            "hidden_size": args.variance_hidden_size,
        })
        model_config["binarization_args"].update({
            "prefer_ds": prefer_ds,
        })
        model_config["dur_prediction_args"].update({
            "hidden_size": args.duration_hidden_size,
        })
        model_config["melody_encoder_args"].update({
            "hidden_size": args.melody_encoder_hidden_size,
        })
        model_config["variances_prediction_args"]["backbone_type"] = "lynxnet"
        model_config["variances_prediction_args"]["backbone_args"].update({
            "num_layers": args.variance_num_layers,
            "num_channels": args.variance_num_channels,
        })
        model_config["pitch_prediction_args"]["backbone_type"] = "lynxnet"
        model_config["pitch_prediction_args"]["backbone_args"].update({
            "num_layers": args.pitch_num_layers,
            "num_channels": args.pitch_num_channels,
        })

    # Write updated config
    with open(config_path, "w") as config:
        yaml.dump(model_config, config)

    # Update hparams.py
    with open("utils/hparams.py", "r") as f:
        hparams = f.read()
    hparams = re.sub(r"args_work_dir\s*=\s*.*", f"args_work_dir = '{args.save_dir}'", hparams)
    with open("utils/hparams.py", "w") as f:
        f.write(hparams)

    print(f"Configuration updated successfully for {args.model_type.upper()} {singer_type} training")
    print(f"Save directory: {args.save_dir}")
    print(f"Test files: {random_test_files}")

if __name__ == "__main__":
    main()
