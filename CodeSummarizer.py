#!/usr/bin/env python3
import argparse
import sys
import json
import requests
import os
from pathlib import Path
from typing import Dict, Optional, Union, List, Set
import colorama
from colorama import Fore, Style
from datetime import datetime

class CodeSummarizer:
    def __init__(self):
        """Initialize the CodeSummarizer with Ollama endpoint configuration"""
        self.ollama_endpoint = "http://localhost:11434/api/generate"
        self.model = "llama2:13b"
        # Common code file extensions
        self.code_extensions = {
            '.py', '.js', '.java', '.cpp', '.c', '.h', '.cs', '.php',
            '.rb', '.go', '.rs', '.ts','.html'
        }
        colorama.init()

    def is_code_file(self, file_path: Path) -> bool:
        """
        Check if the file is a recognized code file.
        
        Args:
            file_path (Path): Path to the file
            
        Returns:
            bool: True if it's a code file, False otherwise
        """
        return file_path.suffix.lower() in self.code_extensions

    def _generate_prompt(self, code: str, file_path: Path) -> str:
        """
        Generate a structured prompt for code analysis.
        
        Args:
            code (str): The source code to analyze
            file_path (Path): Path to the file for context
            
        Returns:
            str: Formatted prompt for the model
        """
        return f"""Please analyze this {file_path.suffix[1:]} code file and provide a detailed technical summary including:

1. Overall Purpose: Briefly explain what this code does
2. Main Components: Describe the key classes, functions, or modules
3. Implementation Details: Notable algorithms, patterns, or techniques used
4. Dependencies: List any external libraries or systems required
5. Technical Highlights: Any interesting or important technical aspects

Code to analyze:

{code}

Please structure your response in clear sections using the numbers above."""

    def _call_ollama(self, prompt: str) -> Optional[str]:
        """
        Make an API call to Ollama for text generation.
        """
        try:
            response = requests.post(
                self.ollama_endpoint,
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=120
            )
            response.raise_for_status()
            return response.json().get("response")
        except requests.exceptions.RequestException as e:
            print(f"{Fore.RED}Error communicating with Ollama: {str(e)}{Style.RESET_ALL}", 
                  file=sys.stderr)
            return None
        except json.JSONDecodeError:
            print(f"{Fore.RED}Error parsing Ollama response{Style.RESET_ALL}", 
                  file=sys.stderr)
            return None

    def process_file(self, file_path: Path, relative_path: str) -> Optional[str]:
        """
        Process a single code file and generate its summary.
        
        Args:
            file_path (Path): Absolute path to the code file
            relative_path (str): Relative path for display purposes
            
        Returns:
            Optional[str]: Generated summary or None if processing failed
        """
        try:
            if not file_path.exists():
                print(f"{Fore.RED}Error: File {file_path} does not exist{Style.RESET_ALL}", 
                      file=sys.stderr)
                return None

            # Skip files larger than 100KB to avoid overwhelming the model
            if file_path.stat().st_size > 100 * 1024:
                print(f"{Fore.YELLOW}Skipping {relative_path} (file too large){Style.RESET_ALL}")
                return None

            # Try different encodings for Windows compatibility
            encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']
            code_content = None
            
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        code_content = f.read()
                    break
                except UnicodeDecodeError:
                    continue
            
            if code_content is None:
                print(f"{Fore.RED}Error: Unable to read {relative_path} with supported encodings{Style.RESET_ALL}", 
                      file=sys.stderr)
                return None

            prompt = self._generate_prompt(code_content, file_path)
            summary = self._call_ollama(prompt)
            
            if summary:
                return self._format_output(relative_path, summary)
            return None

        except Exception as e:
            print(f"{Fore.RED}Error processing {relative_path}: {str(e)}{Style.RESET_ALL}", 
                  file=sys.stderr)
            return None

    def _format_output(self, filepath: str, summary: str) -> str:
        """
        Format the summary output with clear section separation.
        """
        separator = "=" * 80
        return f"""
{separator}
{Fore.GREEN}Code Analysis for: {filepath}{Style.RESET_ALL}
{separator}

{summary}

{separator}
"""

    def process_directory(self, directory_path: Path) -> List[tuple[str, str]]:
        """
        Recursively process all code files in a directory and its subdirectories.
        
        Args:
            directory_path (Path): Path to the directory to process
            
        Returns:
            List[tuple[str, str]]: List of (relative_path, summary) tuples
        """
        summaries = []
        total_files = sum(1 for p in directory_path.rglob('*') if self.is_code_file(p))
        processed_files = 0

        print(f"{Fore.CYAN}Found {total_files} code files to process{Style.RESET_ALL}")

        for file_path in directory_path.rglob('*'):
            if self.is_code_file(file_path):
                processed_files += 1
                relative_path = str(file_path.relative_to(directory_path))
                print(f"{Fore.YELLOW}Processing ({processed_files}/{total_files}): {relative_path}{Style.RESET_ALL}")
                
                summary = self.process_file(file_path, relative_path)
                if summary:
                    summaries.append((relative_path, summary))

        return summaries

def main():
    parser = argparse.ArgumentParser(description='Analyze and summarize code files in a directory using Llama2')
    parser.add_argument('directory', help='Directory containing code files to analyze')
    args = parser.parse_args()

    directory_path = Path(args.directory).resolve()
    if not directory_path.exists() or not directory_path.is_dir():
        print(f"{Fore.RED}Error: {args.directory} is not a valid directory{Style.RESET_ALL}")
        sys.exit(1)

    # Create output filename based on directory name
    current_dir=Path.cwd()/"codeSummary.txt"
    output_file =current_dir

    summarizer = CodeSummarizer()
    print(f"{Fore.CYAN}Starting code analysis in: {directory_path}{Style.RESET_ALL}")
    
    summaries = summarizer.process_directory(directory_path)
    
    if summaries:
        try:
            # Create a table of contents
            toc = ["Table of Contents", "=" * 80]
            for filepath, _ in summaries:
                toc.append(f"- {filepath}")
            toc.extend(["", "=" * 80, ""])

            # Write table of contents and summaries
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(toc))
                for _, summary in summaries:
                    # Remove color codes for file output
                    clean_summary = summary.replace(Fore.GREEN, '').replace(Fore.YELLOW, '').replace(Style.RESET_ALL, '')
                    f.write(clean_summary)

            print(f"{Fore.GREEN}\nAnalysis complete! Summary saved to: {output_file}{Style.RESET_ALL}")
            print(f"Processed {len(summaries)} files")
        except Exception as e:
            print(f"{Fore.RED}Error saving summary: {str(e)}{Style.RESET_ALL}", file=sys.stderr)
    else:
        print(f"{Fore.YELLOW}No code files were successfully processed{Style.RESET_ALL}")

if __name__ == "__main__":
    main()