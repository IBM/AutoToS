
<p align="center">
  <img style="height:10em;" src="./blog/tos_icon.png" />
</p>

# AutoToS


<p align="center">
    <a href="https://ibm.github.io/AutoToS">🏠 Homepage</a> •
    <a href="https://arxiv.org/abs/2408.11326">📄 Paper</a> •
    <a href="https://proceedings.neurips.cc/paper_files/paper/2024/file/fa080fe0f218871faec1d8ba20e491d5-Paper-Conference.pdf">📄 ToS Paper</a>
</p>




AutoToS (Automated Thought of Search) builds upon Thought of Search through unit testing and debugging feedback to prompt the model to improve the successor and goal functions, with soundness, completeness tests for the goal and successor functions, all without human involvement in the iterative prompting process. 

## Installation

Use the package manager pip to install the required dependencies.

```bash
pip install -r requirements.txt
```

## Environment Variables
Create a .env file in the root directory and add the following information, replacing "your key" with your key:

```bash
API_KEY="your key"
API_BASE_URL="http://0.0.0.0:4000"
```
Our code works with any [LiteLLM Proxy Server](https://github.com/BerriAI/litellm?tab=readme-ov-file#step-1-start-litellm-proxy). You may adapt the [DomainTestBase](./src/domain_base_class.py) class to work with LM of your choice.

## Export Utils File
To ensure the utils file is correctly exported, run the following command in the root directory path:
```bash
export PYTHONPATH=$PYTHONPATH:./src
```



## Experiments
To run experiments you can use the following command line argument in the src/ folder:
```bash
python experiments.py  --model name_of_model --domain name_of_domain  
```
and if you want to test with a complex validator during the successor soundness test you can write
```bash
python experiments.py  --model name_of_model --domain name_of_domain --complex-validation
```

Currently available domains are  
 * `24game` - the 24Game is a mathematical puzzle, where the task is to get from 4 numbers to a single number 24 through a series of arithmetical operations. We use the dataset from [ToT repository](https://github.com/princeton-nlp/tree-of-thought-llm/tree/master/src/tot/data/24)
 * `blocks` - the BlocksWorld domain is one of the classical planning domains, where the goal is to transform from one configuration of blocks to another
 * `cw` - 5x5 mini crossword puzzles
 * `sokoban` - a famous game where an agent needs to push boxes in a maze to their target positions, and
 * `prontoqa` - a logical inference [dataset](https://github.com/asaparov/prontoqa) 


You also can simply run all experiments consecutively with the `--domain all` option

## Citing

```
@InProceedings{katz-et-al-neurips2024,
  title =        "Thought of Search: Planning with Language Models Through The Lens of Efficiency",
  author =       "Michael Katz and Harsha Kokel and Kavitha Srinivas and Shirin Sohrabi",
  booktitle =    "Proceedings of the Thirty-Seventh Annual Conference on
                  Neural Information Processing Systems ({NeurIPS} 2024)",
  year =         "2024"
}

@InProceedings{cao-et-al-neurips2024wsowa,
  author =       "Daniel Cao and Michael Katz and Harsha Kokel and Kavitha Srinivas and Shirin Sohrabi",
  title =        "Automating {T}hought of {S}earch: A Journey Towards Soundness and Completeness",
  booktitle =    "{NeurIPS} 2024 Workshop on Open-World Agents",
  year =         "2024"
}
```