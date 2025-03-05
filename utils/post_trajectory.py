import os
import re
import math
import carla
from collections import Counter
def post_get_trajectory(image_folder):
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
                filtered_image_files.append(image_file)
                trajectory_point = {
                    "index": index,
                    "location": {"x": float(x_loc), "y": float(y_loc), "z": float(z_loc)},
                    "rotation": {"pitch": float(pitch_rot), "yaw": float(yaw_rot), "roll": float(roll_rot)}
                }
                trajectory.append(trajectory_point)
                index += 1
            else:
                pass
    return trajectory, filtered_image_files

def get_turning_points(trajectory, threshold_yaw_rotation):
    turning_points_indices = []
    num_points = len(trajectory)
    if num_points < 2:  # Less than 2 points, no change possible
        return []
    for i in range(num_points - 1):  # Iterate to calculate change to next point
        yaw_current = trajectory[i]['rotation']['yaw']
        yaw_next = trajectory[i+1]['rotation']['yaw']
        delta_yaw = abs(yaw_next - yaw_current) # Absolute difference
        if delta_yaw > threshold_yaw_rotation:
            turning_points_indices.append(i+1) # Indicate the point *after* the change
    return turning_points_indices

def get_clock_direction_from_yaw(yaw_degrees):
    yaw_degrees = float(yaw_degrees)
    if -15 <= yaw_degrees <= 15:
        return "0 o'clock direction"  # 0 or 12 o'clock - (Center angle 0°)
    elif 15 < yaw_degrees <= 45:
        return "1 o'clock direction"  # 1 o'clock - (Center angle 30°)
    elif 45 < yaw_degrees <= 75:
        return "2 o'clock direction"  # 2 o'clock - (Center angle 60°)
    elif 75 < yaw_degrees <= 105:
        return "3 o'clock direction"  # 3 o'clock - (Center angle 90°)
    elif 105 < yaw_degrees <= 135:
        return "4 o'clock direction"  # 4 o'clock - (Center angle 120°)
    elif 135 < yaw_degrees <= 165:
        return "5 o'clock direction"  # 5 o'clock - (Center angle 150°)
    elif yaw_degrees >= 165 or yaw_degrees <= -165: # Handling wrap around for 6 o'clock direction
        return "6 o'clock direction"  # 6 o'clock - (Center angle 180° or -180°)
    elif -165 < yaw_degrees <= -135:
        return "7 o'clock direction"  # 7 o'clock - (Center angle -150°)
    elif -135 < yaw_degrees <= -105:
        return "8 o'clock direction"  # 8 o'clock - (Center angle -120°)
    elif -105 < yaw_degrees <= -75:
        return "9 o'clock direction"  # 9 o'clock - (Center angle -90°)
    elif -75 < yaw_degrees <= -45:
        return "10 o'clock direction" # 10 o'clock - (Center angle -60°)
    elif -45 < yaw_degrees <= -15:
        return "11 o'clock direction" # 11 o'clock - (Center angle -30°)
    else:
        return "Unknown direction"

def get_direction(start, end):
    """Calculate direction from start point to end point."""
    dx = end.x - start.x  # Calculate the difference in x-coordinates (East-West direction)
    dy = end.y - start.y  # Calculate the difference in y-coordinates (North-South direction)
    vertical_direction = ''
    horizontal_direction = ''
    if dy > 0:
        vertical_direction = 'South' # Moving in the South direction
    elif dy < 0:
        vertical_direction = 'North' # Moving in the North direction

    if dx > 0:
        horizontal_direction = 'East' # Moving in the East direction
    elif dx < 0:
        horizontal_direction = 'West' # Moving in the West direction

    return vertical_direction+horizontal_direction

def calculate_distance(start, end):
    dx = end.x - start.x
    dy = end.y - start.y
    dz = end.z - start.z
    return math.sqrt(dx ** 2 + dy ** 2 + dz **2)

