# LangChain Test Lab Operations

## Bootstrapping Environment

### 1. Requirements
Ensure the local Ollama daemon is properly spun up and hosting `gemma4:26b` to avoid socket read errors.

### 2. Frontend Application
```bash
make langchain-lab-dev
```
Serves the React evaluation interface at `http://localhost:5173`.

### 3. Backend Integration Core
```bash
make langchain-api-dev
```
Loads the `lab_api` FastAPI instance on port 8000. Provides standard non-streaming, stateless Agent responses.

## Evaluation Test Prompts
Copy and paste these exact prompts into the React Lab interface to evaluate the model's capabilities:

### 1. The Decorator Test
```text
Write a Python decorator called @measure_time to calculate the execution time of any function in milliseconds. Then, write a dummy function sleep_test that simulates a delay, apply the decorator to it, and call it at the very bottom of the script to print the result.
```

### 2. The Auto-Coder Filesystem Test
```text
Write a Python script that creates a text file named langgraph_magic.txt inside the /tmp/ directory, containing the text 'Hello from Gemma 4 Auto-Coder!'. After writing to the file, have the script read the file back and print its contents to the console.
```
*(After it successfully completes, you can go to your terminal and type `cat /tmp/langgraph_magic.txt` to verify that the file actually exists!)*

### 3. The Algorithmic State Test
```text
Please write a Python class FibonacciGenerator that contains a method to generate and print the first 15 numbers in the Fibonacci sequence. Instantiate the class and execute the method at the bottom of the script.
```
