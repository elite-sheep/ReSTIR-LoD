# Copyright @yucwang 2025

import argparse
from config import RenderConfig
import os
import common
import numpy as np
import pyexr
import time
import tqdm
import random
import yaml
from typing import List

from lod_utils import *

max_lod_level = 4

def determine_lod_by_coc(coc):
    if coc < 0.45:
        return 0
    elif coc < 0.5:
        return 1
    elif coc < 0.9:
        return 2
    else:
        return 3

def determine_lod_level(camera, lod_bounds):
    f = camera.focalLength / 125.0
    a = camera.apertureRadius * 2.0
    s = camera.focalDistance
    K_sensor = a * f / (s - f)

    z = min_distance_to_bound(camera.position, lod_bounds)
    coc = K_sensor * (abs(z - s)) / z
    coc = coc * 1000.0
    print(f'K_sensor: {K_sensor}, coc: {coc}, z: {z}')
    lod_level_coc = determine_lod_by_coc(coc)

    return lod_level_coc

class Animation:
    focal_distances: List[float]
    steps: List[float]
    start_focal_distance = 0.0

    def __init__(self):
        self.focal_distances = []
        self.steps = []

    def get(self, i_frame: int) -> float:
        if i_frame > self.steps[-1]:
            return 0.0
        for i in range(len(self.steps)):
            if i_frame < self.steps[i]:
                next_focal_distance = self.focal_distances[i]
                prev_focal_distance = self.focal_distances[i - 1] if i > 0 else self.start_focal_distance
                prev_key_frame = self.steps[i - 1] if i > 0 else 0
                return (next_focal_distance - prev_focal_distance) / (self.steps[i] - prev_key_frame)

        return 0.0

    def add_key_frame(self, focal_distance: float, step: int):
        self.focal_distances.append(focal_distance)
        self.steps.append(step)

def render(base_dir, config: RenderConfig):
    lod_names = [ 'GoldKing' ]

    reso = config.resolution
    output_dir = os.path.join(base_dir, config.output_dir)
    os.makedirs(output_dir, exist_ok=True)

    testbed = common.create_testbed(reso)

    img = None
    scene = common.load_scene(testbed, config.scene_path, reso[0] / reso[1])
    passes = common.create_render_pass(testbed, config, random.randint(0, 65536))

    # preprocess LoD
    camera = scene.camera
    lod_levels = {}
    for lod_name in lod_names:
        lod_bounds = get_lod_mesh_bounds(scene, lod_name)
        lod_level = determine_lod_level(camera, lod_bounds)
        lod_levels[lod_name] = lod_level
        scene.set_lod_level(lod_name, lod_level)
        print(f'LoD {lod_name} bounds: {lod_bounds.center}, level: {lod_level}')

    # Enable clock for scene animation (GoldKing translation at 30 FPS)
    clock = testbed.clock
    clock.framerate = 30
    clock.play()

    # warm up
    for i in tqdm.tqdm(range(16)):
        testbed.frame()

    animation = Animation()
    animation.start_focal_distance = camera.focalDistance
    animation.add_key_frame(2.4, 32)
    animation.add_key_frame(1.0, 64)
    animation.add_key_frame(2.5, 96)
    animation.add_key_frame(1.75, 128)
    animation.add_key_frame(1.81, 150)
    animation.add_key_frame(1.79, 159)
    animation.add_key_frame(1.81, 165)

    total_rendering_time = 0.0
    animation_paused = False
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

        camera.focalDistance = camera.focalDistance + animation.get(i)
        print(f'camera focalDistance: {camera.focalDistance}')

        lod_changed = False
        for lod_name in lod_names:
            lod_bounds = get_lod_mesh_bounds(scene, lod_name)
            lod_level = determine_lod_level(camera, lod_bounds)
            if lod_level < lod_levels[lod_name]:
                clock.pause()
                lod_changed = True
                animation_paused = True
                scene.lower_lod_level(lod_name)
                lod_levels[lod_name] -= 1
                print(f'Lowered LoD {lod_name} to level {lod_levels[lod_name]}, pausing animation')
            elif lod_level > lod_levels[lod_name]:
                clock.pause()
                lod_changed = True
                animation_paused = True
                scene.raise_lod_level(lod_name)
                lod_levels[lod_name] += 1
                print(f'Raised LoD {lod_name} to level {lod_levels[lod_name]}, pausing animation')
        if not lod_changed and animation_paused:
            clock.play()
            animation_paused = False
            print('Resuming animation')
    print(f'FPS: {config.num_iters / total_rendering_time} frames per second')

