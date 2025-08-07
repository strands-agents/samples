# LlamaCpp Provider for Strands SDK

This tutorial demonstrates using the LlamaCpp provider with Strands Agents. LlamaCpp enables running quantized models locally with advanced features like grammar constraints, multimodal support, and custom sampling parameters.

## Prerequisites

- Python 3.8+
- llama.cpp with server support ([Installation Guide](https://github.com/ggerganov/llama.cpp))
- 16GB RAM (minimum 8GB)
- 8GB storage for model files

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Download Model Files

Download the quantized Qwen2.5-Omni model for multimodal capabilities:

```bash
# Create models directory
mkdir -p models && cd models

# Download main model (4.68 GB)
huggingface-cli download ggml-org/Qwen2.5-Omni-7B-GGUF \
  Qwen2.5-Omni-7B-Q4_K_M.gguf --local-dir .

# Download multimodal projector (1.55 GB)
huggingface-cli download ggml-org/Qwen2.5-Omni-7B-GGUF \
  mmproj-Qwen2.5-Omni-7B-Q8_0.gguf --local-dir .

cd ..
```

Both files are required for audio and vision support.

### 3. Start LlamaCpp Server

```bash
llama-server -m models/Qwen2.5-Omni-7B-Q4_K_M.gguf \
  --mmproj models/mmproj-Qwen2.5-Omni-7B-Q8_0.gguf \
  --host 0.0.0.0 --port 8080 -c 8192 -ngl 50 --jinja
```

Key parameters:
- `-m`: Path to main model file
- `--mmproj`: Path to multimodal projector
- `-c`: Context window size (default: 8192)
- `-ngl`: Number of GPU layers (0 for CPU-only)
- `--jinja`: Enable template support for tools

The server will log "loaded multimodal model" when ready.

### 4. Run the Tutorial

```bash
jupyter notebook llamacpp_demo.ipynb
```

## Key Features

### Grammar Constraints

Control output format using GBNF (Backus-Naur Form) grammars:

```python
model.use_grammar_constraint('root ::= "yes" | "no"')
```

### Advanced Sampling

LlamaCpp provides fine-grained control over text generation:

- **Mirostat**: Dynamic perplexity control
- **TFS**: Tail-free sampling for quality improvement
- **Min-p**: Minimum probability threshold
- **Custom sampler ordering**: Control sampling pipeline

### Structured Output

Generate validated JSON output using Pydantic models:

```python
agent.structured_output(MyModel, "Generate user data")
```

### Multimodal Capabilities

- **Audio Input**: Process speech and audio files
- **Vision Input**: Analyze images
- **Combined Processing**: Simultaneous audio-visual understanding

### Performance Optimization

- Prompt caching for repeated queries
- Slot-based session management
- GPU acceleration with configurable layers

## Tutorial Content

The Jupyter notebook demonstrates:

1. **Grammar Constraints**: Enforce specific output formats
2. **Sampling Strategies**: Compare generation quality with different parameters
3. **Structured Output**: Type-safe data generation
4. **Tool Integration**: Function calling with LlamaCpp
5. **Audio Processing**: Speech recognition and understanding
6. **Image Analysis**: Visual content interpretation
7. **Multimodal Agents**: Combined audio-visual processing
8. **Performance Testing**: Optimization techniques and benchmarks

## Additional Examples

The `examples/` directory contains standalone Python scripts demonstrating specific features.

## Parameter Reference

### Standard Parameters

- `temperature`: Controls randomness (0.0-2.0)
- `max_tokens`: Maximum response length
- `top_p`: Nucleus sampling threshold
- `frequency_penalty`: Reduce repetition
- `presence_penalty`: Encourage topic diversity

### LlamaCpp-Specific Parameters

- `grammar`: GBNF grammar string
- `json_schema`: JSON schema for structured output
- `mirostat`: Enable Mirostat sampling (0, 1, or 2)
- `min_p`: Minimum probability cutoff
- `repeat_penalty`: Penalize token repetition
- `cache_prompt`: Enable prompt caching
- `slot_id`: Session slot for multi-user support

See the notebook for detailed parameter usage examples.

## Hardware Requirements

### Minimum Configuration
- 8GB RAM
- 4GB VRAM (or CPU-only mode)
- 8GB storage

### Recommended Configuration
- 16GB RAM
- 8GB+ VRAM
- CUDA-capable GPU or Apple Silicon

### GPU Acceleration
- **NVIDIA**: Requires CUDA toolkit
- **Apple Silicon**: Metal support included
- **AMD**: ROCm support (experimental)
- **CPU Mode**: Set `-ngl 0` when starting server

## About Quantized Models

### What is Quantization?

Quantization reduces model size by using lower precision numbers (e.g., 4-bit instead of 16-bit). This enables running large language models on consumer hardware with minimal quality loss.

### Qwen2.5-Omni-7B Model

- **Parameters**: 7.6 billion
- **Quantization**: 4-bit (Q4_K_M format)
- **Size**: 4.68GB (vs ~15GB unquantized)
- **Context**: 8,192 tokens (expandable to 32K)
- **Languages**: 23 languages supported

### LlamaCpp vs Ollama

| Feature | LlamaCpp | Ollama |
|---------|----------|--------|
| **Model Format** | GGUF files | Modelfile abstraction |
| **Control** | Full parameter access | Simplified interface |
| **Features** | Grammar, multimodal, sampling | Basic generation |
| **Use Case** | Advanced applications | Quick prototyping |

LlamaCpp provides lower-level control suitable for production applications requiring specific output formats or advanced features.

## Troubleshooting

### Common Issues

1. **Server won't start**: Verify llama.cpp installation and model file paths
2. **Out of memory**: Reduce GPU layers with `-ngl` parameter
3. **No multimodal support**: Ensure both model files are downloaded
4. **Slow performance**: Enable GPU acceleration or reduce context size

### Additional Resources

- [LlamaCpp Documentation](https://github.com/ggerganov/llama.cpp)
- [GGUF Format Specification](https://github.com/ggerganov/ggml/blob/master/docs/gguf.md)
- [Strands SDK Documentation](https://docs.strands.dev)

## License

MIT