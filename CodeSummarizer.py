import argparse
import sys
import json
import requests
import os
from pathlib import Path
from typing import Dict, Optional, Union
import colorama
from colorama import Fore, Style

class CodeSummarizer:
    def __init__(self):
        """Initialize the CodeSummarizer with Ollama endpoint configuration"""
        self.ollama_endpoint = "http://localhost:11434/api/generate"
        self.model = "llama3.2"
        # Initialize colorama for Windows color support
        colorama.init()
    
    def _generate_prompt(self, code: str) -> str:
        """
        Generate a structured prompt for code analysis.
        
        Args:
            code (str): The source code to analyze
            
        Returns:
            str: Formatted prompt for the model
        """
        return f"""Please analyze this code and provide a detailed technical summary including:

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
        
        Args:
            prompt (str): The formatted prompt to send to Ollama
            
        Returns:
            Optional[str]: Generated response from the model or None if failed
        """
        try:
            response = requests.post(
                self.ollama_endpoint,
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=60
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

    def process_file(self, file_path: Union[str, Path]) -> Optional[str]:
        """
        Process a single code file and generate its summary.
        
        Args:
            file_path (Union[str, Path]): Path to the code file
            
        Returns:
            Optional[str]: Generated summary or None if processing failed
        """
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                print(f"{Fore.RED}Error: File {file_path} does not exist{Style.RESET_ALL}", 
                      file=sys.stderr)
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
                print(f"{Fore.RED}Error: Unable to read file with supported encodings{Style.RESET_ALL}", 
                      file=sys.stderr)
                return None

            prompt = self._generate_prompt(code_content)
            summary = self._call_ollama(prompt)
            
            if summary:
                return self._format_output(file_path.name, summary)
            return None

        except Exception as e:
            print(f"{Fore.RED}Error processing file {file_path}: {str(e)}{Style.RESET_ALL}", 
                  file=sys.stderr)
            return None

    def _format_output(self, filename: str, summary: str) -> str:
        """
        Format the summary output with clear section separation.
        
        Args:
            filename (str): Name of the processed file
            summary (str): Raw summary from the model
            
        Returns:
            str: Formatted summary with clear sections
        """
        separator = "=" * 80
        return f"""
{separator}
{Fore.GREEN}Code Analysis for: {filename}{Style.RESET_ALL}
{separator}

{summary}

{separator}
"""

def check_ollama_installation():
    """Check if Ollama is properly installed and running"""
    try:
        response = requests.get("http://localhost:11434/api/version")
        if response.status_code == 200:
            return True
    except:
        return False
    return False

def main():
    parser = argparse.ArgumentParser(description='Analyze and summarize code files using Llama2')
    parser.add_argument('files', nargs='+', help='Path to one or more code files to analyze')
    parser.add_argument('--output', '-o', help='Output file for the summary (optional)')
    args = parser.parse_args()

    # Check Ollama installation
    if not check_ollama_installation():
        print(f"""{Fore.RED}
Error: Cannot connect to Ollama. Please ensure:

1. Ollama is installed:
   - Download Ollama for Windows from: https://ollama.ai/download/windows
   - Install the downloaded .msi file
   - Restart your computer after installation

2. Start Ollama:
   - Open Command Prompt as Administrator
   - Run: wsl --update
   - Run: ollama serve

3. Pull the Llama2 model:
   - In another Command Prompt window, run:
   - ollama pull llama2:13b

If you're still having issues, check if WSL2 is installed and properly configured.
{Style.RESET_ALL}""")
        sys.exit(1)

    summarizer = CodeSummarizer()
    all_summaries = []

    print(f"{Fore.CYAN}Starting code analysis...{Style.RESET_ALL}")
    
    for file_path in args.files:
        print(f"{Fore.YELLOW}Processing {file_path}...{Style.RESET_ALL}")
        summary = summarizer.process_file(file_path)
        if summary:
            all_summaries.append(summary)
            if not args.output:
                print(summary)

    if args.output and all_summaries:
        try:
            output_path = Path(args.output)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(all_summaries))
            print(f"{Fore.GREEN}\nSummaries have been saved to {output_path}{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}Error saving to output file: {str(e)}{Style.RESET_ALL}", 
                  file=sys.stderr)
            if not args.output:
                print('\n'.join(all_summaries))

if __name__ == "__main__":
    main()