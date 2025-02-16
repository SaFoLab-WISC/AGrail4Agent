# ⛓‍💥 Agent Protector: A Lifelong Agent Guardrail with Effective and Adaptive Safety Detection

[Weidi Luo](https://github.com/EddyLuo1232), [Shenghong Dai](https://scholar.google.com/citations?user=GUarSlcAAAAJ&hl=en), [Xiaogeng Liu](https://xiaogeng-liu.com/), [Suman Banerjee](https://pages.cs.wisc.edu/~suman/), [Huan Sun](https://u.osu.edu/ihudas/people/), [Muhao Chen](https://muhaochen.github.io/), [Chaowei Xiao](https://xiaocw11.github.io/)


[**🛎 Project Page**](https://eddyluo1232.github.io/JailBreakV28K/) | [**😀 arxiv**](https://arxiv.org/pdf/2404.03027.pdf)


**<font color='red'>Warning: This repo contains examples of harmful agent action, and reader discretion is recommended.</font>**

## 👻 Environment Configuration

### Create Python environment
```python
conda create -n agentguard python=3.9
conda activate agentguard
pip install -r requirements.txt
pip install -e .
```

### Create Docker Environment
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

### Conduct Evaluation on Safe-OS
Add your OPENAI_API_KEY and ANTHROPIC_API_KEY in DAS/utlis.py, then check and run the scripts on Safe-OS:
```python
bash DAS/scripts/safe_os.sh
```

### Tool Development
Please check the /DAS/tools/tool.py and follow the interface.


## 📰 News
| Date       | Event    |
|------------|----------|
| **2024/07/09** | 🎉 Our paper is accepted by COLM 2024.|
| **2024/06/22** | 🛠️ We have updated our version to V0.2, which allows users to customize and evaluate their attack models.|
| **2024/04/04** | 🎁 We have posted our paper on Arxiv.|
| **2024/04/03** | 🎉 We have released our evaluation and inference samples.|
| **2024/03/30** | 🔥 We have released our dataset.|


## 💡 Abstract



## 📲 Contact
- Weidi Luo: luo.1455@osu.edu

- Chaowei Xiao: cxiao34@wisc.edu

## 📖 BibTeX:
```python

```
