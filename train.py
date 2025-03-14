import argparse
import re
import os
import shutil
import yaml
from pathlib import Path
from tensorboard import program

def main():
    parser = argparse.ArgumentParser(description='Train DiffSinger model')
    parser.add_argument('--save_interval', type=int, default=2000, help='Step interval for validation and saving')
    parser.add_argument('--batch_size', type=int, default=9, help='Batch size for training')
    parser.add_argument('--max_updates', type=int, default=160000, help='Maximum training steps')
    parser.add_argument('--resume_training', action='store_true', help='Resume training from checkpoint')
    parser.add_argument('--local_data', action='store_true', help='Use locally binarized data')
    parser.add_argument('--re_config_path', type=str, default='', help='Path to existing config for resume training')
    parser.add_argument('--training_config', type=str, default='content/DiffSinger/configs/acoustic.yaml', help='Path to training config file')
    parser.add_argument('--save_dir', type=str, default='', help="Path to model save path")
    
    args = parser.parse_args()

    if args.resume_training:
        model_dir = os.path.dirname(args.re_config_path)
        save_dir = model_dir
        
        # Update hparams.py
        with open("utils/hparams.py", "r") as f:
            hparams_py_read = f.read()
        hparams_py_read = re.sub(r"args_work_dir\s*=\s*.*", f"args_work_dir = '{save_dir}'", hparams_py_read)
        with open("utils/hparams.py", "w") as f:
            f.write(hparams_py_read)
        
        # # Update training_utils.py
        # with open("utils/training_utils.py", "r") as f:
        #     training_utils_stuff = f.read()
        # training_utils_stuff = re.sub("relative_path\s*=\s*.*", 
        #                             "relative_path = filepath.relative_to(Path('content').resolve())", 
        #                             training_utils_stuff)
        # with open("utils/training_utils.py", "w") as f:
        #     f.write(training_utils_stuff)

        config_path = args.re_config_path
        log_dir = save_dir

        # Copy dictionary
        shutil.copy2(os.path.join(model_dir, 'dictionary.txt'), 'dictionaries/custom_dict.txt')
    else:
        save_dir = args.save_dir
        config_path = args.training_config
        log_dir = save_dir

    # Update config
    with open(config_path, "r") as config:
        config_data = yaml.safe_load(config)
    
    config_dir = os.path.dirname(config_path)
    binary_dir = os.path.join(config_dir, "binary")

    config_data["val_check_interval"] = args.save_interval
    config_data["max_batch_size"] = args.batch_size
    config_data["max_updates"] = args.max_updates
    
    if args.local_data:
        config_data["binary_data_dir"] = binary_dir
    
    with open(config_path, "w") as config:
        yaml.dump(config_data, config)

    # Launch tensorboard
    tb = program.TensorBoard()
    tb.configure(argv=[None, '--logdir', f'{log_dir}/lightning_logs'])
    url = tb.launch()
    print(f"TensorBoard started at {url}")

    # Start training
    os.system(f"python scripts/train.py --config {config_path} --exp_name {save_dir} --reset")

if __name__ == "__main__":
    main()