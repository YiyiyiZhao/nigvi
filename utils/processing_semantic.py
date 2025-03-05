from PIL import Image
import numpy as np
from collections import Counter
import os
import pdb
import re
import json
from tqdm import tqdm

class SemanticProcessor():
    def __init__(self, top_n=5):
        self.color_map=self.create_cityscapes_color_label_map()
        self.top_n=top_n
    def create_cityscapes_color_label_map(self):
        color_map = {
            (0, 0, 0): 'Unlabeled',
            (128, 64, 128): 'Roads',
            (244, 35, 232): 'SideWalks',
            (70, 70, 70): 'Building',
            (102, 102, 156): 'Wall',
            (190, 153, 153): 'Fence',
            (153, 153, 153): 'Pole',
            (250, 170, 30): 'TrafficLight',
            (220, 220, 0): 'TrafficSign',
            (107, 142, 35): 'Vegetation',
            (152, 251, 152): 'Terrain',
            (70, 130, 180): 'Sky',
            (220, 20, 60): 'Pedestrian',
            (255, 0, 0): 'Rider',
            (0, 0, 142): 'Car',
            (0, 0, 70): 'Truck',
            (0, 60, 100): 'Bus',
            (0, 80, 100): 'Train',
            (0, 0, 230): 'Motorcycle',
            (119, 11, 32): 'Bicycle',
            (110, 190, 160): 'Static',
            (170, 120, 50): 'Dynamic',
            (55, 90, 80): 'Other',
            (45, 60, 150): 'Water',
            (157, 234, 50): 'RoadLine',
            (81, 0, 81): 'Ground',
            (150, 100, 100): 'Bridge',
            (230, 150, 140): 'RailTrack',
            (180, 165, 180): 'GuardRail',
        }
        return color_map
    def semantic_to_label_image(self, semantic_image_path):
        img = Image.open(semantic_image_path).convert('RGB')
        img_array = np.array(img)
        height, width, _ = img_array.shape

        label_image = np.zeros((height, width), dtype=object) # 使用 object dtype 存储字符串标签

        for h in range(height):
            for w in range(width):
                pixel_color = tuple(img_array[h, w, :])
                label = self.color_map.get(pixel_color, "Unknown")
                label_image[h, w] = label
        return label_image, height, width

    def get_grid_semantic_labels(self, label_image, image_width, image_height):
        region_descriptions = []
        row_split_points = [int(image_height * (i / 2)) for i in range(3)]
        col_split_points = [int(image_width * (i / 3)) for i in range(4)]
        regions = {
            "top_left":      (row_split_points[0], row_split_points[1], col_split_points[0], col_split_points[1]),
            "top_middle":    (row_split_points[0], row_split_points[1], col_split_points[1], col_split_points[2]),
            "top_right":     (row_split_points[0], row_split_points[1], col_split_points[2], col_split_points[3]),
            "bottom_left":   (row_split_points[1], row_split_points[2], col_split_points[0], col_split_points[1]),
            "bottom_middle": (row_split_points[1], row_split_points[2], col_split_points[1], col_split_points[2]),
            "bottom_right":  (row_split_points[1], row_split_points[2], col_split_points[2], col_split_points[3])
        }

        for region_name, (row_start, row_end, col_start, col_end) in regions.items():
            current_region_labels = []
            for row in range(row_start, row_end):
                current_region_labels.extend(label_image[row, col_start:col_end].flatten())

            label_counts = Counter(current_region_labels)
            labels_to_remove = ['Unlabeled', 'Unknown', 'Other']
            for label_to_remove in labels_to_remove:
                label_counts.pop(label_to_remove, None)

            top_label_counts = label_counts.most_common(self.top_n)
            top_labels = [label for label, count in top_label_counts]

            if top_labels:
                semantic_label_string = ", ".join([label for label in top_labels])
            else:
                semantic_label_string = None
            region_descriptions.append({region_name: semantic_label_string})
        return region_descriptions

    def get_semantic_info(self, semantic_image_path):
        label_image, image_height, image_width = self.semantic_to_label_image(semantic_image_path)
        semantic_info = self.get_grid_semantic_labels(label_image, image_width, image_height)
        return semantic_info


if __name__=="__main__":
    sem_pro=SemanticProcessor()
    town_dir = "Town01"
    path_dir = "/home/yi/Projects/Carla_0.9/PythonAPI/dev_maps/data/Town01/Path_1/camera_images_semantic_front"
    image_files = [f for f in os.listdir(path_dir) if f.endswith(".png")]
    image_files.sort()

    min_idx = float('inf')

    trajectory_semantic_labels=[]
    for image_file in tqdm(image_files[:20]):
        match = re.search(r'^(\d+)_loc_([^_]+)_([^_]+)_([^_]+)_rot_([^_]+)_([^_]+)_([^_]+)\.png', image_file)
        if match:
            idx, x_loc, y_loc, z_loc, pitch_rot, yaw_rot, roll_rot = match.groups()
            current_idx = int(idx)
            if current_idx<min_idx:
                min_idx = current_idx
            if not (x_loc == '0.0' and y_loc == '0.0' and z_loc == '0.0' and pitch_rot == '0.0' and yaw_rot == '0.0' and roll_rot == '0.0'):
                semantic_info=sem_pro.get_semantic_info(os.path.join(path_dir, image_file))
                up_idx=current_idx-min_idx
                print({"idx": up_idx, "x": x_loc, "y": y_loc, "z_loc":z_loc, "pitch_rot": pitch_rot, "yaw_rot": yaw_rot, "roll_rot": roll_rot, "semantic_grid":semantic_info})