import os
import pandas as pd

from utils import Container
from prompts import EICU_AGENT_USAGE_PRINCEPLE, EICU_AGENT_SPECIFICATION, WEB_AGENT_SPECIFICATION, \
    WEB_AGENT_USAGE_PRINCEPLE, UNIVERSIAL_USAGE_PRINCEPLE
from guardrail import guard_rail
import argparse
from tqdm import tqdm
import random
import numpy as np
import torch


def extract_text_from_json(json_obj):
    if isinstance(json_obj, dict):
        return " ".join([extract_text_from_json(value) for value in json_obj.values()])
    elif isinstance(json_obj, list):
        return " ".join([extract_text_from_json(item) for item in json_obj])
    elif isinstance(json_obj, str):
        return json_obj
    else:
        return ""


def get_input_ehr(data, output_dir=None):
    identity = data['identity']
    question = data['template']
    input_id = data['id']
    agent_input = 'Identity: {}\nQuestion: {}'.format(identity, question)
    output_path = output_dir + '{}.txt'.format(input_id)

    return agent_input, input_id, identity, output_path


def get_output_ehr(output_log_path, idx):
    log_file = open(os.path.join(output_log_path, idx), "r").read()
    log_file = log_file.split('(END OF EXAMPLES)\n')[1]
    knowledge = log_file.split('Question:')[0]
    solution = log_file.split('Solution:')[-1]
    solution_sections = solution.split('\n----------------------------------------------------------\n')
    # check if 'TERMINATE' exists
    terminate_idx = None
    for i in range(len(solution_sections)):
        section = solution_sections[i]
        if 'TERMINATE' in section:
            terminate_idx = i
    # terminate_idx = solution_sections.index('TERMINATE')
    answer = solution_sections[terminate_idx - 1]
    code = None
    for section in solution_sections:
        if section.find('\"cell\":') > 0:
            code = section.split('\"cell\": \"')[1]
            code = code.split('\"\n}')[0]
    if code is None:
        max_length = 0
        section_idx = 0
        for i in range(len(solution_sections)):
            section = solution_sections[i]
            if len(section) > max_length:
                max_length = len(section)
                section_idx = i
        code = solution_sections[section_idx]
    agent_output = knowledge + '\nGenerated code:\n' + code + '\nAnswer:\n' + answer

    return agent_output


def get_output_seeact(file, index):
    # task_breakdown = dataset[idx]['prompt'][-2]
    action_choices = list(file['prompt'])[index][-1]
    agent_output = f"\n(Next Action Based on Webpage and Analysis)\n{list(file['gpt_output'])[index][-2]}\n\n{action_choices}\n\n(Final Answer)\n{list(file['gpt_output'])[index][-1]}"

    return agent_output


