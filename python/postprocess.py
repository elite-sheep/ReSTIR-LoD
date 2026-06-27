# Copyright @yucwang 2025

import argparse
import os
import glob
import numpy as np
import pyexr
from PIL import Image
import subprocess
import tqdm


def tonemap(hdr, gamma=2.2):
    """Simple Reinhard tonemapping + gamma correction."""
    ldr = hdr / (1.0 + hdr)
    ldr = np.clip(ldr, 0.0, 1.0)
    ldr = np.power(ldr, 1.0 / gamma)
    return (ldr * 255).astype(np.uint8)


def exr_to_png(input_dir, output_dir=None):
    """Convert all EXR files in input_dir to PNG."""
    if output_dir is None:
        output_dir = input_dir

    os.makedirs(output_dir, exist_ok=True)

    exr_files = sorted(glob.glob(os.path.join(input_dir, '*.exr')))
    if not exr_files:
        print(f'No EXR files found in {input_dir}')
        return

    print(f'Converting {len(exr_files)} EXR files to PNG...')
    for exr_path in tqdm.tqdm(exr_files):
        hdr = pyexr.read(exr_path)
        hdr = np.nan_to_num(hdr, nan=0.0)
        ldr = tonemap(hdr[:, :, :3])

        basename = os.path.splitext(os.path.basename(exr_path))[0]
        png_path = os.path.join(output_dir, f'{basename}.png')
        Image.fromarray(ldr).save(png_path)

    print(f'Saved PNGs to {output_dir}')


def make_video(input_dir, output_path=None, fps=30):
    """Create a video from PNG files using ffmpeg."""
    if output_path is None:
        output_path = os.path.join(input_dir, 'video.mp4')

    input_pattern = os.path.join(input_dir, 'img_%d.png')

    cmd = [
        'ffmpeg', '-y',
        '-framerate', str(fps),
        '-i', input_pattern,
        '-c:v', 'libx264',
        '-pix_fmt', 'yuv420p',
        '-crf', '18',
        output_path
    ]

    print(f'Creating video at {output_path} ({fps} FPS)...')
    subprocess.run(cmd, check=True)
    print(f'Video saved to {output_path}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Post-process EXR renders to PNG and video')
    subparsers = parser.add_subparsers()

    # exr2png
    p_convert = subparsers.add_parser('exr2png', help='Convert EXR files to PNG')
    p_convert.add_argument('input_dir', type=str, help='Directory containing EXR files')
    p_convert.add_argument('--output_dir', type=str, default=None, help='Output directory (default: same as input)')
    p_convert.set_defaults(func=lambda args: exr_to_png(args.input_dir, args.output_dir))

    # video
    p_video = subparsers.add_parser('video', help='Create video from PNG files')
    p_video.add_argument('input_dir', type=str, help='Directory containing PNG files')
    p_video.add_argument('--output', type=str, default=None, help='Output video path')
    p_video.add_argument('--fps', type=int, default=30, help='Frames per second (default: 30)')
    p_video.set_defaults(func=lambda args: make_video(args.input_dir, args.output, args.fps))

    # all: exr2png + video in one step
    p_all = subparsers.add_parser('all', help='Convert EXR to PNG and create video')
    p_all.add_argument('input_dir', type=str, help='Directory containing EXR files')
    p_all.add_argument('--output', type=str, default=None, help='Output video path')
    p_all.add_argument('--fps', type=int, default=30, help='Frames per second (default: 30)')

    def run_all(args):
        exr_to_png(args.input_dir)
        make_video(args.input_dir, args.output, args.fps)

    p_all.set_defaults(func=run_all)

    args = parser.parse_args()
    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help()
