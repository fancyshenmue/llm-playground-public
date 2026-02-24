from datasets import load_dataset
import os

# Disable HF auth check if possible or rely on cached credentials
os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"

print("Attempting to load one record from bigcode/the-stack (v1)...")
try:
    # Try loading the Python subset from v1
    ds = load_dataset(
        "bigcode/the-stack",
        data_dir="data/python",
        streaming=True,
        split="train",
    )

    row = next(iter(ds))
    print("\nSUCCESS! Found columns:")
    print(list(row.keys()))

    if 'content' in row:
        print("\n'content' column exists!")
    else:
        print("\n'content' column MISSING.")

except Exception as e:
    print(f"\nError loading dataset: {e}")
