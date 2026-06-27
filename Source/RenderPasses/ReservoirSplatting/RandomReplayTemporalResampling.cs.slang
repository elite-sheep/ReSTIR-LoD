// Copyright @yucwang 2025

#include "Utils/Math/MathConstants.slangh"
#include "Scene/SceneDefines.slangh"
#include "RaytracingCommon.slang"

import Utils.Color.ColorHelpers;
import Utils.Debug.PixelDebug;

import LoadShadingData;
import PathTracer;
import ReconnectionData;
import Reservoir;

import GatherHelper;

import ShiftOptions;
import ShiftMapping;

struct RandomReplayTemporalResampling
{
    bool useConfidenceWeights;

    PathTracerParams params;

    StructuredBuffer<PathReservoir> prevReservoirs;
    RWStructuredBuffer<PathReservoir> currReservoirs;

    StructuredBuffer<ReconnectionData> prevReconnectionData;
    RWStructuredBuffer<ReconnectionData> currReconnectionData;

    StructuredBuffer<ShiftedPathData> shiftedPathDataBuffer;

    /** Runs the path tracer for a single pixel.
        \param[in] pixel Pixel index.
    */
    void run(uint2 pixel)
    {
        printSetPixel(pixel);
        print("======= Random Replay Temporal Resampling =======", pixel);
        SampleGenerator sg = SampleGenerator(pixel, (params.useFixedSeed > 0) ? params.fixedSeed + 3 : kNumRenderPasses * (params.frameCount + params.seed) + 3);

        GatherHelper gatherHelper = GatherHelper(pixel, params.frameDim);
        uint32_t reservoirIdx = params.linearizePixel(pixel);
        uint32_t prevReservoirIdx = params.linearizePixel((uint2) gatherHelper.prevPixel);

        // At this point we can assume that a previous reservoir exists and is valid.
        PathReservoir dstReservoir = PathReservoir();
        ReconnectionData dstReconnectionData = ReconnectionData();

        {
            PathReservoir prevReservoir = prevReservoirs[prevReservoirIdx];
            PathReservoir currReservoir = currReservoirs[reservoirIdx];

            ReconnectionData prevReconnection = prevReconnectionData[prevReservoirIdx];
            ReconnectionData currReconnection = currReconnectionData[reservoirIdx];

            uint screenPixels = params.frameDim.x * params.frameDim.y;

            float currSampleMIS = 0.0f;
            float3 currPHat = float3(0.0f, 0.0f, 0.0f);
            // Handle the current reservoir (initial candidate) first.
            if (any(currReservoir.integrand > 0.0f))
            {
                // Shifting current sample to current domain... pHat remains the same and the Jacobian is 1.
                float m1 = luminance(currReservoir.integrand) * (useConfidenceWeights ? currReservoir.confidence : 1.0f);
                currPHat = currReservoir.integrand;

                // Shifting current sample to previous domain.
                float3 shiftedCurrRadiance = shiftedPathDataBuffer[screenPixels + reservoirIdx].radiance;
                float shiftedJacobian = 1.0f;
                float m2 = luminance(shiftedCurrRadiance) * shiftedJacobian * (useConfidenceWeights ? prevReservoir.confidence : 1.0f);

                // TODO: This check is only necessary if the secondaryPathJacobian ever equals 0... is that ever possible?
                m2 = isnan(m2) ? 0.0f : m2;

                currSampleMIS = (m1 + m2 == 0.0f) ? 0.0f : m1 / (m1 + m2);
            }
            bool currSelected = dstReservoir.addSampleFromReservoir(sg, currSampleMIS, currPHat, 1.0f, currReservoir);
            dstReconnectionData = currSelected ? currReconnection : dstReconnectionData;

            // Reconnection shift. Connect y_1 with x_2, regardless of if it's in the shutter time or not.
            float prevSampleMIS = 0.0f;
            float3 prevPHat = float3(0.0f, 0.0f, 0.0f);
            float shiftedJacobian = 1.0f;
            if (any(prevReservoir.integrand > 0.0f))
            {
                // Shift previous sample to current domain.
                float3 currPrevRadiance = shiftedPathDataBuffer[reservoirIdx].radiance;
                shiftedJacobian = 1.0f;
                float m1 = luminance(currPrevRadiance) * shiftedJacobian * (useConfidenceWeights ? currReservoir.confidence : 1.0f);

                // TODO: are all these NaN-checks still necessary? Should only happen if the secondary path Jacobian is 0 at any point.
                prevPHat = isnan(m1) ? float3(0.0f, 0.0f, 0.0f) : currPrevRadiance;
                shiftedJacobian = isnan(m1) ? 1.0f : shiftedJacobian; // W_{y_i} = W_{x_i} * |T(x)|
                m1 = isnan(m1) ? 0.0f : m1;

                // Shift previous sample to previous domain... the previous pHat is the same with a Jacobian of 1.
                float m2 = luminance(prevReservoir.integrand) * (useConfidenceWeights ? prevReservoir.confidence : 1.0f);

                prevSampleMIS = ((m1 + m2) == 0.0f) ? 0.0f : m2 / (m1 + m2);
            }

            bool prevSelected = dstReservoir.addSampleFromReservoir(sg, prevSampleMIS, prevPHat, shiftedJacobian, prevReservoir);
            dstReconnectionData = prevSelected ? prevReconnection : dstReconnectionData;
        }

        currReservoirs[reservoirIdx] = dstReservoir;
        currReconnectionData[reservoirIdx] = dstReconnectionData;
    }
}

cbuffer CB
{
    RandomReplayTemporalResampling gRandomReplayTemporalResampling;
}

//
// Shader entry point for ray generation shader.
//

[numthreads(8, 16, 1)]
void main(uint3 dispatchThreadId: SV_DispatchThreadID)
{
    uint2 pixel = dispatchThreadId.xy;
    uint2 frameDim = gRandomReplayTemporalResampling.params.frameDim;
    if (all(pixel >= frameDim)) return;

    printSetPixel(pixel);
    gRandomReplayTemporalResampling.run(pixel);
}
