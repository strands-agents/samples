# Architecture Diagrams

This folder contains the architecture diagrams for the Lambda Error Analysis system.

## Generated Diagrams

- **`lambda-error-analysis-architecture.png`** - White background version (for light mode)
- **`lambda-error-analysis-architecture-transparent.png`** - Transparent background version (for dark mode)

## Regenerating Diagrams

If you need to regenerate the diagrams (e.g., after making changes to the architecture):

### Prerequisites

1. **Install Graphviz** (system dependency):
   ```bash
   # macOS
   brew install graphviz
   
   # Ubuntu/Debian
   sudo apt-get install graphviz
   
   # Windows
   # Download from: https://graphviz.org/download/
   ```

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

### Generate Diagrams

Run the generation script:
```bash
python generate_diagram.py
```

This will create both versions:
- White background: `lambda-error-analysis-architecture.png`
- Transparent background: `lambda-error-analysis-architecture-transparent.png`

## Modifying the Diagram

To modify the architecture diagram:

1. Edit `generate_diagram.py`
2. Update both functions:
   - `generate_lambda_error_analysis_diagram()` - for white background
   - `generate_transparent_diagram()` - for transparent background
3. Run `python generate_diagram.py` to regenerate

## Notes

- The transparent version uses white text for certain labels to ensure visibility on dark backgrounds
- Both diagrams use the same architecture layout for consistency
- The diagrams library uses Graphviz under the hood for rendering
