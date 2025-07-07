#!/usr/bin/env python3
"""
Pattern Validation Script

This script validates Strands Agent patterns to ensure they meet
the repository standards before submission.
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Any
import jsonschema


# Pattern metadata schema for validation
METADATA_SCHEMA = {
    "type": "object",
    "required": [
        "title", "description", "category", "complexity", "tags",
        "frameworks", "llm_providers", "author", "created_date"
    ],
    "properties": {
        "title": {"type": "string", "minLength": 5, "maxLength": 100},
        "description": {"type": "string", "minLength": 20, "maxLength": 500},
        "category": {
            "type": "string",
            "enum": [
                "basic-agents", "multi-agent-systems", "knowledge-retrieval",
                "aws-integrations", "tool-integrations", "ui-ux-patterns"
            ]
        },
        "complexity": {
            "type": "string",
            "enum": ["beginner", "intermediate", "advanced"]
        },
        "tags": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 2,
            "maxItems": 10
        },
        "frameworks": {
            "type": "array",
            "items": {"type": "string"},
            "contains": {"const": "strands-agents"}
        },
        "llm_providers": {
            "type": "array",
            "items": {"type": "string"}
        },
        "aws_services": {
            "type": "array",
            "items": {"type": "string"}
        },
        "author": {
            "type": "object",
            "required": ["name", "github"],
            "properties": {
                "name": {"type": "string", "minLength": 1},
                "github": {"type": "string", "minLength": 1},
                "linkedin": {"type": "string"}
            }
        },
        "created_date": {
            "type": "string",
            "pattern": "^\\d{4}-\\d{2}-\\d{2}$"
        },
        "updated_date": {
            "type": "string",
            "pattern": "^\\d{4}-\\d{2}-\\d{2}$"
        },
        "version": {"type": "string"},
        "demo": {
            "type": "object",
            "properties": {
                "available": {"type": "boolean"},
                "url": {"type": "string"}
            }
        },
        "metrics": {
            "type": "object",
            "properties": {
                "estimated_cost": {"type": "string"},
                "performance": {"type": "string"}
            }
        },
        "dependencies": {
            "type": "object",
            "properties": {
                "python_version": {"type": "string"},
                "strands_version": {"type": "string"},
                "external_libs": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "aws_services": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            }
        },
        "features": {
            "type": "object",
            "properties": {
                "tools": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "integrations": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "deployment_options": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            }
        },
        "learning_objectives": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 1
        },
        "related_patterns": {
            "type": "array",
            "items": {"type": "string"}
        },
        "use_cases": {
            "type": "array",
            "items": {"type": "string"}
        }
    }
}


class PatternValidator:
    """Validates Strands Agent patterns for compliance with repository standards."""
    
    def __init__(self, pattern_path: Path):
        self.pattern_path = pattern_path
        self.pattern_name = pattern_path.name
        self.errors: List[str] = []
        self.warnings: List[str] = []
        
    def validate(self) -> bool:
        """
        Validate the pattern and return True if valid.
        
        Returns:
            bool: True if pattern is valid, False otherwise
        """
        print(f"🔍 Validating pattern: {self.pattern_name}")
        
        # Check directory structure
        self._validate_structure()
        
        # Check metadata
        self._validate_metadata()
        
        # Check README
        self._validate_readme()
        
        # Check source code
        self._validate_source_code()
        
        # Check requirements
        self._validate_requirements()
        
        # Check tests
        self._validate_tests()
        
        # Report results
        self._report_results()
        
        return len(self.errors) == 0
    
    def _validate_structure(self) -> None:
        """Validate the pattern directory structure."""
        required_files = [
            "README.md",
            "pattern-metadata.json",
            "requirements.txt",
            "src/agent.py"
        ]
        
        recommended_dirs = ["tests", "examples"]
        
        for file_path in required_files:
            full_path = self.pattern_path / file_path
            if not full_path.exists():
                self.errors.append(f"Missing required file: {file_path}")
        
        for dir_path in recommended_dirs:
            full_path = self.pattern_path / dir_path
            if not full_path.exists():
                self.warnings.append(f"Missing recommended directory: {dir_path}")
    
    def _validate_metadata(self) -> None:
        """Validate the pattern metadata file."""
        metadata_path = self.pattern_path / "pattern-metadata.json"
        
        if not metadata_path.exists():
            self.errors.append("Missing pattern-metadata.json file")
            return
        
        try:
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
        except json.JSONDecodeError as e:
            self.errors.append(f"Invalid JSON in metadata file: {e}")
            return
        except Exception as e:
            self.errors.append(f"Error reading metadata file: {e}")
            return
        
        # Validate against schema
        try:
            jsonschema.validate(metadata, METADATA_SCHEMA)
        except jsonschema.ValidationError as e:
            self.errors.append(f"Metadata validation error: {e.message}")
        except Exception as e:
            self.errors.append(f"Metadata validation error: {e}")
        
        # Additional checks
        if metadata.get("title", "").lower() != self.pattern_name.replace("-", " ").lower():
            self.warnings.append("Pattern title doesn't match directory name")
    
    def _validate_readme(self) -> None:
        """Validate the README file."""
        readme_path = self.pattern_path / "README.md"
        
        if not readme_path.exists():
            self.errors.append("Missing README.md file")
            return
        
        try:
            with open(readme_path, 'r') as f:
                content = f.read()
        except Exception as e:
            self.errors.append(f"Error reading README.md: {e}")
            return
        
        required_sections = [
            "# ", "## Requirements", "## Deployment Instructions",
            "## How it works", "## Testing", "## Cleanup"
        ]
        
        for section in required_sections:
            if section not in content:
                self.errors.append(f"README missing required section: {section}")
        
        # Check for serverless land pattern link
        if "Learn more about this pattern at Serverless Land Patterns" not in content:
            self.warnings.append("README missing Serverless Land Patterns link")
        
        # Check for cost warning
        if "AWS costs incurred" not in content:
            self.warnings.append("README missing AWS cost warning")
    
    def _validate_source_code(self) -> None:
        """Validate the main source code file."""
        agent_path = self.pattern_path / "src" / "agent.py"
        
        if not agent_path.exists():
            self.errors.append("Missing src/agent.py file")
            return
        
        try:
            with open(agent_path, 'r') as f:
                content = f.read()
        except Exception as e:
            self.errors.append(f"Error reading src/agent.py: {e}")
            return
        
        # Check for required imports
        required_imports = ["from strands import Agent"]
        for import_stmt in required_imports:
            if import_stmt not in content:
                self.errors.append(f"Missing required import: {import_stmt}")
        
        # Check for docstring
        if '"""' not in content[:500]:
            self.warnings.append("src/agent.py missing module docstring")
        
        # Check for main function
        if "if __name__ == '__main__':" not in content:
            self.warnings.append("src/agent.py missing main execution block")
    
    def _validate_requirements(self) -> None:
        """Validate the requirements.txt file."""
        req_path = self.pattern_path / "requirements.txt"
        
        if not req_path.exists():
            self.errors.append("Missing requirements.txt file")
            return
        
        try:
            with open(req_path, 'r') as f:
                content = f.read()
        except Exception as e:
            self.errors.append(f"Error reading requirements.txt: {e}")
            return
        
        # Check for strands-agents
        if "strands-agents" not in content:
            self.errors.append("requirements.txt missing strands-agents dependency")
        
        # Check for version pinning
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        for line in lines:
            if '==' not in line and '>=' not in line and line.startswith('strands'):
                self.warnings.append(f"Consider pinning version for: {line}")
    
    def _validate_tests(self) -> None:
        """Validate test files."""
        tests_dir = self.pattern_path / "tests"
        
        if not tests_dir.exists():
            self.warnings.append("No tests directory found")
            return
        
        test_files = list(tests_dir.glob("test_*.py"))
        if not test_files:
            self.warnings.append("No test files found in tests directory")
        
        for test_file in test_files:
            try:
                with open(test_file, 'r') as f:
                    content = f.read()
                
                if "import pytest" not in content and "def test_" not in content:
                    self.warnings.append(f"Test file {test_file.name} may not contain valid tests")
            
            except Exception as e:
                self.warnings.append(f"Error reading test file {test_file.name}: {e}")
    
    def _report_results(self) -> None:
        """Report validation results."""
        print(f"\n📊 Validation Results for {self.pattern_name}")
        print("=" * 50)
        
        if self.errors:
            print("❌ ERRORS:")
            for error in self.errors:
                print(f"   • {error}")
        
        if self.warnings:
            print("\n⚠️  WARNINGS:")
            for warning in self.warnings:
                print(f"   • {warning}")
        
        if not self.errors and not self.warnings:
            print("✅ Pattern validation passed with no issues!")
        elif not self.errors:
            print(f"\n✅ Pattern validation passed with {len(self.warnings)} warnings")
        else:
            print(f"\n❌ Pattern validation failed with {len(self.errors)} errors")


