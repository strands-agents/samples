"""
Utils package for LlamaCpp model provider demo.

This package contains helper utilities for the LlamaCpp demo notebook,
organized into logical modules for better code organization and reusability.
"""

from .audio_recorder import (
    AudioRecorder,
    create_audio_interface,
    display_audio_interface
)
from .image_utils import (
    create_test_image, 
    create_complex_test_image,
    image_to_base64, 
    image_to_bytes,
    analyze_image_with_llamacpp,
    create_image_analysis_demo,
    load_external_image,
    resize_image
)
from .grammar_utils import (
    demonstrate_grammar_constraint, 
    test_sampling_strategy,
    get_predefined_grammars,
    get_sampling_strategies,
    run_grammar_constraints_demo,
    run_sampling_strategies_demo,
    test_structured_output,
    create_json_grammar
)
from .benchmark_utils import (
    benchmark_performance, 
    analyze_benchmark_results, 
    visualize_performance,
    run_comprehensive_benchmark
)

__all__ = [
    # Audio utilities
    'AudioRecorder',
    'create_audio_interface',
    'display_audio_interface',
    
    # Image utilities
    'create_test_image',
    'image_to_bytes',
    'analyze_image_with_llamacpp',
    
    # Grammar and sampling utilities
    'demonstrate_grammar_constraint',
    'test_sampling_strategy',
    'get_predefined_grammars',
    'get_sampling_strategies',
    
    # Benchmark utilities
    'benchmark_performance',
    'run_comprehensive_benchmark',
    
    # Additional utilities (not used in notebook but available)
    'create_complex_test_image',
    'image_to_base64',
    'create_image_analysis_demo',
    'load_external_image',
    'resize_image',
    'run_grammar_constraints_demo',
    'run_sampling_strategies_demo',
    'test_structured_output',
    'create_json_grammar',
    'analyze_benchmark_results',
    'visualize_performance',
]