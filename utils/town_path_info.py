def get_start_dest(town, path):
    if town == 'Town01':
        if path=='Path_1':
            point1 = [213.49, 323.70, 0.11]
            point2 = [331.47, 144.23, 0.11]
    elif town == 'Town02':
        if path=='Path_1':
            point1 = [78.18, 183.55, 0.33]
            point2 = [23.21, 298.54, 0.33]
    elif town == 'Town03':
        if path=='Path_1':
            point1 = [11.10, 30.30, 0.16]
            point2 = [75.30, 80.15, 0.15]
    elif town == 'Town04':
        if path=='Path_1':
            point1 = [268.40, -176.12, 0.35]
            point2 = [138.62, -190.76, 0.23]
    elif town == 'Town05':
        if path=='Path_1':
            point1 = [58.52, 79.70, 0.16]
            point2 = [-41.36, -53.03, 0.22]
    else: #Town10
        point1 = [1.67, 3.11, 0.16]
        point2 = [93.66, 86.69, 0.16]
    return point1, point2

