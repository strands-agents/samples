# LlamaCpp Tutorial Utilities

Support modules for the LlamaCpp tutorial notebook.

## Modules

### audio_utils.py
Audio recording and analysis utilities.

**Classes:**
- `AudioRecorder`: Simple audio recorder for capturing microphone input
  - Record audio with configurable duration and sample rate
  - Play back recorded audio
  - Convert audio to bytes for SDK integration

**Functions:**
- `create_enhanced_audio_interface()`: Creates a comprehensive Jupyter widget interface
- `display_audio_interface()`: Displays the audio interface in notebooks

**Features:**
- Progress tracking during recording and analysis
- Separate output areas for recording status, analysis, and transcription
- Error handling with troubleshooting guidance
- Support for Qwen2.5-Omni multimodal analysis

### image_utils.py
Image processing and analysis utilities.

**Functions:**
- `create_test_image()`: Create simple test images with geometric shapes
- `create_complex_test_image()`: Create complex scenes for advanced testing
- `image_to_bytes()`: Convert PIL images to bytes for SDK
- `analyze_image_with_llamacpp()`: Analyze images using LlamaCpp multimodal models
- `create_image_analysis_demo()`: Complete image analysis demonstration
- `load_external_image()`: Load images from file paths
- `resize_image()`: Resize images while maintaining aspect ratio

**Features:**
- Programmatic test image generation
- Direct integration with Strands SDK
- Error handling for analysis failures
- Support for various image formats

### grammar_utils.py
Grammar constraints and sampling utilities.

**Functions:**
- `demonstrate_grammar_constraint()`: Test specific GBNF grammar constraints
- `get_predefined_grammars()`: Collection of common grammar patterns
- `test_sampling_strategy()`: Test different sampling configurations
- `get_sampling_strategies()`: Predefined sampling strategy configurations
- `test_structured_output()`: Generate structured output with Pydantic models
- `run_grammar_constraints_demo()`: Comprehensive grammar demonstration
- `run_sampling_strategies_demo()`: Comprehensive sampling demonstration
- `create_json_grammar()`: Generate GBNF grammars from JSON schemas

**Features:**
- Pre-built grammar patterns
- Multiple sampling strategies
- Structured output generation
- Response timing analysis

### benchmark_utils.py
Performance benchmarking utilities.

**Functions:**
- `benchmark_performance()`: Comprehensive performance testing
- `analyze_benchmark_results()`: Statistical analysis of benchmark data
- `visualize_performance()`: Text-based performance visualizations
- `run_comprehensive_benchmark()`: Complete benchmark suite with analysis

**Features:**
- Multiple configuration testing with statistical analysis
- Performance comparison with baseline measurements
- Text-based charts for response time, tokens/sec, and consistency
- Recommendations based on benchmark results
- Error handling for failed benchmark runs

## Usage Examples

### Audio Recording
```python
from utils import AudioRecorder, create_enhanced_audio_interface, display_audio_interface

# Create recorder
recorder = AudioRecorder(sample_rate=16000)

# Create interface
interface = create_enhanced_audio_interface(recorder)
display_audio_interface(interface)
```

### Image Analysis
```python
from utils import create_test_image, analyze_image_with_llamacpp

# Create and analyze image
image = create_test_image()
analysis = analyze_image_with_llamacpp(image, "Describe this image")
print(analysis)
```

### Grammar Constraints
```python
from utils import demonstrate_grammar_constraint, get_predefined_grammars

# Get available grammars
grammars = get_predefined_grammars()

# Test yes/no constraint
demonstrate_grammar_constraint(
    grammars["yes_no"]["grammar"],
    "Is Python interpreted?",
    "Yes/No responses only"
)
```

### Performance Benchmarking
```python
from utils import run_comprehensive_benchmark

# Run complete benchmark suite
results = run_comprehensive_benchmark()
print(f"Fastest config: {results['summary']['fastest_config']}")
```

## Dependencies

- `strands`: Strands SDK
- `sounddevice`, `soundfile`, `scipy`: Audio processing
- `PIL`: Image manipulation
- `ipywidgets`: Notebook widgets
- `pydantic`: Data validation
- `numpy`: Numerical operations

## Integration with Notebook

The main notebook imports all utilities with:

```python
from utils import (
    # Audio utilities
    AudioRecorder, create_enhanced_audio_interface, display_audio_interface,
    
    # Image utilities  
    create_test_image, analyze_image_with_llamacpp,
    
    # Grammar utilities
    demonstrate_grammar_constraint, get_predefined_grammars,
    
    # Benchmark utilities
    run_comprehensive_benchmark
)
```

This keeps the notebook clean and focused on demonstrating LlamaCpp capabilities while maintaining all functionality in reusable, well-organized modules.

## Notes

- All functions include error handling
- Modular design for easy extension
- See individual module docstrings for detailed API documentation