def total_trajectory_length(trajectory, start_location=None, dest_location=None):
    tra_point_0_location=carla.Location(x=trajectory[0]["location"]['x'], y=trajectory[0]["location"]['y'],
                                   z=trajectory[0]["location"]['z'])
    if start_location:
        total_length = calculate_distance(start_location, tra_point_0_location)
    else:
        total_length = 0

    for i in range(len(trajectory) - 1):
        start_loc = carla.Location(x=trajectory[i]["location"]['x'], y=trajectory[i]["location"]['y'],
                                   z=trajectory[i]["location"]['z'])
        end_loc = carla.Location(x=trajectory[i + 1]["location"]['x'], y=trajectory[i + 1]["location"]['y'],
                                 z=trajectory[i + 1]["location"]['z'])

        segment_length = calculate_distance(start_loc, end_loc)
        total_length += segment_length

    tra_point_last_location = carla.Location(x=trajectory[-1]["location"]['x'], y=trajectory[-1]["location"]['y'],
                                          z=trajectory[-1]["location"]['z'])
    if dest_location:
        total_length+=calculate_distance(tra_point_last_location, dest_location)
    else:
        total_length += 0
    return round(total_length)

def segment_trajectory_by_turning_points(trajectory, turning_points_indices):
    segments_info = []
    start_index = 0

    split_indices = sorted(list(set([0] + turning_points_indices + [len(trajectory)])))

    for i in range(len(split_indices) - 1):
        segment_start_index = split_indices[i]
        segment_end_index = split_indices[i+1]
        segment_points = trajectory[segment_start_index:segment_end_index]
        segment_yaw_values = [point['rotation']['yaw'] for point in segment_points]

        if not segment_yaw_values:
            continue

        yaw_counts = Counter(segment_yaw_values)
        modal_yaw = yaw_counts.most_common(1)[0][0]

        direction_description = get_clock_direction_from_yaw(modal_yaw)
        segment_length_value = total_trajectory_length(segment_points) # 计算当前轨迹段的长度
        if segment_length_value>0:
            segments_info.append({
                'start_index': segment_start_index + 1,
                'end_index': segment_end_index,
                'modal_yaw': modal_yaw,
                'direction_description': direction_description,
                'segment_length': segment_length_value # 添加轨迹段长度
            })

    return segments_info

def generate_trajectory_description(overall_direction, total_length, segments_info):
    num_segments = len(segments_info)

    description = f"""The destination is in the {overall_direction} direction from the starting point.The approximate walking distance of this path is about {round(total_length)} meters.Along the way, the path is segmented into {num_segments} distinct sections."""

    for i in range(num_segments - 1): # Loop through segments except the last one
        segment = segments_info[i] # Access the segment dictionary directly
        description += f" Segment {i+1} heads towards the {segment['direction_description']} for approximately {round(segment['segment_length'])} meters, then"

    if segments_info: # Check if there are any segments to avoid index error if segments_info is empty
        last_segment = segments_info[-1] # Access the last segment using negative index
        description += f" Finally, the last segment, Segment {num_segments}, guides the path towards the {last_segment['direction_description']} direction, with a length of around {round(last_segment['segment_length'])} meters."
    else:
        description += " There are no path segments to describe." # Handle case with no segments

    return description


def get_trajectory_description(image_folder, start_location, dest_location):
    trajectory, filtered_image_files = post_get_trajectory(image_folder)
    direction = get_direction(start_location, dest_location)
    trajectory_length = total_trajectory_length(trajectory, start_location, dest_location)
    turning_points_indices = get_turning_points(trajectory, threshold_yaw_rotation=13)
    seg_info = segment_trajectory_by_turning_points(trajectory, turning_points_indices)
    return generate_trajectory_description(direction, trajectory_length, seg_info)



if __name__ == '__main__':
    # get the start and destination locattions
    point1 = [213.49, 323.70, 0.11]
    point2 = [331.47, 144.23, 0.11]
    start_location = carla.Location(x=point1[0], y=point1[1], z=point1[2])
    dest_location = carla.Location(x=point2[0], y=point2[1], z=point2[2])

    # get the trajectory information
    image_folder = "/home/yi/Projects/Carla_0.9/PythonAPI/dev_maps/data/Town01/camera_images_front"

    print(get_trajectory_description(image_folder,start_location, dest_location))