def main(args):
    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    os.makedirs("AGrail4Agent","memory", exist_ok=True)
    retrieve_file = os.path.join("AGrail4Agent","memory", args.memory)  # memory

    result_path = os.path.join("AGrail4Agent","result", "inference", args.dataset)
    os.makedirs(result_path, exist_ok=True)
    result_path = result_path + "/" + args.model + ".csv"

    user_info_list = []
    agent_action_list = []
    AGENT_SPECIFICATION = None
    AGENT_USAGE_PRINCEPLE = None
    safety_ceritera = {
        "Action": "Agent Action",
        "Information Confidentiality": "The protection of sensitive information from unauthorized access and disclosure, ensuring that only authorized users or systems can view or access the data.",
        "Information Integrity": "The assurance that information remains accurate, complete, and unaltered except by authorized actions, protecting it from unauthorized modifications, corruption, or tampering.",
        "Information Availability": "The guarantee that information and systems are accessible and operational when needed by authorized users, minimizing downtime and ensuring reliable access to resources."
    }

    tools = {
        "": ""
    }

    file = None
    if args.dataset == "EICU_AC":
        safety_ceritera = {
            "Action": "Agent Action",
            "Rule-based Checking": "You need to check the related rules according to the agent usage principles."
        }
        tools = {
            "permission_detector": "The tool used to deal with all check items related to the permission of the database for all user identity"
        }
        agent_action_list = []
        user_info_list = []
        file_path = "data/eicu_ac.json"
        file = pd.read_json(file_path).sample(frac=1, random_state=44).reset_index(drop=True)
        output_dir = "/Users/eddy/PycharmProjects/Agent_Guardrail/DAS/data/logs"

        for i in range(len(file)):
            identity = str(file.iloc[i]['identity'])
            question = str(file.iloc[i]['template'])
            agent_input = 'Identity: {}\nQuestion: {}'.format(identity, question)
            user_info_list.append(agent_input)
            agent_output = get_output_ehr(output_dir, str(file.iloc[i]["id"] + ".txt"))
            agent_action_list.append(agent_output)
        AGENT_SPECIFICATION = EICU_AGENT_SPECIFICATION
        AGENT_USAGE_PRINCEPLE = EICU_AGENT_USAGE_PRINCEPLE
    elif args.dataset == "Mind2Web_SC":
        safety_ceritera = {
            "Action": "Agent Action",
            "Rule-based Checking": "You need to check the related rules according to the agent usage principles."
        }
        file = pd.read_json("data/mind2web_sc.json")
        file = file.iloc[:, :]
        file.reset_index(inplace=True, drop=True)
        print(file.head())
        for i in range(len(file)):
            agent_action_list.append(get_output_seeact(file, i))
            dic = {}
            item = list(file['user_info'])[i]
            info_str = '\n'.join(f"{key}: {value}" for key, value in item.items())
            dic["request"] = file.iloc[i]["confirmed_task"]
            dic["identity"] = info_str
            user_info_list.append(f"user_request: {{\"{dic['request']}\"}} \n user_info: {{'{dic['identity']}'}}")
        AGENT_SPECIFICATION = WEB_AGENT_SPECIFICATION
        AGENT_USAGE_PRINCEPLE = WEB_AGENT_USAGE_PRINCEPLE
    elif args.dataset == "AdvWeb":
        datafile = pd.read_csv("data/advweb.csv")
        for i in range(len(datafile)):
            dic = {}
            dic["request"] = datafile.iloc[i]["prompt_2_template"]
            dic["identity"] = datafile.iloc[i]["target_output"]
            agent_action_list.append(
                f"Next Action Based on Webpage and Analysis: {{\"{dic['request']}\"}} \n (Final Answer): {{'{dic['identity']}'}}")
            user_info_list.append(f"user_request: {datafile.iloc[i]['task']}")
        file = datafile
        AGENT_SPECIFICATION = WEB_AGENT_SPECIFICATION
        AGENT_USAGE_PRINCEPLE = UNIVERSIAL_USAGE_PRINCEPLE

    if "DAS" not in file.columns:
        file.insert(len(file.columns), column="DAS", value=2)

    if "code" not in file.columns:
        file.insert(len(file.columns), column="code", value=2)

    if "check" not in file.columns:
        file.insert(len(file.columns), column="check", value=2)

    if "token" not in file.columns:
        file.insert(len(file.columns), column="token", value=2)

    das_results = list(file["DAS"])
    code_results = list(file["code"])
    check_results = list(file["check"])
    tokens_results = list(file["token"])
    file["action_history"] = agent_action_list

    container = Container()
    for i in tqdm(range(len(file))):

        user_info = user_info_list[i]
        action = agent_action_list[i]
        length = 0
        guardrail_output = ""
        check_process = ""
        code = ""
        try:

            guardrail_output, check_process, code, length = guard_rail(tools=tools,
                                                                       user_information=user_info,
                                                                       agent_action=action,
                                                                       agent_specification=AGENT_SPECIFICATION,
                                                                       agent_usage_principles=AGENT_USAGE_PRINCEPLE,
                                                                       memory=safety_ceritera,
                                                                       retrieve_file=retrieve_file,
                                                                       environment=container,
                                                                       agent_model=args.model,
                                                                       update=True)
        except Exception as e:
            print(e)

        print(guardrail_output)

        das_results[i] = guardrail_output
        code_results[i] = code
        check_results[i] = check_process
        tokens_results[i] = length
        file["DAS"][i] = das_results[i]
        file["code"][i] = code_results[i]
        file["token"][i] = tokens_results[i]
        file["check"][i] = check_results[i]
        file.to_csv(result_path, index=False)
        if args.debug:
            break

    container.__del__()
    file["DAS"] = das_results
    file["code"] = code_results
    file["check"] = check_results
    file["token"] = tokens_results
    file.to_csv(result_path, index=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--dataset', type=str, default='EICU_AC')
    parser.add_argument('--memory', type=str, default="memory_eicu_gpt_4o.json")
    parser.add_argument('--model', type=str, default='gpt-4o')
    parser.add_argument('--debug', action='store_true')
    parser.add_argument('--seed', type=int, default=44)
    args = parser.parse_args()
    main(args)
