#include "Scene/SceneDefines.slangh"
#include "RaytracingCommon.slang"

import GatherHelper;
import Rendering.Utils.PixelStats;
import Utils.Debug.PixelDebug;
import Utils.Math.PackedFormats;
import Utils.Math.FormatConversion;
import PathTracer;
import ReconnectionData;
import Reservoir;
import ShiftMapping;

import Utils.Color.ColorHelpers;

import Utils.NVAPI; // TODO(@skallweit) this is currently needed to make g_NvidiaExt visible

// ParameterBlock<PathTracer> gPathTracer;

struct RandomReplayTemporalSamples
{
    PathTracerParams params;
    StructuredBuffer<PathReservoir> prevReservoirs;
    StructuredBuffer<ReconnectionData> prevReconnectionData;
    StructuredBuffer<PathReservoir> currReservoirs;
    StructuredBuffer<ReconnectionData> currReconnectionData;

    RWStructuredBuffer<ShiftedPathData> shiftedPathDataBuffer;

    void run(const uint2 pixel)
    {
        printSetPixel(pixel);
        print("======= Random Replay Temporal Samples =======", pixel);
        uint pathID = pixel.x | (pixel.y << 12);
        uint reservoirIdx = params.linearizePixel(pixel);
        uint screenPixels = params.frameDim.x * params.frameDim.y;

        GatherHelper gatherHelper = GatherHelper(pixel, params.frameDim);
        uint2 prevPixel = (uint2) gatherHelper.prevPixel;
        uint prevPathID = prevPixel.x | (prevPixel.y << 12);
        uint prevReservoirIdx = params.linearizePixel(prevPixel);

        PathReservoir prevReservoir = prevReservoirs[prevReservoirIdx];
        ReconnectionData prevReconnection = prevReconnectionData[prevReservoirIdx];

        // Random Replay previous path to the current frame.
        ShiftedPathData shiftedPathData = ShiftedPathData();
        shiftedPathData.radiance = randomReplay(pathID, prevReconnection, false);
        shiftedPathDataBuffer[reservoirIdx] = shiftedPathData;

        PathReservoir currReservoir = currReservoirs[reservoirIdx];
        ReconnectionData currReconnection = currReconnectionData[reservoirIdx];
        // Random Replay current path to the previous frame.
        ShiftedPathData shiftedPrevPathData = ShiftedPathData();
        shiftedPrevPathData.radiance = randomReplay(prevPathID, currReconnection, true);
        shiftedPathDataBuffer[reservoirIdx + screenPixels] = shiftedPrevPathData;
    }
}

cbuffer CB
{
    RandomReplayTemporalSamples gRandomReplayTemporalSamples;
}

[numthreads(8, 16, 1)]
void main(uint3 dispatchThreadId: SV_DispatchThreadID)
{
    uint2 pixel = dispatchThreadId.xy;
    if (all(pixel >= gRandomReplayTemporalSamples.params.frameDim)) return;

    gRandomReplayTemporalSamples.run(pixel);
}
