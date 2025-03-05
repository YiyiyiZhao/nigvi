import os
import base64
import requests
from openai import OpenAI
import json
import pdb


class VLMRequester:
    def __init__(self, model_name):
        self.model_name = model_name

        if 'gpt' in self.model_name:
            self.gpt_api_key = os.environ.get("OPENAI_API_KEY")
            self.gpt_base_url = os.environ.get("OPENAI_BASE_URL")
        elif 'claude' in self.model_name:
            self.claude_api_key = os.environ.get("ANTHROPIC_API_KEY")
            self.claude_base_url = os.environ.get("ANTHROPIC_BASE_URL")
        elif 'gemini' in self.model_name:
            self.gemini_api_key = os.environ.get("GEMINI_API_KEY")
            self.gemini_base_url = os.environ.get("GEMINI_BASE_URL")
        elif 'minicpm' in self.model_name:
            self.local_url = "http://127.0.0.1:5000/ask"
        else:
            print("Please check the VLM's name!")

        self.template_overall = """Please generate the navigation instruction for visually impaired users based on the provided BVE image and the following path information:{}Output only the final navigation instruction for the overall trajectory, without any other words."""

        # ToDo
        self.template_step = """Please generate the navigation instruction for visually impaired for next step based on the informatino..."""

    def encode_image(self, image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    def request_remote(self, image_path, question_type, trajectory_info=None, step_info=None):
        if 'gpt' in self.model_name:
            base_url = self.gpt_base_url
            api_key = self.gpt_api_key
        elif 'claude' in self.model_name:
            base_url = self.claude_base_url
            api_key = self.claude_api_key
        elif 'gemini' in self.model_name:
            base_url = self.gemini_base_url
            api_key = self.gemini_api_key
        else:
            return
        if question_type == 'overall':
            query = self.template_overall.format(trajectory_info)
        else:
            query = self.template_step.format(step_info)

        # Getting the base64 string
        base64_image = self.encode_image(image_path)
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

        payload = {
            "model": self.model_name,
            "messages": [{"role": "user",
                          "content": [{"type": "text", "text": query},
                                      {"type": "image_url",
                                       "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                                      ]
                          }
                         ],
            "max_tokens": 512
        }
        response = requests.post(base_url + "/chat/completions", headers=headers, json=payload)
        tmp = response.json()
        if tmp['choices'][0]['message']['content']:
            result = tmp['choices'][0]['message']['content']
        else:
            result = ''
        return result

    def request_local(self, image_path, question_type, trajectory_info=None, step_info=None):
        url = self.local_url
        base64_image = self.encode_image(image_path)
        if question_type == 'overall':
            query = self.template_overall.format(trajectory_info)
        else:
            query = self.template_step.format(step_info)
        data = {
            "image": base64_image,
            "question": query
        }
        headers = {'Content-Type': 'application/json'}
        response = requests.post(url, data=json.dumps(data), headers=headers)
        tmp = response.json()
        res = tmp['response']
        return res

    def request(self, image_path, question_type, trajectory_info=None, step_info=None):
        if 'minicpm' in self.model_name:
            return self.request_local(image_path, question_type, trajectory_info=trajectory_info, step_info=step_info)
        else:
            return self.request_remote(image_path, question_type, trajectory_info=trajectory_info, step_info=step_info)



if __name__ == "__main__":
    # Path to your image
    image_path = "../data/Town01/Path_1/town01.png"
    trajectory_info = """
    The destination is in the NorthEast direction from the starting point.
    The approximate walking distance of this path is about 267 meters.
    Along the way, the path is segmented into 4 distinct sections.
    Segment 1 heads towards the 0 o'clock direction for approximately 29 meters, then
    Segment 2 heads towards the 11 o'clock direction for approximately 95 meters, then
    Segment 3 heads towards the 10 o'clock direction for approximately 88 meters, then
    Finally, the last segment, Segment 4, guides the path towards the 9 o'clock direction, with a length of around 45 meters.
    """

    vlm_req = VLMRequester()
    # res = vlm_req.request('gpt-4o', image_path, 'overall', trajectory_info)
    # print(res)

    res = vlm_req.request_local('minicpm', image_path, 'overall', trajectory_info)
    print(res)

    # response--gpt-4o
    # "Start by heading straight in front of you for 29 meters, slightly veer left and continue for 95 meters,
    # veer left again and proceed for 88 meters, then make a final left turn and walk 45 meters to reach your destination."

    # response--claude-3-5-20241022
    # Head 29 meters forward, turn slightly left and proceed 95 meters, then turn a bit more left and continue 88 meters, finally turn slightly left again and walk 45 meters to reach your destination.

    # response--gemini-2.0-flash-thinking-exp-01-21
    # Walk approximately 267 meters towards the Northeast, first at 0 o'clock for 29 meters, then at 11 o'clock for 95 meters, then at 10 o'clock for 88 meters, and finally at 9 o'clock for 45 meters.

    # Grok-3
    # Start by walking straight ahead for 29 meters, then veer slightly left and continue for 95 meters. Next, adjust slightly more left and walk for 88 meters. Finally, turn left and proceed for 45 meters to reach your destination, approximately 267 meters northeast from the starting point.

    # miniCPM

    # microsoft/Phi-4-multimodal-instruct
    # to walk in the north-east direction

    # MiniCPM-2.6-Int4
    # Start, walk 29 meters North, turn right and walk 95 meters East, turn left and walk 88 meters South, turn right and walk 45 meters West.
