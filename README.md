# ReSTIR LoD

![](teaser.png)

This repository contains the implementation of *"Real-Time Level-of-Detail Rendering with ReSTIR"* by Yu-Chen Wang, Markus Kettunen, Daqi Lin, Chris Wyman, Lifan Wu, and Shuang Zhao. Built on NVIDIA's [Falcor 8.0](https://github.com/NVIDIAGameWorks/Falcor) framework and the [Reservoir Splatting](README_falcor.md) codebase, our method couples ReSTIR temporal path resampling with dynamic level-of-detail (LoD) selection, allocating geometric detail where it matters while keeping temporal reuse stable across LoD transitions.

## Major changes

The ReSTIR LoD algorithm is implemented in the `Source/RenderPasses/ReservoirSplatting/` render pass. Relative to the base Reservoir Splatting codebase, the core changes live in two shader files:

- `ShiftMapping.slang` — adds an LoD-aware reconnection shift (`geometricLoDShift`) that re-maps the reconnection vertex through texture UVs when an object's LoD level changes between frames, keeping the shift valid across LoD transitions.
- `ScatterTemporalResampling.cs.slang` — performs scatter-based temporal reuse across LoD transitions, splatting reservoirs from the prior frame onto the current frame's geometry.

### Python driver scripts

The `python/` directory holds the headless experiment infrastructure that drives the render pass through Falcor's Python bindings (`falcor.Testbed`). It is organized into shared modules and per-scene render scripts.

Shared modules:

- `config.py` — the `RenderConfig` dataclass capturing all run parameters (scene path, bounce count, temporal/spatial flags, temporal-reuse option, resolution, iteration/sample counts, output directory).
- `common.py` — headless setup helpers: `create_testbed()` builds a windowless Falcor instance; `load_scene()` loads a `.pyscene` with the `DontMergeMaterials | RTDontMergeDynamic | DontOptimizeMaterials` flags so per-object LoD geometry is preserved; `create_render_pass()` wires the `VBufferRT → ReservoirSplatting → AccumulatePass` render graph.
- `lod_utils.py` — LoD geometry helpers: `min/max_distance_to_bound()` for camera-to-bounds distances and `get_lod_mesh_bounds()`, which looks up a mesh's bounding box by the `{name}_LoD_0` naming convention.

Per-scene render scripts (`render_*.py`, e.g. `render_Chessboard.py`) each implement the same flow:

1. `determine_lod_by_coc(coc)` — maps a circle-of-confusion value to an LoD level using scene-specific thresholds.
2. `determine_lod_level(camera, bounds)` — computes the CoC from the camera's focal length, aperture, and focal distance together with the distance to a mesh's bounds, then selects the LoD level.
3. `render()` — warms up, then runs the main loop: render each frame, save it as EXR, advance the camera (here, the focus-pull animation that changes the focal distance), and raise/lower each object's LoD via `scene.set_lod_level()` / `scene.raise_lod_level()` / `scene.lower_lod_level()`.
4. `render_gt()` — renders a high-sample-count reference along the same camera path for error comparison.

Scripts are invoked through `argparse` subcommands (`render`, `gt`, `pt`), each taking a `--config_file` YAML; see [Running an example](#running-an-example) below.

## Running an example

We provide the **Chessboard** example, which renders a focus-pull sequence: the camera's focal distance is animated over time, changing the depth-of-field blur and driving the dynamic LoD selection. The rendering scripts live under `python/`.

The Chessboard scene (models, textures, and `.pyscene` files) is not included in this repository. Download it from [Google Drive](https://drive.google.com/drive/folders/1OHftz_x2Bw41rx7EqXzU-PYFN4zqyvkP?usp=sharing) and place it under `scenes/Chessboard/`.

### 1. Build the project

Build Falcor first (see [Falcor's documentation](https://github.com/NVIDIAGameWorks/Falcor/blob/master/README.md)) so that `Mogwai` and the Python bindings are available. Always rebuild after any shader change.

### 2. Configure the run

The run is controlled by a YAML config. A ready-made one is at [`results/Chessboard/ours.yaml`](results/Chessboard/ours.yaml):

```yaml
enable_temporal: true
enable_spatial:  true
temporal_reuse_option: 'ScatterOnly'
scene_path: 'C:\path\to\Reservoir-Splatting\scenes\Chessboard\scene.pyscene'
max_bounces: 1
output_dir: './ours/'
num_iters: 180          # number of frames in the focus-pull sequence
num_images: 1           # samples accumulated per frame
resolution: [1920, 1080]
```

Update `scene_path` to point to `scenes/Chessboard/scene.pyscene` on your machine. Output EXR frames are written to `output_dir`, resolved relative to the directory containing the config file.

### 3. Render

From the `python/` directory, run the `render` subcommand inside the Python environment that has Falcor's bindings installed. This animates the camera's focal distance (the depth-of-field change) and adjusts each object's LoD level from the resulting circle-of-confusion as it goes:

```
python render_Chessboard.py render --config_file ../results/Chessboard/ours.yaml
```

This writes one EXR per frame (`img_0.exr`, `img_1.exr`, …) into the output directory and prints the average FPS when finished.

To render a high-sample-count reference for comparison, use the `gt` subcommand instead, which follows the same focus-pull path and accumulates many samples at a single frame:

```
python render_Chessboard.py gt --config_file ../results/Chessboard/gt.yaml
```

## Citation
If you use this codebase, or your work is based on this project, please cite our paper:
```
@inproceedings{Wang:2026:ReSTIR-LoD,
  title={Real-Time Level-of-Detail Rendering with ReSTIR},
  author={Wang, Yu-Chen and Kettunen, Markus and Lin, Daqi and Wyman, Chris and Wu, Lifan and Zhao, Shuang},
  booktitle = {ACM SIGGRAPH 2026 Conference Proceedings},
  doi = {10.1145/3799902.3811100},
  year = {2026},
}
```
