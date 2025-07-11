# Pattern Template

This is a template for creating new Strands agent patterns. The pattern will be displayed on the [Strands Agents website](https://strandsagents.com/patterns/).

## Development

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Update `pattern-metadata.json` with:
   ```json
   {
     "title": "Your Pattern Name",
     "description": "A brief description of what your pattern does",
     "introBox": {
       "headline": "How it works",
       "text": [
         "Describe the main components and how they work together",
         "Explain key features or capabilities",
         "Mention any important tools or integrations"
       ]
     },
     "source": {
       "file_url": "URL to the raw implementation file",
       "repo_url": "URL to the pattern's repository"
     }
   }
   ```

## Documentation

Your pattern will be automatically rendered on the website with:
- A title and description
- A "How it works" section with bullet points
- The implementation code
- A link to the full source 