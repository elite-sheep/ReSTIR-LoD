add_plugin(ReservoirSplatting)

target_sources(ReservoirSplatting PRIVATE
    ReservoirSplatting.cpp
    ReservoirSplatting.h
    # Common Utility
    CameraManager.slang
    LoadShadingData.slang
    PathTracer.slang
    Params.slang
    PathStates.slang
    ReflectTypes.cs.slang
    StaticParams.slang
    RaytracingCommon.slang
    # Shift Utility
    Reservoir.slang
    ReconnectionData.slang
    ShiftOptions.slang
    ShiftMapping.slang
    # Initial Candidates
    InitialCandidates.cs.slang
    # Gather Temporal Resampling
    GatherHelper.slang
    RobustReuseOptimization.cs.slang
    CollectTemporalSamples.cs.slang
    GatherTemporalResampling.cs.slang
    # Scatter Temporal Resampling
    ReprojectTemporalSamples.cs.slang
    SortReprojectedReservoirs.cs.slang
    ScatterTemporalResampling.cs.slang
    # Scatter + Backup Temporal Resampling
    ScatterBackupTemporalResampling.cs.slang
    # Multi-Scatter Temporal Resampling
    MultiReprojectTemporalSamples.cs.slang
    MultiSortReprojectedReservoirs.cs.slang
    MultiScatterTemporalResampling.cs.slang
    # Random-Replay Temporal Resampling
    RandomReplayTemporalResampling.cs.slang
    RandomReplayTemporalSamples.cs.slang
    # Spatial Resampling
    SpatialResampling.cs.slang
    # Resolve ReSTIR
    ResolveReSTIR.cs.slang
    # Visualization Utility
    VisualizeForwardReprojection.cs.slang
)

target_copy_shaders(ReservoirSplatting RenderPasses/ReservoirSplatting)

target_source_group(ReservoirSplatting "RenderPasses")
