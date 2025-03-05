from PIL import Image
import numpy as np
from collections import Counter
import os
import pdb
import re
import json

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
                region_descriptions.append({region_name: semantic_label_string})
        return region_descriptions

    def get_semantic_info(self, semantic_image_path):
        label_image, image_height, image_width = self.semantic_to_label_image(semantic_image_path)
        semantic_info = self.get_grid_semantic_labels(label_image, image_width, image_height)
        return semantic_info
class TrajectoryProcessor():
    def __init__(self, town, path):
        self.town = town
        self.path = path
        self.semantic_processor=SemanticProcessor()
        self.front_image_folder = os.path.join("/home/yi/Projects/Carla_0.9/PythonAPI/dev_maps/data", town, path,
                                               "camera_images_front")
        self.semantic_image_folder = os.path.join("/home/yi/Projects/Carla_0.9/PythonAPI/dev_maps/data", town, path,
                                                  "camera_images_semantic_front")
        self.trajectory, self.filtered_image_files = self.get_trajectory(self.front_image_folder)
        self.step_move_info=self.get_step_move_info()
        self.step_semantic_info = self.get_step_semantic_info()

    def get_trajectory(self, image_folder):
        image_files = [f for f in os.listdir(image_folder) if f.endswith('.png')]
        image_files.sort()
        filtered_image_files = []
        trajectory = []
        index = 1
        for image_file in image_files:
            match = re.search(r'_loc_([^_]+)_([^_]+)_([^_]+)_rot_([^_]+)_([^_]+)_([^_]+)\.png', image_file)
            if match:
                x_loc, y_loc, z_loc, pitch_rot, yaw_rot, roll_rot = match.groups()
                if not (
                        x_loc == '0.0' and y_loc == '0.0' and z_loc == '0.0' and pitch_rot == '0.0' and yaw_rot == '0.0' and roll_rot == '0.0'):
                    filtered_image_files.append({"index": index, "image_file": image_file})
                    trajectory_point = {
                        "index": index,
                        "location": {"x": float(x_loc), "y": float(y_loc), "z": float(z_loc)},
                        "rotation": {"pitch": float(pitch_rot), "yaw": float(yaw_rot), "roll": float(roll_rot)}
                    }
                    trajectory.append(trajectory_point)
                    index += 1
                else:
                    pass
        assert len(trajectory)==len(filtered_image_files)
        return trajectory, filtered_image_files

    def get_step_move_info(self):
        step_move_info = []
        for i in range(len(self.trajectory)-1):
            point_i=self.trajectory[i]
            point_i_next=self.trajectory[i+1]
            assert point_i_next['index']==point_i['index']+1
            dx=point_i_next['location']['x']-point_i['location']['x']
            dy=point_i_next['location']['y']-point_i['location']['y']
            d_yaw=point_i_next['rotation']['yaw']-point_i['rotation']['yaw']
            step_info={"current": {"location": {"x": point_i['location']['x'],"y": point_i['location']['y']}, "rotation_yaw": point_i['rotation']['yaw']},
             "next step goal": {"location": {"x": point_i_next['location']['x'],"y": point_i_next['location']['y']}, "rotation_yaw": point_i_next['rotation']['yaw']},
             "move": {"dx":round(dx,1) , "dy":round(dy,1),"d_yaw":round(d_yaw,1)}}
            step_move_info.append({"index": point_i['index'],"step_info":step_info})
        return step_move_info

    def get_step_semantic_info(self):
        step_semantic_info=[]
        for i in range(len(self.trajectory) - 1):
            semantic_img_path=os.path.join(self.semantic_image_folder, self.filtered_image_files[i]['image_file'])
            semantic_info=self.semantic_processor.get_semantic_info(semantic_img_path)
            step_semantic_info.append({"index":self.filtered_image_files[i]["index"], "semantic_info": semantic_info})
        return step_semantic_info






if __name__ == "__main__":
    for town in ["Town01", "Town03", "Town04"]:
        path="Path_1"
        tra_pro=TrajectoryProcessor(town, path)
        # 定义保存文件的目录（确保目录存在）
        output_dir = f"/home/yi/Projects/Carla_0.9/PythonAPI/dev_maps/results/{town}/{path}/"
        os.makedirs(output_dir, exist_ok=True)  # 确保目录存在

        # 分别保存 trajectory 到单独的 JSON 文件
        trajectory_file = os.path.join(output_dir, f"trajectory_{town}_{path}.json")
        with open(trajectory_file, 'w', encoding='utf-8') as f:
            json.dump(tra_pro.trajectory, f, ensure_ascii=False, indent=4)
        print(f"Trajectory data for {town} saved to {trajectory_file}")

        # 分别保存 step_move_info 到单独的 JSON 文件
        move_info_file = os.path.join(output_dir, f"step_move_info_{town}_{path}.json")
        with open(move_info_file, 'w', encoding='utf-8') as f:
            json.dump(tra_pro.step_move_info, f, ensure_ascii=False, indent=4)
        print(f"Step move info for {town} saved to {move_info_file}")

        # 分别保存 step_semantic_info 到单独的 JSON 文件
        semantic_info_file = os.path.join(output_dir, f"step_semantic_info_{town}_{path}.json")
        with open(semantic_info_file, 'w', encoding='utf-8') as f:
            json.dump(tra_pro.step_semantic_info, f, ensure_ascii=False, indent=4)
        print(f"Step semantic info for {town} saved to {semantic_info_file}")
