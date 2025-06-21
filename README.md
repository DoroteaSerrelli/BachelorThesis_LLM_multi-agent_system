# Synaptic Coder  
## BachelorThesis_LLM_multi-agent_system

This repository contains all the Python projects developed for my Bachelor's thesis, titled **"Synaptic Coder: An LLM Multi-Agent System Specialized in Code Generation Tasks."**  
The project demonstrates the use of a multi-agent architecture based on Large Language Models (LLMs) to generate source code, inspired by the _Society of Mind_ approach.

---

### 🧠 Overview

In recent years, Large Language Models (LLMs) have shown exceptional capabilities in language generation, understanding, and few-shot learning.  
Building upon this, recent research suggests that adopting a **multi-agent approach**, where several LLM instances collaborate—proposing and debating solutions over multiple rounds—can significantly enhance reasoning accuracy and reduce hallucinations or factual errors.

This thesis explores the design and architecture of such a **multi-agent LLM system**, where autonomous agents work together to perform source code generation tasks based on natural language descriptions provided by the user.  
The performance of this multi-agent setup is then evaluated and compared with that of a **single LLM** specialized in code generation.

---

### 🛠️ Requirements

To run the project using **PyCharm** or from the command line, the following components are required:

- **Python 3.11**
- **LM Studio** – to run LLMs locally
- **SonarQube** – for static code analysis and function scanning

---

### ⚙️ Installation & Setup

Follow these steps to set up and run the project locally:

#### 1. Clone the Repository

```bash
git clone https://github.com/DoroteaSerrelli/BachelorThesis_LLM_multi-agent_system.git
cd BachelorThesis_LLM_multi-agent_system
```
#### 2. Create a Virtual Environment (Optional but Recommended)

```bash
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
```
#### 3. Install Dependencies

Make sure you have pip updated, then install the required packages:

```bash
pip install -r requirements.txt
```   

#### 4. Install & Configure LM Studio

  1. Download and install LM Studio: https://lmstudio.ai

  2. Download a compatible local LLM model (e.g., Code Llama, Mistral, etc.)

  3. Ensure the model runs via local API (default is usually http://localhost:1234)

  4. Update the API endpoint in your configuration if needed

#### 5. Install & Configure SonarQube (Optional)

  1. Download SonarQube: https://www.sonarsource.com/products/sonarqube

  2. Start the SonarQube server locally

  3. Integrate with your IDE (e.g., SonarLint in PyCharm) or use the CLI for code scanning

---

### 🚀 Usage

Once the environment is set up:

```bash
python main_multi-agent_debate.py
```
Follow the CLI or GUI prompts to input a natural language description of the desired code.
The system will coordinate a set of LLM agents to collaboratively generate and refine the source code output.

<!-- 📁 Project Structure

BachelorThesis_LLM_multi-agent_system/
├── agents/                 # Agent definitions and roles
├── prompts/                # Prompt templates and few-shot examples
├── utils/                  # Utility functions and tools
├── analysis/               # Performance metrics and comparisons
├── main.py                 # Entry point of the application
├── requirements.txt        # Python dependencies
└── README.md               # This file


 👩🏽‍🎓 Author

Dorotea Serrelli
Bachelor's Degree in Computer Science
University of Salerno
Email: d.serrelli1@studenti.unisa.it-->
