import typer
import os
import sys

# Add current directory to path for command imports
sys.path.append(os.path.dirname(__file__))
# Add project root to path for internal imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

from commands.system import check_gpu
from commands.vision import auto_choose_best, compare_epochs, analyze_and_store
from commands.agent import test_telemetry
from commands.generation import generate_training_data, generate_final_golden_ratio, weight_sweep, simple_gen, hybrid_quant_gen
from commands.data import convert_parquet, view_parquet, analyze_tokens

app = typer.Typer(
    name="llm-py-utils",
    help="Python utilities for the LLM Playground",
    add_completion=False,
    rich_markup_mode="rich"
)

@app.command()
def check_gpu_status():
    """
    Check if CUDA is available and display GPU information.
    """
    check_gpu.check_cuda()

@app.command()
def choose_best():
    """
    Automatically choose the best image from a weight sweep using LLM vision.
    """
    auto_choose_best.main()

@app.command()
def compare(
    image_a: str = compare_epochs.IMAGE_A,
    image_b: str = compare_epochs.IMAGE_B
):
    """
    Compare two different images/epochs using LLM vision.
    """
    compare_epochs.compare_images(image_a, image_b)

@app.command()
def gen_data(
    topic: str = "beauty girl",
    total: int = 30,
    output_dir: str = None
):
    """
    Generate training data (images + captions) using Forge and Ollama.
    """
    generate_training_data.main(topic=topic, total=total, output_dir=output_dir)

@app.command()
def gen_golden(
    concept: str = None,
    weight: float = 0.8,
    lora: str = "FancyStyle_v1-000009"
):
    """
    Generate the final 'Golden Ratio' image using expanded prominence and Forge.
    """
    generate_final_golden_ratio.main(concept=concept, weight=weight, lora=lora)

@app.command()
def analyze(image_path: str = None):
    """
    Analyze an image using LLM vision and store result in AnythingLLM.
    """
    analyze_and_store.main(image_path)

@app.command()
def sweep(concept: str = None, lora: str = "FancyStyle_v1-000009"):
    """
    Perform a weight sweep for a LoRA.
    """
    weight_sweep.main(concept, lora)

@app.command()
def gen(concept: str):
    """
    Generate a simple image from a concept.
    """
    simple_gen.generate_image(concept)

@app.command()
def quant(
    inputs: list[str],
    model: str = "deepseek-r1:32b",
    limit: int = 50,
    output: str = "market_analysis.md"
):
    """
    Perform hybrid quant analysis on CSV market data.
    """
    hybrid_quant_gen.main(inputs, model, limit, output)

@app.command()
def convert_dataset(
    input_dir: str = typer.Option(..., "--input", "-i", help="Input directory containing code files"),
    output_dir: str = typer.Option(..., "--output", "-o", help="Output directory for parquet files"),
    extension: str = typer.Option("go", "--ext", "-e", help="File extension to scan"),
    chunk_size: int = typer.Option(10000, "--chunk", "-c", help="Files per chunk"),
    repo_name: str = typer.Option("custom-repo", "--repo", "-r", help="Repo name tag"),
    prefix: str = typer.Option("train", "--prefix", "-p", help="Filename prefix")
):
    """
    Convert a directory of code files into Hugging Face compatible Parquet shards.
    """
    convert_parquet.convert_to_parquet(input_dir, output_dir, extension, chunk_size, repo_name, prefix)

@app.command()
def view_dataset(
    file_path: str = typer.Argument(..., help="Path to the parquet file"),
    head: int = typer.Option(5, "--head", "-n", help="Number of rows to show"),
    full: bool = typer.Option(False, "--full", "-f", help="Show full content")
):
    """
    Visualize a Parquet file in the terminal.
    """
    view_parquet.view_parquet(file_path, head, full)

@app.command()
def analyze_dataset(
    file_path: str = typer.Argument(..., help="Path to parquet file(s)"),
    model: str = typer.Option("Qwen/Qwen2.5-Coder-32B-Instruct", "--model", "-m", help="HF Model ID"),
    sample: int = typer.Option(1000, "--sample", "-s", help="Sample size per file")
):
    """
    Analyze token length distribution to verify sequence_len settings.
    """
    analyze_tokens.analyze_tokens(file_path, model, sample)

@app.command()
def test_agent(
    prompt: str = "Who are you?",
    model: str = typer.Option(None, "--model", "-m", help="Model to use")
):
    """
    Test the agent flow through the Arize Phoenix Proxy.
    """
    test_telemetry.main(prompt, model)

if __name__ == "__main__":
    app()
