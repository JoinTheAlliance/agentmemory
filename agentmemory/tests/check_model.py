import os
from pathlib import Path
import shutil
import tempfile
from agentmemory.check_model import check_model, infer_embeddings

def test_check_model():
    model_name = "all-MiniLM-L6-v2"
    temp_dir = tempfile.mkdtemp()
    model_path = str(Path(temp_dir) / ".cache" / "onnx_models")

    # Remove existing model if it exists
    if os.path.exists(model_path):
        shutil.rmtree(model_path)

    result_path = check_model(model_name, model_path)

    assert os.path.exists(result_path)
    assert os.path.exists(os.path.join(result_path, "model.onnx"))
    assert os.path.exists(os.path.join(result_path, "tokenizer.json"))

    # Clean up by removing the temporary directory after the test
    shutil.rmtree(temp_dir)

import numpy as np

def test_infer_embeddings():
    # Define the path to the ONNX model, assuming you are using the check_model function
    model_path = check_model()

    # Test data
    documents = ["This is a test sentence.", "Another test sentence."]
    
    # Run the inference
    embeddings = infer_embeddings(documents, model_path)

    # Validate the result
    assert isinstance(embeddings, np.ndarray), "Output must be a numpy array"
    assert embeddings.shape[0] == len(documents), "Number of embeddings must match number of input documents"
    assert embeddings.shape[1] > 0, "Embedding size must be greater than 0"