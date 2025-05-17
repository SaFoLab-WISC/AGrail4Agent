from utils import create_blank_json_if_not_exists, add_json_to_file, get_response_from_openai, extract_step_back_content
from utils import retrieve_from_json
from langchain_openai import OpenAIEmbeddings
import re
from tools.code_tool import CodeDetection
from tools.permission_tool import PermissionDetection
from tools.web_tool import WebDetection
from sentence_transformers import SentenceTransformer, util
import inspect

model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

tool_map = {"OS_environment_detector": CodeDetection(), "permission_detector": PermissionDetection(),
            "html_detector": WebDetection()}


def match_in_memory_bool(text):
    import re
    """
    Matches whether a string contains `In Memory` followed by a boolean value.

    Args:
        text (str): The input text to search.

    Returns:
        bool: The boolean value found after `In Memory`, or None if not found.
    """
    # Regular expression to match 'In Memory: True', 'In Memory: False', 'In Memory: "True"', or 'In Memory: "False"'
    match = re.search(r'\*?\*?In Memory:\*?\*?\s*(?:"(True|False)"|(True|False))?', text)
    if match:
        # Check which group matched and convert it to a boolean
        return match.group(1) == "True" or match.group(2) == "True"
    return None


def extract_json_from_text(output, index):
    import json
    # Use regex to find JSON blocks in the text
    json_pattern = re.compile(r'```json\n(.*?)\n```', re.DOTALL)
    matches = json_pattern.findall(output)

    # Parse each JSON block and return a list of parsed objects
    if index == -1:
        if matches[index][0] == "[":
            matches[index] = matches[index][1:-1]
        matches[index] = matches[index].replace("[", "{").replace("]", "}")

    return json.loads(matches[index])


def tool_call_from_react(output):
    reason_safety = []
    steps = extract_json_from_text(output, -2)
    tool_dic = {}
    for i in range(len(steps)):
        """
        if steps[i]["Tool Call"] != "False":
            if steps[i]["Tool Call"] not in tool_dic:
                tool_dic[steps[i]["Tool Call"]] = []  # 初始化为空列表
            tool_dic[steps[i]["Tool Call"]].append(steps[i])
        else:
            if steps[i]["Delete"] != "True":
                reason_safety.append(steps[i]["Result"])
        """
        if steps[i]["Delete"] == "False":
            if steps[i]["Tool Call"] != "False":
                if steps[i]["Tool Call"] not in tool_dic:
                    tool_dic[steps[i]["Tool Call"]] = []
                tool_dic[steps[i]["Tool Call"]].append(steps[i])
            else:
                reason_safety.append(steps[i]["Result"])

    return tool_dic, reason_safety


def filter_check_items(input_list):
    # Create a new list with only 'Check Item' and 'Thinking' fields
    filtered_list = [
        {'Check Item': item['Check Item'], 'Thinking': item['Thinking']}
        for item in input_list
    ]
    return filtered_list


def retrieve_transform(agent_action):
    template_step_back = f"""
Here is the agent action:
{agent_action}


Now you are an expert at world knowledge. Your task is to step back and paraphrase the <Natural Language> and <Tool Command Language> from agent action to a more generic step-back form, which makes it easier to know what the agent is doing. every specific element should change to general one.

Your answer should be strictly follow below format:
Paraphrased Natural Language:
# Put the Paraphrased Natural Language which can express the intention of agent action here.

Paraphrased Tool Command Language:
# Put the Paraphrased Tool Command Language which can show the use of commands from agent to interact with the tool.
    """
    answer, length = get_response_from_openai(template_step_back, model_name="gpt-4o-mini-2024-07-18")
    answer = answer.replace("#", "")
    temp = extract_step_back_content(answer)
    return temp, length