def render_gt(base_dir, config: RenderConfig):
    lod_names = [ 'GoldKing' ]

    reso = config.resolution
    output_dir = os.path.join(base_dir, config.output_dir)
    os.makedirs(output_dir, exist_ok=True)

    testbed = common.create_testbed(reso)

    img = None
    scene = common.load_scene(testbed, config.scene_path, reso[0] / reso[1])
    passes = common.create_render_pass(testbed, config, random.randint(0, 65536))

    # preprocess LoD
    camera = scene.camera
    lod_levels = {}
    for lod_name in lod_names:
        lod_bounds = get_lod_mesh_bounds(scene, lod_name)
        lod_level = determine_lod_level(camera, lod_bounds)
        lod_levels[lod_name] = lod_level
        scene.set_lod_level(lod_name, lod_level)
        print(f'LoD {lod_name} bounds: {lod_bounds.center}, level: {lod_level}')

    animation = Animation()
    animation.start_focal_distance = camera.focalDistance
    animation.add_key_frame(2.4, 32)
    animation.add_key_frame(1.0, 64)
    animation.add_key_frame(2.5, 96)
    animation.add_key_frame(1.75, 128)
    animation.add_key_frame(1.81, 150)
    animation.add_key_frame(1.79, 159)
    animation.add_key_frame(1.81, 165)

    # Enable clock for scene animation (GoldKing translation at 30 FPS)
    clock = testbed.clock
    clock.framerate = 30
    clock.play()

    for i in tqdm.tqdm(range(163)):
        testbed.frame()
        camera.focalDistance = camera.focalDistance + animation.get(i)

        for lod_name in lod_names:
            lod_bounds = get_lod_mesh_bounds(scene, lod_name)
            lod_level = determine_lod_level(camera, lod_bounds)
            if lod_level < lod_levels[lod_name]:
                scene.lower_lod_level(lod_name)
                lod_levels[lod_name] -= 1
                print(f'Lowered LoD {lod_name} to level {lod_levels[lod_name]}')
            elif lod_level > lod_levels[lod_name]:
                scene.raise_lod_level(lod_name)
                lod_levels[lod_name] += 1
                print(f'Raised LoD {lod_name} to level {lod_levels[lod_name]}')

    final_img = None
    n_spp = 8192
    for i in tqdm.tqdm(range(n_spp)):
        testbed.frame()
        image = testbed.render_graph.get_output("ReservoirSplatting.color").to_numpy()[:,:,:3]
        if final_img is None:
            final_img = image / n_spp
        else:
            final_img = final_img + image / n_spp
    pyexr.write(os.path.join(output_dir, f"gt.exr"), final_img)

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
            num_iters=config['num_iters'],
            num_images=config.get('num_images', 1)
        )

        render(base_dir, render_config)

def gt_with_args(base_dir, args):
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
            num_iters=config['num_iters'],
            num_images=config.get('num_images', 1)
        )

        render_gt(base_dir, render_config)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Chessboard animated rendering experiments')
    parser.add_argument('--verbose', action='store_true', help='Verbose')
    subparsers = parser.add_subparsers()

    parser_render = subparsers.add_parser('render', help='Render images')
    parser_render.add_argument('--config_file', type=str, help='Path to the config file')
    parser_render.set_defaults(func=render_with_args)

    parser_gt = subparsers.add_parser('gt', help='Render ground truth images')
    parser_gt.add_argument('--config_file', type=str, help='Path to the config file')
    parser_gt.set_defaults(func=gt_with_args)

    args = parser.parse_args()

    if hasattr(args, 'func'):
        args.func(os.path.dirname(args.config_file), args)
    else:
        parser.print_help()
