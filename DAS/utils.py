import json
import os
import docker
import struct
import socket
import re
import io
import tarfile
from typing import List, Callable, Tuple
from openai import OpenAI
from langchain_community.document_loaders import JSONLoader
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
import os
os.environ["ANTHROPIC_API_KEY"] = ""#Your api key.
os.environ["OPENAI_API_KEY"] = ""#Your api key.


def format_dic_to_stry(dic):
    stry = "{\n"
    for key, value in dic.items():
        stry += f"    {key}: {value},\n"
    stry += "}"
    return stry


def retrieve_from_json(request, memory_type, file, embedding=OpenAIEmbeddings(model="text-embedding-3-small")):
    def metadata_func(record: dict, metadata: dict) -> dict:
        for key in memory_type.keys():
            metadata[key] = str(record.get(key))

        return metadata

    loader = JSONLoader(
        file_path=file,
        jq_schema='.[]',
        text_content=False,
        metadata_func=metadata_func
    )
    try:
        data = loader.load()
    except Exception as e:
        print("No data found in file, we will use start setting...")
        return "", "", ""
    vectorstore = Chroma.from_documents(documents=data, embedding=embedding)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 1})
    retrieve_docs_list = retriever.invoke(request)
    retrieve_info = {}
    knowledge_template = ""
    retrieve_action = ""
    retrieve_natural_language_action = ""
    for i in range(len(retrieve_docs_list)):
        for key in memory_type.keys():
            if key == "Action":
                retrieve_action = retrieve_docs_list[i].metadata[key]
                retrieve_natural_language_action = \
                retrieve_docs_list[i].metadata[key].split(", Tool Command Language:")[0].replace("Natural Language:",
                                                                                                 "").strip()
                retrieve_info[key] = retrieve_natural_language_action
            else:
                retrieve_info[key] = retrieve_docs_list[i].metadata[key]
        template = format_dic_to_stry(retrieve_info)
        knowledge_template = knowledge_template + template
        break
    return knowledge_template, retrieve_action, retrieve_natural_language_action



