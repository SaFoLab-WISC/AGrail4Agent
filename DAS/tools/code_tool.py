from .tool import Tools
from DAS.utils import extract_content, capture_bool_from_string, detect_python_error, get_response_from_openai


class CodeDetection(Tools):
    def __init__(self):
        super().__init__()

    @staticmethod
    def generator(user_information, agent_action, tool_checks,
                  agent_specification, agent_usage_principles):
        template = f"""
            You are a code generator for Agent Security. Your task is to provide a Python program that implements your the check items for checking <Agent Action> with <User Request with User Information> and <Agent Usage Principles>.

        Agent Specification: A description of the agent to be protected, including the input and output to the agent and how the agent works.
        <Agent Specification>
        {agent_specification}
        <\\Agent Specification>

        Check List: contains check items that check whether the <Agent Action> can be safely executed to fulfill <User Request with User Information> without violating <Agent Usage Principles>.
        <Check List>
        {tool_checks}
        <\\Check List>

        User Request with User Information: The user's request with user information to the agent.
        <User Request with User Information>
        {user_information}
        <\\User Request with User Information>

        Agent Action: The action executed by a protected agent to fulfill <User Request with User Information>.
        <Agent Action>
        {agent_action}
        <\\Agent Action>

        Agent Usage Principles: Principles that <Agent Action> must follow while executing instructions.
        <Agent Usage Principles>
        {agent_usage_principles}
        <\\Agent Usage Principles>


        Here is the Code Generation Rule:
        <Code Generation Rule>
        1. This code should be used solely for checking purposes and should not perform any <Agent Action>.
        2. It should print "True" only if all checks are successful; otherwise, it should print "False" without any additional output.
        3. The code should include annotation to aid in debugging.
        4. Do not use try-except to handle errors; let the errors throw naturally.
        <\\Code Generation Rule>
        
        Here is the code book you can refer:
        <Code Book>
        1. check user identity: os.getpid()
        2. check path permission: os.chdir(path)
        3. check file permission: os.access(path, os.R_OK), os.access(path, os.W_OK), os.access(path, os.X_OK)
        4. the existence of file: os.path.exists(path)
        <\\Code Book>

        Your answer format should be as follows format:
        Demonstration of check items:
        # Put your thinking in one line contains: 1. Carefully review each check item to ensure it is correct and does not over-detect, i.e., mistakenly classify a safe agent action as "False." If such behavior is found, delete the check item. 2. Verify if there are duplicate check items, and consolidate them if present. If yes, delete. 
        
        Select check items:
        ```JSON
        # Put the Select Check Items follow <Check List> format.
        ```

        Detailed Code Generation:
        ```python
        # End with:
        if __name__ == "__main__":
            print(main()) #only print True or False. 
        ```
            """
        return template

    @staticmethod
    def code_debug(code, tool_checks, error, user_information, agent_action, agent_usage_principles):
        template = f"""

        You are a code debugger for Agent Security. Your task is to fix the bug of the checking program with a detailed and specific check list that includes code implementation details for checking <Agent Action> based on the given information.


        User Request with User Information: The User's request with User's Information to Agent.
        <User Request with User Information>
        {user_information}
        <\\User Request with User Information>

        Agent Action: The action to fulfill <User Request with User Information>.
        <Agent Action>
        {agent_action}
        <\\Agent Action>

        Agent Usage Principles: Principles that <Agent Action> must to follow while executing instructions.
        <Agent Usage Principles>
        {agent_usage_principles}
        <\\Agent Usage Principles>

        Here is the check list:
        <Check List>
        {tool_checks}
        <\\Check List>


        The code is as follows:
        {code}

        The execution result is:
        {error}


        Please fix the bug and return you fixed code.

        Your answer should be in following format:

        Error Analyze:
        # put your error analyze here.

        Fixed Code:
        ```python
        # Put your fixed code here.
        # Your code only returns one "True" if all check items pass, "False" otherwise.
        # End with:
        if __name__ == "__main__":
            print(main()) #only print True or False. 

        ```

            """
        return template

    def code_debugger(self, code, check_list, error, user_info, agent_action, agent_principles, agent_model):
        template = self.code_debug(code, check_list, error, user_info, agent_action, agent_principles)
        output,_ = get_response_from_openai(prompt=template, model_name=agent_model)
        code = extract_content(output, "python")
        return code

    def get_checking_result(self, agent_environment, user_information, agent_action, tool_check_list, agent_specification, agent_usage_principles, agent_model, user_identity):
        guardrail_output = "None"
        code = None
        while capture_bool_from_string(guardrail_output) is None:
            output,_ = get_response_from_openai(
                self.generator(user_information, agent_action, tool_check_list, agent_specification,
                               agent_usage_principles), agent_model)
            print(output)
            code = extract_content(output, "python")
            check_list = extract_content(output, "JSON")
            # Save the code to a .py file
            agent_environment.put_file(code, 'code.py')
            # Execute the Python file in the container
            guardrail_result = agent_environment.run_file('/tmp/code.py', user=user_identity)
            print(guardrail_result)
            guardrail_output = guardrail_result.output.decode('utf-8')
            while detect_python_error(guardrail_output):
                print("Debugging...")
                code = self.code_debugger(code, check_list, guardrail_output, user_information, agent_action,
                                          agent_usage_principles,
                                          agent_model=agent_model)
                print(code)
                print(user_identity)
                agent_environment.put_file(code, 'code.py')
                # Execute the Python file in the container
                guardrail_result = agent_environment.run_file('/tmp/code.py', user=user_identity)
                print(guardrail_result)
                guardrail_output = guardrail_result.output.decode('utf-8')

        return capture_bool_from_string(guardrail_output), code
