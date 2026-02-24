from datasets import load_dataset
import os

# Disable HF auth check if possible or rely on cached credentials
os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"

print("Attempting to load one record from bigcode/the-stack-v2...")
try:
    # Use the same pattern as the config
    ds = load_dataset(
        "bigcode/the-stack-v2",
        data_files="data/Python/train-00000-of-*.parquet",
        streaming=True,
        split="train",
        name="default"
    )

    row = next(iter(ds))
    print("\nSUCCESS! Found columns:")
    print(list(row.keys()))

    # Check for content-like fields
    if 'content' in row:
        print("\n'content' column exists!")
    else:
        print("\n'content' column MISSING.")
        # Print first 100 chars of likely text fields if found
        for k, v in row.items():
            if isinstance(v, str) and len(v) > 50:
                 print(f"Sample '{k}': {v[:100]}...")

except Exception as e:
    print(f"\nError loading dataset: {e}")
