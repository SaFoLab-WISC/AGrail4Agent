<p align="center">
    <img src="icon.png" width="150"/>
<p>

<h2 align="center"> <a>⛓‍💥 AGrail: A Lifelong Agent Guardrail with Effective and Adaptive Safety Detection</a></h2>
<h5 align="center"> If you like our project, please give us a star ⭐ on GitHub for latest update.  </h2>

<h5 align="center">

[Weidi Luo](https://eddyluo1232.github.io/), [Shenghong Dai](https://scholar.google.com/citations?user=GUarSlcAAAAJ&hl=en), [Xiaogeng Liu](https://xiaogeng-liu.com/), [Suman Banerjee](https://pages.cs.wisc.edu/~suman/), [Huan Sun](https://u.osu.edu/ihudas/people/), [Muhao Chen](https://muhaochen.github.io/), [Chaowei Xiao](https://xiaocw11.github.io/)

[![arxiv](https://img.shields.io/badge/Arxiv-2403.09513-red)]()
[![project](https://img.shields.io/badge/Project-Page-blue)](https://eddyluo1232.github.io/AGrail/)
[![Defenses](https://img.shields.io/badge/Agent-Guardrail-green)]


**<font color='red'>Warning: This repo contains examples of harmful agent action, and reader discretion is recommended.</font>**




## 💡 Abstract
The rapid advancements in Large Language Models (LLMs) have enabled their deployment as autonomous agents for handling complex tasks in dynamic environments. These LLMs demonstrate strong problem-solving capabilities and adaptability to multifaceted scenarios. However, their use as agents also introduces significant risks, including task-specific risks, which are identified by the agent administrator based on the specific task requirements and constraints, and systemic risks, which stem from vulnerabilities in their design or interactions, potentially compromising confidentiality, integrity, or availability (CIA) of information and triggering security risks. Existing defense agencies fail to adaptively and effectively mitigate these risks. In this paper,  we propose AGrail, a lifelong agent guardrail to enhance LLM agent safety, which features adaptive safety check generation, effective safety check optimization, and tool compatibility & flexibility. Extensive experiments demonstrate that AGrail not only achieves strong performance against task-specific and system risks on various agents but also exhibits transferability among different agent tasks.
<img src="workflow.png" width="1000"/>

## 👻 Quick Start

### 1.Create Python environment
```python
conda create -n agentguard python=3.9
conda activate agentguard
pip install -r requirements.txt
pip install -e .
```

### 2.Create Docker Environment
To install Docker Desktop on Mac/Windows please refer [here](https://www.docker.com/get-started/).
Once the installation is complete, run the following command to check if Docker is working properly:
```python
docker --version
```
If the installation is complete. Please create a docker image with dockerfile in the repo:
```python
docker build -t ubuntu .
docker run -it ubuntu
```

### 3.Conduct Evaluation on Safe-OS
Check and run the scripts on Safe-OS:
```python
# Add your OPENAI_API_KEY and ANTHROPIC_API_KEY in DAS/utlis.py.
bash DAS/scripts/safe_os.sh
```

### 4.Tool Development for AGrail
Please check the /DAS/tools/tool.py and follow the interface.


## 👍 Contact
- Weidi Luo: luo.1455@osu.edu

- Chaowei Xiao: cxiao34@wisc.edu

## 📖 BibTeX:
```python

```
