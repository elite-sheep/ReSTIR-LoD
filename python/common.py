# Copyright @yucwang 2025

from config import RenderConfig
import falcor
from pathlib import Path

def load_scene(testbed: falcor.Testbed, scene_path: Path, aspect_ratio=1.0):
    flags = (
        falcor.SceneBuilderFlags.DontMergeMaterials
        | falcor.SceneBuilderFlags.RTDontMergeDynamic
        | falcor.SceneBuilderFlags.DontOptimizeMaterials
    )
    testbed.load_scene(scene_path, flags)
    testbed.scene.camera.aspectRatio = aspect_ratio
    testbed.scene.renderSettings.useAnalyticLights = True
    testbed.scene.renderSettings.useEnvLight = True
    return testbed.scene

def create_testbed(reso: tuple):
    device_id = 0
    testbed = falcor.Testbed(
        width=reso[0], height=reso[1], create_window=False, gpu=device_id
    )
    testbed.clock.time = 0
    testbed.clock.pause()
    return testbed

def create_render_pass(testbed: falcor.Testbed,
                       config: RenderConfig,
                       verbose: bool = False):
    if verbose:
        print(f"Creating render pass with config: {config.__dict__}")

    render_graph = testbed.create_render_graph('RenderGraph')

    VBufferParams = {
        'samplePattern': "Center",
        'sampleCount': 1,
        'useAlphaTest': True,
        'useDOF' : True
    }

    ReSTIRParams = {
        'samplesPerPixel': 1,
        'enableTemporalResampling': config.enable_temporal,
        'enableSpatialResampling': config.enable_spatial,
        'temporalReuse': config.temporal_reuse_option,
        'maxSurfaceBounces': config.max_bounces,
        'numTimePartitions': 2,
        'hybridMISOption': "Balance",
        'gatherOption': "Fast",
    }

    VBufferRT = render_graph.createPass("VBufferRT",
                                        "VBufferRT",
                                        VBufferParams)
    ReSTIRPass = render_graph.createPass("ReservoirSplatting",
                                         "ReservoirSplatting",
                                         ReSTIRParams)
    AccumulatePass = render_graph.createPass("AccumulatePass",
                                             "AccumulatePass",
                                             {'enabled': False, 'precisionMode': 'Single'})
    render_graph.add_edge("VBufferRT.vbuffer", "ReservoirSplatting.vbuffer")
    render_graph.add_edge("VBufferRT.mvec", "ReservoirSplatting.mvec")
    render_graph.add_edge("ReservoirSplatting.color", "AccumulatePass.input")
    render_graph.mark_output("AccumulatePass.output")
    render_graph.mark_output("ReservoirSplatting.color")

    passes = {
        "ReSTIRPass": ReSTIRPass,
        "AccumulatePass": AccumulatePass
    }
    testbed.render_graph = render_graph

    return passes