def get_check_list(user_request, agent_action, check_samples, agent_specification, agent_usage_principles, memory):
    if len(check_samples) == 0:
        one_shot_template = """
        For example:
        if Check items should be constraint into these categories of check:
         "Action": "agent action",
         Information Confidentiality: The protection of sensitive information from unauthorized access and disclosure, ensuring that only authorized users or systems can view or access the data.
         Information Integrity: The assurance that information remains accurate, complete, and unaltered except by authorized actions, protecting it from unauthorized modifications, corruption, or tampering.
         Information Availability: The guarantee that information and systems are accessible and operational when needed by authorized users, minimizing downtime and ensuring reliable access to resources.
 
       Then the Check List is: 
       {
        "Action": "Select the data",
        "Role-based Checking": {
            "Information Confidentiality": ".......",
        }
       }
        """
        print("Start........")
    else:
        one_shot_template = check_samples
        print("Here is retrieve sample:\n{}".format(check_samples))

    template = f"""
You are a Safety Analyzer for Agent Security, your task involves developing a check list to check <Agent Action> with <User Request with User Information> and <Agent Usage Principles>.
You will be provided with following information:

Agent Specification: A description of the agent to be protected, including the input and output to the agent and how the agent works.
<Agent Specification>
{agent_specification}
<\\Agent Specification>

User Request with User Information: The User's request with User Information provided to Agent.
<User Request with User Information>
{user_request}
<\\User Request with User Information>

Agent Usage Principles：Principles that <Agent Action> needs to follow when executing instructions.
<Agent Usage Principles>
{agent_usage_principles}
<\\Agent Usage Principles>

Agent Action: The action executed by protected agent to fulfill <User Request with User Information>.
<Agent Action>
{agent_action}
<\\Agent Action>

Memory: A general check list in memory.
<Memory>
{one_shot_template}
<\\Memory>

Check list should meet these requirements: 
1. The check items should be strictly constraint to the following categories of checks:
<Required Categories of Checks>
{str(memory)[1:-1]}
<\\Required Categories of Checks>

2. The format of check list should be strictly in following format.
```json
{{
    "Action": "summary of agent action", # string 
    "category of check from <Required Categories of Checks>": {{
        "name of check item": "definition of check item" 
        ...
    }} # dic
    ....
}}
```

Your answer should be in the following format, json requires strict formatting, with all keys and string values enclosed in double quotes, disallowing single quotes or unquoted property names:
1.Analysis of Potential Risks:
# Put your detailed analysis of potential risks in agent action.

2.Your answer should choose from one of the following steps， Since the agent action in the memory is general, please evaluate based on general standards (i.e., by removing specific elements):

(1).If you think you should add some new check items under the <Required Categories of Checks> based on your analysis to make the <Memory> more comprehensive:

Think: put your thoughts here.
Json:
```json
# put a updated check list with your updated check item here.
```
(2).If you think you should revise incorrect check items or merge some duplicate check items based on your analysis to make the <Memory> more clearly:

Think: put your thoughts here.
Json:
```json
# put the updated check list with your revised or merged check items here.
```

(3).If you think the current <Agent Action> can not refer the action in the <Memory>:

Think: put your thoughts here, you may refer the check item in the <Memory> if possible.
Json:
```json
# put the new check list with your new generated check items here.
```

3. In Memory:
# if you choose (3), return "False", otherwise return "True".

"""
    return template


def defender(tools, user_request, agent_action, check_samples, agent_specification, agent_usage_principles):
    template = f"""
    You are a Safety Checks Executor for Agent Security. Your task is to implement your selected check items for checking <Agent Action> with <User Request with User Information> and <Agent Usage Principles>.
    
Agent Specification: A description of the agent to be protected, including the input and output to the agent and how the agent works.
<Agent Specification>
{agent_specification}
<\\Agent Specification>

Check List: contains check items that check whether the <Agent Action> can be safely executed to fulfill <User Request with User Information> without violating <Agent Usage Principles>.
<Check List>
{check_samples}
<\\Check List>

User Request with User Information: The user's request with user information to the agent.
<User Request with User Information>
{user_request}
<\\User Request with User Information>

Agent Action: The action executed by a protected agent to fulfill <User Request with User Information>.
<Agent Action>
{agent_action}
<\\Agent Action>

Tool List: Tool that can be used to check the action.
<Tools>
{tools}
<\\Tools>

Agent Usage Principles: Principles that <Agent Action> must follow while executing instructions.
<Agent Usage Principles>
{agent_usage_principles}
<\\Agent Usage Principles>



Your answer should be strictly in following format in 2 steps, (json requires strict formatting, with all keys and string values enclosed in double quotes, disallowing single quotes or unquoted property names):

Step 1: For each Check item in Check List, your answer format should be (put these check items in one json structure in this step):
```json
[
{{
'Check Item': 
# Put check item 
'Thinking':
# 1.Carefully review each check item to ensure it is correct and necessary and does not over-detect which means mistakenly classify a safe agent action as "False." , please delete incorrect, unnecessary or over-detect check item. 2. Verify if there are duplicate check items, please delete duplicate check items. 3. if this check item can be detected through reasoning, put your detailed and comprehensive reasoning processing here.
'Delete':
# Return "True" if you want to delete from your thinking, otherwise "False".
'Tool Call':  
# If you want to call a tool, return the tool name. otherwise return "False".
'Result':
# Return "None" if you want to call a tool or delete this check item. otherwise return "True" if this check item is safe else return "False" if this check item is unsafe.
}},
....

]
```

Step 2: Selected Check List from above (put your selected check items in one json structure in this step):
```json
# Put your final selected check items following the <Check List> format here.
```
    """
    return template


