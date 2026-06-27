# Copyright @yucwang 2025

import os

class RenderConfig:
    scene_path: str
    max_bounces: int = 2
    enable_temporal: bool = True
    enable_spatial: bool = True
    temporal_reuse_option: str
    resolution: tuple = (1920, 1080)
    num_iters: int = 32
    num_images: int = 1
    output_dir: str

    def __init__(self,
                 scene_path: str,
                 max_bounces: int,
                 enable_temporal: bool,
                 enable_spatial: bool,
                 temporal_reuse_option: str,
                 resolution: tuple,
                 num_iters: int,
                 num_images: int,
                 output_dir: str):
        self.scene_path = scene_path
        self.max_bounces = max_bounces
        self.enable_temporal = enable_temporal
        self.enable_spatial = enable_spatial
        self.temporal_reuse_option = temporal_reuse_option
        self.resolution = resolution
        self.num_iters = num_iters
        self.num_images = num_images
        self.output_dir = output_dir
