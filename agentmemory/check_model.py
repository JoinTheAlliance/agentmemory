import os
import requests
import tarfile
from pathlib import Path
from tqdm import tqdm

def _download(url: str, fname: Path, chunk_size: int = 1024) -> None:
    resp = requests.get(url, stream=True)
    total = int(resp.headers.get("content-length", 0))
    with open(fname, "wb") as file, tqdm(
        desc=str(fname),
        total=total,
        unit="iB",
        unit_scale=True,
        unit_divisor=1024,
    ) as bar:
        for data in resp.iter_content(chunk_size=chunk_size):
            size = file.write(data)
            bar.update(size)

default_model_path = Path.home() / ".cache" / "onnx_models"

def check_model(model_name = "all-MiniLM-L6-v2", model_path = default_model_path) -> str:
    DOWNLOAD_PATH = Path(model_path) / model_name
    ARCHIVE_FILENAME = "onnx.tar.gz"
    MODEL_DOWNLOAD_URL = f"https://chroma-onnx-models.s3.amazonaws.com/{model_name}/onnx.tar.gz"

    # Check if model is not downloaded yet
    if not os.path.exists(DOWNLOAD_PATH / ARCHIVE_FILENAME):
        os.makedirs(DOWNLOAD_PATH, exist_ok=True)
        _download(MODEL_DOWNLOAD_URL, DOWNLOAD_PATH / ARCHIVE_FILENAME)

        with tarfile.open(DOWNLOAD_PATH / ARCHIVE_FILENAME, "r:gz") as tar:
            tar.extractall(DOWNLOAD_PATH)

    return str(DOWNLOAD_PATH / "onnx")

import importlib
import numpy as np
from tokenizers import Tokenizer
import onnxruntime
import numpy.typing as npt
from typing import List

def _normalize(v: npt.NDArray) -> npt.NDArray:
    norm = np.linalg.norm(v, axis=1)
    norm[norm == 0] = 1e-12
    return v / norm[:, np.newaxis]

def infer_embeddings(documents: List[str], model_path: str, batch_size: int = 32) -> npt.NDArray:
    # Load the tokenizer and model
    tokenizer = Tokenizer.from_file(model_path + "/tokenizer.json")
    tokenizer.enable_truncation(max_length=256)
    tokenizer.enable_padding(pad_id=0, pad_token="[PAD]", length=256)
    model = onnxruntime.InferenceSession(model_path + "/model.onnx")

    all_embeddings = []
    for i in range(0, len(documents), batch_size):
        batch = documents[i : i + batch_size]
        encoded = [tokenizer.encode(d) for d in batch]
        input_ids = np.array([e.ids for e in encoded])
        attention_mask = np.array([e.attention_mask for e in encoded])
        onnx_input = {
            "input_ids": np.array(input_ids, dtype=np.int64),
            "attention_mask": np.array(attention_mask, dtype=np.int64),
            "token_type_ids": np.array(
                [np.zeros(len(e), dtype=np.int64) for e in input_ids],
                dtype=np.int64,
            ),
        }
        model_output = model.run(None, onnx_input)
        last_hidden_state = model_output[0]
        # Perform mean pooling with attention weighting
        input_mask_expanded = np.broadcast_to(
            np.expand_dims(attention_mask, -1), last_hidden_state.shape
        )
        embeddings = np.sum(last_hidden_state * input_mask_expanded, 1) / np.clip(
            input_mask_expanded.sum(1), a_min=1e-9, a_max=None
        )
        embeddings = _normalize(embeddings).astype(np.float32)
        all_embeddings.append(embeddings)
    return np.concatenate(all_embeddings)
