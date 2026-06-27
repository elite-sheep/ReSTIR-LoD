# Copyright @yucwang 2025

import argparse
from config import RenderConfig
import os
import common
import falcor
import numpy as np
import pyexr
import tqdm
import random
import yaml
import matplotlib.pyplot as plt

def render(base_dir, config: RenderConfig):
    reso = config.resolution
    output_dir = os.path.join(base_dir, config.output_dir)
    os.makedirs(output_dir, exist_ok=True)

    testbed = common.create_testbed(reso)

    img = np.zeros(shape=(reso[1], reso[0], 3))
    scene = common.load_scene(testbed, config.scene_path, reso[0] / reso[1])
    passes = common.create_render_pass(testbed, config, random.randint(0, 65536))

    # warm up
    for i in tqdm.tqdm(range(16)):
        testbed.frame()

    clock = testbed.clock
    clock.play()
    for i in tqdm.tqdm(range(config.num_iters)):
        testbed.frame()
        img = testbed.render_graph.get_output("ReservoirSplatting.color").to_numpy()[:,:,:3]
    pyexr.write(os.path.join(output_dir, f"img_final.exr"), img)

    # print(scene.stats)

    # scene.raise_lod_level("PotLid")
    # scene.raise_lod_level("Pot")
    # img = np.zeros(shape=(reso[1], reso[0], 3))
    # for _ in tqdm.tqdm(range(config.num_iters)):
    #     testbed.frame()
    #     img = img + testbed.render_graph.get_output("ReservoirSplatting.color").to_numpy()[:,:,:3]
    # pyexr.write(os.path.join(output_dir, "img2.exr"), img / config.num_iters)

def render_with_args(base_dir, args):
    config_file = args.config_file
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
        render_config = RenderConfig(
            scene_path=config['scene_path'],
            max_bounces=config.get('max_bounces', 4),
            enable_temporal=config.get('enable_temporal', True),
            enable_spatial=config.get('enable_spatial', True),
            temporal_reuse_option=config['temporal_reuse_option'],
            output_dir=config['output_dir'],
            resolution=config['resolution'],
            num_iters=config['num_iters']
        )

        render(base_dir, render_config)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Gradient-PT rendering experiments')
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
