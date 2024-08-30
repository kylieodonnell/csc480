from world_maker.World import World
from PIL import Image
from world_maker.data_analysis import (get_data, get_data_no_update, filter_negative, rectangle_2D_to_3D, skeleton_mountain_map, highway_map, filter_sobel, skeleton_highway_map,
                                       smooth_sobel_water, subtract_map, detect_mountain, filter_smooth, overide_map)
from world_maker.City import City
from world_maker.Position import Position
from random import randint
from world_maker.pack_rectangle import generate_building

import numpy as np


def world_maker():
    world = World()
    heightmap, watermap, treemap = get_data(world)
    # heightmap, watermap, treemap = get_data_no_update()
    heightmap_smooth = filter_smooth(heightmap, 4)
    heightmap_smooth.save('./world_maker/data/heightmap_smooth.png')

    filter_sobel(
        "./world_maker/data/heightmap.png").save('./world_maker/data/sobelmap.png')
    filter_sobel(heightmap_smooth).save(
        './world_maker/data/sobelmap_from_smooth.png')

    smooth_sobel_water_map = smooth_sobel_water(
        './world_maker/data/sobelmap_from_smooth.png')
    skeleton_highway = skeleton_highway_map(highway_map())

    city = City()
    city.generate_district()
    city.loop_expend_district()
    city.district_draw_map()

    road_grid = city.district_generate_road()
    image_mountain_map = city.get_district_mountain_map()
    road = city.draw_roads(4)
    road.save('./world_maker/data/roadmap.png')

    # Buildings
    subtract_map(smooth_sobel_water_map, road).save(
        './world_maker/data/city_map.png')
    subtract_map('./world_maker/data/city_map.png',
                 './world_maker/data/skeleton_highway_area.png').save('./world_maker/data/city_map.png')
    subtract_map('./world_maker/data/city_map.png',
                 './world_maker/data/mountain_map.png').save('./world_maker/data/city_map.png')

    rectangle_building = generate_building(
        './world_maker/data/city_map.png', './world_maker/data/heightmap.png', output='./world_maker/data/building.png', min_width=20, max_width=40)
    rectangle_building = rectangle_2D_to_3D(rectangle_building)

    # Houses
    skeleton_mountain = skeleton_mountain_map(image_mountain_map)
    subtract_map('./world_maker/data/mountain_map.png',
                 './world_maker/data/skeleton_mountain_area.png').save('./world_maker/data/mountain_map.png')
    subtract_map('./world_maker/data/mountain_map.png',
                 './world_maker/data/skeleton_highway_area.png').save('./world_maker/data/mountain_map.png')
    subtract_map(smooth_sobel_water_map, filter_negative(
        './world_maker/data/mountain_map.png')).save('./world_maker/data/mountain_map.png')

    rectangle_mountain = generate_building(
        './world_maker/data/mountain_map.png', './world_maker/data/heightmap.png', output='./world_maker/data/building_moutain.png')
    rectangle_mountain = rectangle_2D_to_3D(
        rectangle_mountain)

    # Road
    heightmap_smooth_2 = filter_smooth(heightmap, 4)
    heightmap_smooth_2.save('./world_maker/data/heightmap_smooth_2.png')
    overide_map('./world_maker/data/skeleton_highway_area.png',
                './world_maker/data/skeleton_mountain_area.png').save('./world_maker/data/full_road.png')
    overide_map('./world_maker/data/full_road.png',
                './world_maker/data/roadmap.png').save('./world_maker/data/full_road.png')

    road_heightmap = subtract_map(
        heightmap_smooth_2, filter_negative('./world_maker/data/full_road.png'))

    road_heightmap.save('./world_maker/data/road_heightmap.png')

    # Terraforming
    # Smooth initialization
    overide_map('./world_maker/data/heightmap.png',
                './world_maker/data/building_moutain.png').save('./world_maker/data/heightmap_with_building.png')
    overide_map('./world_maker/data/heightmap_with_building.png',
                './world_maker/data/building.png').save('./world_maker/data/heightmap_with_building.png')
    filter_smooth(
        './world_maker/data/heightmap_with_building.png', 2).save('./world_maker/data/heightmap_with_building.png')

    overide_map('./world_maker/data/heightmap_with_building.png',
                road_heightmap).save('./world_maker/data/heightmap_with_building.png')

    filter_smooth('./world_maker/data/heightmap_with_building.png',
                  2).save('./world_maker/data/heightmap_with_building.png')

    # Smooth repetition
    for i in range(10):
        overide_map('./world_maker/data/heightmap_with_building.png',
                    './world_maker/data/building_moutain.png').save('./world_maker/data/heightmap_with_building.png')
        overide_map('./world_maker/data/heightmap_with_building.png',
                    './world_maker/data/building.png').save('./world_maker/data/heightmap_with_building.png')
        filter_smooth(
            './world_maker/data/heightmap_with_building.png', 2).save('./world_maker/data/heightmap_with_building.png')

    filter_smooth(
        './world_maker/data/heightmap_with_building.png', 2).save('./world_maker/data/heightmap_smooth.png')

    return rectangle_mountain, rectangle_building, skeleton_highway, skeleton_mountain, road_grid