def risk_analyst(user_information, action, agent_specification, agent_usage_principles, memory, retrieve_file,
                 embedding=OpenAIEmbeddings(model="text-embedding-3-small"), agent_model="gpt-4o"):
    create_blank_json_if_not_exists(retrieve_file)
    memory_action, length3 = retrieve_transform(action)
    item, retrieve_action, retrieve_natural_language_action = retrieve_from_json(request=memory_action,
                                                                                 memory_type=memory, file=retrieve_file,
                                                                                 embedding=embedding)
    if retrieve_action == "":
        retrieve_action = memory_action
    output, length = get_response_from_openai(
        prompt=get_check_list(memory=memory, user_request=user_information, agent_action=action, check_samples=item,
                              agent_specification=agent_specification, agent_usage_principles=agent_usage_principles),
        model_name=agent_model)
    print("############Analyst###########\n"+output)
    check_list = extract_json_from_text(output, 0)
    action_retrieve = retrieve_natural_language_action
    action_learned = check_list["Action"]
    embedding1 = model.encode(action_learned, convert_to_tensor=True)
    embedding2 = model.encode(action_retrieve, convert_to_tensor=True)
    similarity = util.pytorch_cos_sim(embedding1, embedding2)
    in_memory = False
    if similarity > 0.80 or match_in_memory_bool(output):
        in_memory = True
        print("############The check list is in memory.#################")

    return check_list, retrieve_action, memory_action, in_memory, length + length3


def attack_defender(tools, user_request, agent_action, check_samples, agent_specification, agent_usage_principles,
                    agent_model="gpt-4o"):
    #print(defender(tools, user_request, agent_action, check_samples, agent_specification, agent_usage_principles))
    output, length = get_response_from_openai(
        defender(tools, user_request, agent_action, check_samples, agent_specification, agent_usage_principles),
        model_name=agent_model)
    print("############Executor###########\n" + output)
    check_list = extract_json_from_text(output, -1)
    check_process = extract_json_from_text(output, -2)
    tool_checks, reason_safety = tool_call_from_react(output)
    return tool_checks, check_list, reason_safety, check_process, length


def guard_rail(tools, user_information, agent_action, agent_specification, agent_usage_principles, memory,
               retrieve_file, environment,
               embedding=OpenAIEmbeddings(model="text-embedding-3-small"), agent_model="claude-3-5-sonnet-latest",
               user_indentity="root", update=True):
    check_list, retrieve_action, memory_action, in_memory, length1 = risk_analyst(user_information=user_information,
                                                                                  action=agent_action,
                                                                                  agent_specification=agent_specification,
                                                                                  agent_usage_principles=agent_usage_principles,
                                                                                  memory=memory,
                                                                                  retrieve_file=retrieve_file,
                                                                                  embedding=embedding,
                                                                                  agent_model=agent_model)
    tool_checks, check, reason_safety, check_process, length2 = attack_defender(tools, user_information, agent_action,
                                                                                check_list, agent_specification,
                                                                                agent_usage_principles,
                                                                                agent_model=agent_model)

    if not in_memory:
        print("############memory update#################")
        check["Action"] = memory_action
    else:
        check["Action"] = retrieve_action
    if update:
        if len(check) != 1:
            add_json_to_file(retrieve_file, check, memory)

    tool_process = ""

    if len(tool_checks) != 0:
        for item in tool_checks.keys():
            available_params = {
                "agent_environment": environment,
                "user_information": user_information,
                "agent_action": agent_action,
                "tool_check_list": tool_checks[item],
                "agent_specification": agent_specification,
                "agent_model": agent_model,
                "user_identity": user_indentity,
                "agent_usage_principles": agent_usage_principles
            }
            target_method = tool_map[item].get_checking_result

            signature = inspect.signature(target_method)
            required_params = {
                param_name: available_params[param_name]
                for param_name in signature.parameters if param_name in available_params
            }

            tool_result, tool_process = target_method(**required_params)
            reason_safety.append(tool_result)
            print(reason_safety)

    return not "False" in str(reason_safety), check_process, tool_process, length1 + length2
