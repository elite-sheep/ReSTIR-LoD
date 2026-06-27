# Copyright @yucwang 2025

import falcor

def clamp(x, low, high):
    return max(low, min(x, high))

def min_distance_to_bound(p, bounds):
    bounds_min = bounds.min_point
    bounds_max = bounds.max_point
    dx = clamp(p.x, bounds_min.x, bounds_max.x) - p.x
    dy = clamp(p.y, bounds_min.y, bounds_max.y) - p.y
    dz = clamp(p.z, bounds_min.z, bounds_max.z) - p.z
    return (dx * dx + dy * dy + dz * dz) ** 0.5

def max_distance_to_bound(p, bounds):
    bounds_min = bounds.min_point
    bounds_max = bounds.max_point
    dx = (bounds_min.x - p.x) if abs(bounds_min.x - p.x) > abs(bounds_max.x - p.x) else (bounds_max.x - p.x)
    dy = (bounds_min.y - p.y) if abs(bounds_min.y - p.y) > abs(bounds_max.y - p.y) else (bounds_max.y - p.y)
    dz = (bounds_min.z - p.z) if abs(bounds_min.z - p.z) > abs(bounds_max.z - p.z) else (bounds_max.z - p.z)
    return (dx * dx + dy * dy + dz * dz) ** 0.5

def get_lod_mesh_bounds(scene, lod_name):
    mesh_name = f'{lod_name}_LoD_0'
    for mesh_id in range(scene.get_mesh_count()):
        mesh_name_i = scene.get_mesh_name(mesh_id)
        if mesh_name_i == mesh_name:
            return scene.get_mesh_bounds(mesh_id)

    return None
