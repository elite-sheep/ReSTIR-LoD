# Copyright @yucwang 2025

import argparse
from config import RenderConfig
import os
import common
import falcor
import numpy as np
import pyexr
import time
import tqdm
import random
import yaml

def render(base_dir, config: RenderConfig):
    reso = config.resolution
    output_dir = os.path.join(base_dir, config.output_dir)
    os.makedirs(output_dir, exist_ok=True)

    testbed = common.create_testbed(reso)

    scene = common.load_scene(testbed, config.scene_path, reso[0] / reso[1])
    passes = common.create_render_pass(testbed, config, random.randint(0, 65536))

    camera = scene.camera

    # warm up
    for i in tqdm.tqdm(range(16)):
        testbed.frame()

    # Enable clock for door animation at 30 FPS
    clock = testbed.clock
    clock.framerate = 30
    clock.play()

    total_rendering_time = 0.0
    for i in tqdm.tqdm(range(config.num_iters)):
        img = None
        for _ in range(config.num_images):
            st = time.perf_counter()
            testbed.frame()
            en = time.perf_counter()
            total_rendering_time += (en - st)
            if img is None:
                img = testbed.render_graph.get_output("ReservoirSplatting.color").to_numpy()[:,:,:3]
            else:
                img += testbed.render_graph.get_output("ReservoirSplatting.color").to_numpy()[:,:,:3]
        img = np.nan_to_num(img, nan=0.0)
        pyexr.write(os.path.join(output_dir, f"img_{i}.exr"), img / config.num_images)
    print(f'FPS: {config.num_iters / total_rendering_time} frames per second')

def render_with_args(base_dir, args):
    config_file = args.config_file
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
        render_config = RenderConfig(
            scene_path=config['scene_path'],
            max_bounces=config.get('max_bounces', 6),
            enable_temporal=config.get('enable_temporal', True),
            enable_spatial=config.get('enable_spatial', True),
            temporal_reuse_option=config['temporal_reuse_option'],
            output_dir=config['output_dir'],
            resolution=config['resolution'],
            num_iters=config['num_iters'],
            num_images=config.get('num_images', 1)
        )
        render(base_dir, render_config)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='VeachAjar animated rendering')
    parser.add_argument('--verbose', action='store_true', help='Verbose')
    subparsers = parser.add_subparsers()

    parser_render = subparsers.add_parser('render', help='Render images')
    parser_render.add_argument('--config_file', type=str, help='Path to the config file')
    parser_render.set_defaults(func=render_with_args)

    args = parser.parse_args()

    if hasattr(args, 'func'):
        args.func(os.path.dirname(args.config_file), args)
    else:
        parser.print_help()
