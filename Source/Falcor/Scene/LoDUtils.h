#pragma once
#include <optional>
#include <string>
#include <tuple>
#include <vector>

namespace Falcor
{

struct LoDMetaData {
    std::string name;
    int maxLevel;
    std::vector<int> meshIDs;

    LoDMetaData(): name(""), maxLevel(0), meshIDs() {}

    LoDMetaData(const std::string& name, int maxLevel, const std::vector<int>& meshIDs)
        : name(name), maxLevel(maxLevel), meshIDs(meshIDs) {}

    LoDMetaData(const std::string& name, int maxLevel)
        : name(name), maxLevel(maxLevel), meshIDs(maxLevel, 0) {}
};

bool isLoDMesh(const std::string& meshName);
std::optional<std::tuple<std::string, int>> parseLodMeshName(const std::string& meshName);

} // namespace Falcor