def validate_pattern(pattern_path: str) -> bool:
    """
    Validate a single pattern.
    
    Args:
        pattern_path: Path to the pattern directory
        
    Returns:
        bool: True if pattern is valid
    """
    path = Path(pattern_path)
    
    if not path.exists():
        print(f"❌ Pattern path does not exist: {pattern_path}")
        return False
    
    if not path.is_dir():
        print(f"❌ Pattern path is not a directory: {pattern_path}")
        return False
    
    validator = PatternValidator(path)
    return validator.validate()


def validate_all_patterns(patterns_dir: str = "agent-patterns") -> bool:
    """
    Validate all patterns in the patterns directory.
    
    Args:
        patterns_dir: Path to the patterns directory
        
    Returns:
        bool: True if all patterns are valid
    """
    patterns_path = Path(patterns_dir)
    
    if not patterns_path.exists():
        print(f"❌ Patterns directory does not exist: {patterns_dir}")
        return False
    
    pattern_dirs = [d for d in patterns_path.iterdir() if d.is_dir()]
    
    if not pattern_dirs:
        print(f"⚠️  No pattern directories found in {patterns_dir}")
        return True
    
    all_valid = True
    print(f"🔍 Validating {len(pattern_dirs)} patterns...")
    
    for pattern_dir in pattern_dirs:
        validator = PatternValidator(pattern_dir)
        is_valid = validator.validate()
        all_valid = all_valid and is_valid
        print()  # Add spacing between patterns
    
    print("=" * 60)
    if all_valid:
        print("✅ All patterns passed validation!")
    else:
        print("❌ Some patterns failed validation. Please fix the errors above.")
    
    return all_valid


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Validate Strands Agent patterns")
    parser.add_argument(
        "pattern",
        nargs="?",
        help="Path to specific pattern to validate (validates all if not provided)"
    )
    parser.add_argument(
        "--patterns-dir",
        default="agent-patterns",
        help="Directory containing patterns (default: agent-patterns)"
    )
    
    args = parser.parse_args()
    
    if args.pattern:
        # Validate specific pattern
        success = validate_pattern(args.pattern)
    else:
        # Validate all patterns
        success = validate_all_patterns(args.patterns_dir)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main() 