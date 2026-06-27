#pragma once
#include "LoDUtils.h"

#include <regex>

namespace Falcor
{

bool isLoDMesh(const std::string& meshName)
{
    static const std::regex lodPattern(R"(.*_LoD_\d+$)", std::regex::icase);
    return std::regex_match(meshName, lodPattern);
}

std::optional<std::tuple<std::string, int>> parseLodMeshName(const std::string& meshName)
{
    static const std::regex lodPattern(R"(^(.*)_LoD_(\d+)$)", std::regex::icase);
    std::smatch match;
    if (std::regex_match(meshName, match, lodPattern))
    {
        std::string baseName = match[1];
        int lodLevel = std::stoi(match[2]);
        return std::make_tuple(baseName, lodLevel);
    }
    return std::nullopt;
}

} // namespace Falcor
