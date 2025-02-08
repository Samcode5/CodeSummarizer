import requests
import json
from pathlib import Path
from typing import Dict, Optional, Union, List, Set
import colorama
from colorama import Fore, Style

class CodeAnalyzer:
    def __init__(self):
        """Initialize the CodeAnalyzer with Ollama endpoint configuration"""
        self.ollama_endpoint = "http://localhost:11434/api/generate"
        self.model = "llama3.2:latest"
        # Common code file extensions
        self.code_extensions = {
            '.py', '.js', '.java', '.cpp', '.c', '.h', '.cs', '.php',
            '.rb', '.go', '.rs', '.ts','.html', '.css'
        }
        colorama.init()

    def is_code_file(self, file_path: Path) -> bool:
        """Check if the file is a recognized code file."""
        return file_path.suffix.lower() in self.code_extensions

    def _generate_prompt(self, code: str, file_path: Path) -> str:
        """Generate a structured prompt for code analysis."""
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
        """Make an API call to Ollama for text generation."""
        try:
            response = requests.post(
                self.ollama_endpoint,
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=150  
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
        """Process a single code file and generate its summary."""
        try:
            if not file_path.exists():
                print(f"{Fore.RED}Error: File {file_path} does not exist{Style.RESET_ALL}")
                return None

            # Maximum file size 500KB
            max_file_size = 500 * 1024
            file_size = file_path.stat().st_size

            if file_size > max_file_size:
                print(f"{Fore.YELLOW}Skipping {relative_path} (file size: {file_size/1024:.1f}KB, max: {max_file_size/1024:.1f}KB){Style.RESET_ALL}")
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
                print(f"{Fore.RED}Error: Unable to read {relative_path} with supported encodings{Style.RESET_ALL}")
                return None

            prompt = self._generate_prompt(code_content, file_path)
            return self._call_ollama(prompt)

        except Exception as e:
            print(f"{Fore.RED}Error processing {relative_path}: {str(e)}{Style.RESET_ALL}")
            return None

    def process_directory(self, directory_path: Path) -> tuple[List[tuple[str, str]], Dict]:
        """Process all code files in a directory and its subdirectories."""
        summaries = []
        skipped_files = []
        failed_files = []
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
                else:
                    failed_files.append(relative_path)

        stats = {
            'total': total_files,
            'success': len(summaries),
            'skipped': len(skipped_files),
            'failed': len(failed_files)
        }

        return summaries, stats