def get_response_from_openai(prompt, model_name="gpt-4o"):
    length = 0 # you can use to calculate token cost.
    if "gpt" in model_name:
        print("GPT loading {}...".format(model_name))
        client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        completion = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": f"""{prompt}"""}],
        )
        response = completion.choices[0].message.content

    else:
        print("Cluade loading {}...".format(model_name))
        import anthropic

        client = anthropic.Anthropic(api_key = os.environ["ANTHROPIC_API_KEY"])

        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=8192,
            temperature=0,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"{prompt}"
                        }
                    ]
                }
            ]
        )
        response = next(
            (block.text for block in message.content if hasattr(block, "text")),
            None,
        )
    return response, length


def extract_step_back_content(text):
    natural_language_pattern = r"Paraphrased Natural Language:\s*(.+)"
    tool_command_language_pattern = r"Paraphrased Tool Command Language:\s*(.+)"

    natural_language_match = re.search(natural_language_pattern, text)
    tool_command_language_match = re.search(tool_command_language_pattern, text)

    natural_language = natural_language_match.group(1).strip() if natural_language_match else None
    tool_command_language = tool_command_language_match.group(1).strip() if tool_command_language_match else None

    template = f"""Natural Language:{natural_language[:]}, Tool Command Language:{tool_command_language[:]}"""
    template = template.replace("#", "")
    return template


def detect_python_error(log: str) -> bool:
    error_indicators = [
        "Traceback (most recent call last):",
        "Error",
        "Exception",
        "SyntaxError"
    ]
    return any(indicator in str(log) for indicator in error_indicators)


def extract_json_content(text):
    # Find all JSON content using a more flexible regex pattern
    pattern = r'```json\s*(.*?)\s*```'
    json_matches = re.findall(pattern, text, re.DOTALL)

    if json_matches:
        # Extract the last JSON match
        json_content = json_matches[-1].strip()  # Remove any extra whitespace

        try:
            # Parse the JSON string
            parsed_json = json.loads(json_content)
            return parsed_json
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")
            return None
    else:
        print("No JSON content found.")
        return None


def add_json_to_file(file_path, add_data, structure_file):
    """
    Adds new JSON data to an existing JSON file or creates the file if it doesn't exist.
    If an entry with the same 'Operation' key exists, it replaces it.

    Parameters:
    - file_path: str, the path to the JSON file.
    - add_data: dict, the parsed JSON data to be added.

    The function reads the existing content of the file, checks for duplicate operations,
    updates or appends the new data, and writes it back to the file.
    """
    new_data = add_data.copy()
    keys_to_remove = [item for item in new_data.keys() if item not in structure_file.keys()]
    for item in keys_to_remove:
        del new_data[item]

    try:
        if os.path.exists(file_path):
            # Load the existing data from the file if it exists
            with open(file_path, 'r') as file:
                try:
                    existing_data = json.load(file)
                    # Ensure existing data is a list
                    if not isinstance(existing_data, list):
                        existing_data = [existing_data]
                except json.JSONDecodeError:
                    existing_data = []
        else:
            existing_data = []

        # Check for existing entry with the same 'Operation'
        updated = False
        for i, entry in enumerate(existing_data):
            if entry.get('Action') == new_data.get('Action'):
                existing_data[i] = new_data
                updated = True
                break

        if not updated:
            # Append the new data if no matching 'Operation' was found
            existing_data.append(new_data)

        # Write the updated data back to the file
        with open(file_path, 'w') as file:
            json.dump(existing_data, file, indent=4)

    except Exception as e:
        print(f"Error while adding JSON data to file: {e}")


import os
import json

def create_blank_json_if_not_exists(file_path):
    if not os.path.isfile(file_path):
        with open(file_path, 'w') as file:
            json.dump([{}], file)  # 创建一个包含一个空字典的列表
        print(f'{file_path} created successfully.')
    else:
        print(f'{file_path} already exists.')



def extract_content(text, content, n=-1):
    # Find the JSON content using a more flexible regex pattern
    pattern = r'```{content}\s*(.*?)\s*```'.format(content=content)
    code_match = re.findall(pattern, text, re.DOTALL)
    if code_match:
        # Extract the JSON part
        code_content = code_match[n].strip()  # Remove any extra whitespace
        return code_content
    else:
        print("No content found.")
        return None


def capture_bool_from_string(log_str):
    match = re.search(r'(True|False)(?!.*(True|False))', log_str)

    if match:
        return match.group(0)
    else:
        return None


class Container:
    def __init__(self):
        self.client = docker.from_env()
        self.container: docker.models.containers.Container = self.client.containers.run(
            "ubuntu", detach=True, tty=True, stdin_open=True, remove=True,
            labels={"created_by": "os-pipeline"}
        )
        self.exec_id = self.client.api.exec_create(self.container.id, "bash --login", stdin=True, tty=True)["Id"]
        self.sock = self.client.api.exec_start(self.exec_id, socket=True)._sock
        self.sock.settimeout(5)
        # Install Python in the container
        # self._send_command("apt update && apt install -y python3 python3-pip")
        # Clear buffer
        self.sock.recv(1000)

    def __del__(self):
        try:
            self.container.stop()
        except:
            pass

    def _send_command(self, command):
        self.sock.send(command.encode("utf-8") + b'\n')
        data = self.sock.recv(8)
        _, n = struct.unpack('>BxxxL', data)
        self.sock.recv(n)

    def execute(self, command: str, user: str):
        class DummyOutput:
            output: bytes
            exit_code: int

            def __init__(self, code, o):
                self.output = o
                self.exit_code = code

        if not isinstance(command, str):
            return DummyOutput(-1, b'')

        self._send_command(command)
        output = b''
        while True:
            try:
                data = self.sock.recv(8)
                if not data:
                    break
                _, n = struct.unpack('>BxxxL', data)
                line = self.sock.recv(n)
                output += line
                if re.search(b"\x1b.+@.+[#|$] ", line):
                    break
            except (TimeoutError, socket.timeout):
                break
        return DummyOutput(0, output)

    def execute_independent(self, command, user, *params):
        # print("=== EXECUTING INDEPENDENT ===\n", command)
        language, command = command
        # if params:
        #     print("== Parameters ==\n", params)
        if language == "bash":
            cmd = ["bash", "-c", command]
            if params:
                cmd.append("--")
                cmd.extend(params)
        elif language == "python":
            cmd = ["python3", "-c", command, *params]
        elif language == "c++":
            self.execute_independent(("bash", f"echo \"{json.dumps(command)}\" > /tmp/main.cpp && "
                                              f"g++ -o /tmp/a.out /tmp/main.cpp"), None)
            cmd = ["/tmp/a.out", *params]
        elif language == "c":
            self.execute_independent(("bash", f"echo \"{json.dumps(command)}\" > /tmp/main.cpp && "
                                              f"gcc -o /tmp/a.out /tmp/main.cpp"), None)
            cmd = ["/tmp/a.out", *params]
        else:
            raise ValueError("Unsupported language")
        return self.container.exec_run(cmd, user=user)

    def put_file(self, file_content: str, file_name: str):
        tar_stream = io.BytesIO()
        with tarfile.open(fileobj=tar_stream, mode='w') as tar:
            file_data = io.BytesIO(file_content.encode('utf-8'))
            tar_info = tarfile.TarInfo(name=file_name)
            tar_info.size = len(file_content)
            tar.addfile(tarinfo=tar_info, fileobj=file_data)
        tar_stream.seek(0)

        # Put the archive to the container
        self.container.put_archive('/tmp', tar_stream.getvalue())

    def run_file(self, file_path: str, user: str):
        test = self.container.exec_run(f"whoami", user=user)
        print(test.output.decode('utf-8'))
        result = self.container.exec_run(f"python3 {file_path}", user=user)
        return result

class JudgeConfig:
    image: str = None
    init_script: List[Tuple[str, str]] = None
    start: Tuple[str, str] = None
    description: str


class SessionExeption(Exception):
    pass


class Session:
    def __init__(self, model_inference, history=None) -> None:
        self.history: list[dict] = history or []
        self.exception_raised = False
        self.model_inference = self.wrap_inference(model_inference)

    def inject(self, message: dict) -> None:
        assert isinstance(message, dict)
        assert "role" in message and "content" in message
        assert isinstance(message["role"], str)
        assert isinstance(message["content"], str)
        assert message["role"] in ["user", "agent"]
        self.history.append(message)

    def action(self, extend_messages: List[dict] = None):
        extend = []
        environment = None
        if extend_messages:
            if isinstance(extend_messages, list):
                print("######：" + str(extend_messages))
                extend.extend(extend_messages)
            elif isinstance(extend_messages, dict):
                print("######：" + str(extend_messages))
                extend.append(extend_messages)
            else:
                raise Exception("Invalid extend_messages")
        result = self.model_inference(self.history + extend)
        temp = next(reversed(self.history))
        last_item = ""
        if temp["content"].startswith("The output of the OS"):
            last_item = temp["content"]
        self.history.extend(extend)
        self.history.append({"role": "agent", "content": result})
        print("#####" + last_item)
        return last_item, result

    def wrap_inference(self, inference_function: Callable[[List[dict]], str]) -> Callable[[List[dict]], str]:
        def _func(history: List[dict]) -> str:
            if self.exception_raised:
                return ""
            try:
                result = inference_function(history)
            except Exception as e:
                print(e)
                import traceback
                traceback.print_exc()
                print("Warning: Exception raised during inference.")
                self.exception_raised = True
                result = ""
            return result

        return _func

class Agent:
    def __init__(self, model_name) -> None:
        self.name = model_name

    def create_session(self) -> Session:
        return Session(self.inference)

    def inference(self, History: List[dict]) -> str:
        history = History
        for h in history:
            if h['role'] == 'agent':
                h['role'] = 'assistant'

        client = OpenAI(
            api_key=os.environ["OPENAI_API_KEY"])
        completion = client.chat.completions.create(
            model="gpt-4-turbo",  # model = "deployment_name".
            messages=history,
        )

        return completion.choices[0].message.content
