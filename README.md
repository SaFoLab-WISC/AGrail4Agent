<p align="center">
    <img src="icon.png" width="150"/>
<p>

<h2 align="center"> <a>⛓‍💥 AGrail: A Lifelong Agent Guardrail with Effective and Adaptive Safety Detection</a></h2>
<h5 align="center"> If you like our project, please give us a star ⭐ on GitHub for latest update.  </h2>

<h5 align="center">

[Weidi Luo](https://eddyluo1232.github.io/), [Shenghong Dai](https://scholar.google.com/citations?user=GUarSlcAAAAJ&hl=en), [Xiaogeng Liu](https://xiaogeng-liu.com/), [Suman Banerjee](https://pages.cs.wisc.edu/~suman/), [Huan Sun](https://u.osu.edu/ihudas/people/), [Muhao Chen](https://muhaochen.github.io/), [Chaowei Xiao](https://xiaocw11.github.io/)

[![arxiv](https://img.shields.io/badge/Arxiv-2502.11448-red)](https://arxiv.org/abs/2502.11448)
[![project](https://img.shields.io/badge/Project-Page-blue)](https://eddyluo1232.github.io/AGrail/)
![Defenses](https://img.shields.io/badge/Agent-Guardrail-green)


**<font color='red'>Warning: This repo contains examples of harmful agent action, and reader discretion is recommended.</font>**




## 💡 Abstract
The rapid advancements in Large Language Models (LLMs) have enabled their deployment as autonomous agents for handling complex tasks in dynamic environments. These LLMs demonstrate strong problem-solving capabilities and adaptability to multifaceted scenarios. However, their use as agents also introduces significant risks, including task-specific risks, which are identified by the agent administrator based on the specific task requirements and constraints, and systemic risks, which stem from vulnerabilities in their design or interactions, potentially compromising confidentiality, integrity, or availability (CIA) of information and triggering security risks. Existing defense agencies fail to adaptively and effectively mitigate these risks. In this paper,  we propose AGrail, a lifelong agent guardrail to enhance LLM agent safety, which features adaptive safety check generation, effective safety check optimization, and tool compatibility & flexibility. Extensive experiments demonstrate that AGrail not only achieves strong performance against task-specific and system risks on various agents but also exhibits transferability among different agent tasks.
<img src="workflow.png" width="1000"/>

## 👻 Quick Start

### 1. Create Python Environment
```python
conda create -n AGrail python=3.9
conda activate AGrail
pip install -r requirements.txt
pip install -e .
```

### 2. Create Docker Environment
To install Docker Desktop on Mac/Windows please refer [here](https://www.docker.com/get-started/).
Once the installation is complete, run the following command to check if Docker is working properly:
```python
docker --version
```
If the installation is complete. Please create a docker image with **dockerfile (install image under the same category with dockerfile)** in the repo:
```python
docker build -t ubuntu .
docker run -it ubuntu
```
If no error, please run all scripts and code locally.
### 3. Dataset Download
Here is the data link for other data, if you can not find data resources, please contact the author of the corresponding dataset by Email:
[Mind2Web and EICU-AC](https://github.com/guardagent/dataset) \\
[AdvWeb](https://github.com/AI-secure/AdvWeb)\\
[EIA](https://github.com/OSU-NLP-Group/EIA_against_webagent)

### 3. Conduct Inference on Safe-OS
Since prompt injection is generated based on GPT-4-Turbo's OS agent, please use GPT-4-Turbo as the foundation model of the OS agent to evaluate prompt injection attacks and GPT-4o as the foundation model for other attacks. Check and run the scripts on Safe-OS:
```python
# Add your OPENAI_API_KEY and ANTHROPIC_API_KEY in DAS/utlis.py.
bash DAS/scripts/safe_os.sh
```

### 4. Conduct Evaluation on Safe-OS
```python
python eval --dataset "prompt injection" --path #put your inference result csv file here.
python eval --dataset "system sabotage" --path #put your inference result csv file here.
python eval --dataset "environment" --path #put your inference result csv file here.
python eval --dataset "benign" --path #put your inference result csv file here.
```

### 4 .Tool Development for AGrail
Please check the /DAS/tools/tool.py and follow the interface.




## 👍 Contact
- Weidi Luo: luo.1455@osu.edu

- Chaowei Xiao: cxiao34@wisc.edu

## 📖 BibTeX:
```python
@misc{luo2025agraillifelongagentguardrail,
      title={AGrail: A Lifelong Agent Guardrail with Effective and Adaptive Safety Detection}, 
      author={Weidi Luo and Shenghong Dai and Xiaogeng Liu and Suman Banerjee and Huan Sun and Muhao Chen and Chaowei Xiao},
      year={2025},
      eprint={2502.11448},
      archivePrefix={arXiv},
      primaryClass={cs.AI},
      url={https://arxiv.org/abs/2502.11448}, 
}
```
