from utils.vlm_response import *
from utils.post_trajectory import *
from utils.town_path_info import *
from tqdm import tqdm
import pdb



class NIGenerator():
    def __init__(self, town, path, vlm_model):
        self.town=town
        self.path = path

        self.dir_path=os.path.join(f"data/{town}/{path}")
        self.bve_img_path=os.path.join(self.dir_path,f"{town.lower()}.png")
        self.front_img_dir=os.path.join(self.dir_path, "camera_images_front")
        self.semantic_img_dir=os.path.join(self.dir_path,"camera_images_semantic_front")

        self.start_location=None
        self.dest_location=None
        self.trajectory=None
        self.trajectory_info=None

        self.vlm_req = VLMRequester(vlm_model)

    def generate_overall(self):
        point1,point2=get_start_dest(self.town, self.path)
        self.start_location = carla.Location(x=point1[0], y=point1[1], z=point1[2])
        self.dest_location = carla.Location(x=point2[0], y=point2[1], z=point2[2])
        self.trajectory_info=get_trajectory_description(self.front_img_dir, self.start_location, self.dest_location)
        print(self.trajectory_info)
        res = self.vlm_req.request(self.bve_img_path, 'overall', self.trajectory_info)
        return res
    def generate_step(self):
        pass

if __name__ == '__main__':
    # res_dir="results"
    # os.makedirs(res_dir, exist_ok=True)
    #
    # instructions=[]
    #
    # for town in tqdm(['Town01', 'Town02', 'Town03', 'Town04', 'Town05', 'Town10']):
    #     path = "Path_1"
    #     for vlm_name in tqdm(['gpt-4o', 'claude-3-5-sonnet-20241022','gemini-2.0-flash-thinking-exp-01-21','minicpm-2-6-int4']):
    #         ni = NIGenerator(town, path, vlm_name)
    #         ni_overall=ni.generate_overall()
    #         result = {"town": town, "path": path, "vlm_name": vlm_name, "ni_overall": ni_overall}
    #         temp_filename = os.path.join(res_dir, f"temp_{town}_{vlm_name}.json")
    #         with open(temp_filename, "w", encoding='utf-8') as f:
    #             json.dump(result, f, ensure_ascii=False, indent=2)
    #         print(f"Temporary result saved for {town}, {vlm_name}!")
    #         instructions.append({"town":town, "path":path, "vlm_name":vlm_name, "ni_overall":ni_overall})

    instructions = []
    for town in tqdm(['Town01', 'Town02', 'Town03', 'Town04', 'Town05', 'Town10']):
        path = "Path_1"
        for vlm_name in tqdm(['gpt-4o', 'claude-3-5-sonnet-20241022','gemini-2.0-flash-thinking-exp-01-21','minicpm-2-6-int4']):
            with open(os.path.join("results", f"temp_{town}_{vlm_name}.json"), "r") as f:
                data = json.load(f)
            instructions.append(data)

    with open(os.path.join("results", "overall_navigation_instructions.json"), "w") as f:
        json.dump(instructions,f,ensure_ascii=False, indent=2)
        print("File Saved!")


