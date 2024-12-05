import argparse
import sys
from pathlib import Path
from datetime import datetime
import colorama
from colorama import Fore, Style
from model_handler import CodeAnalyzer
from pdf_generator import PDFGenerator
import os

def get_downloads_path() -> Path:
    """Get the path to the user's Downloads directory"""
    if os.name == 'nt':  # Windows
        import winreg
        sub_key = r'SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders'
        downloads_guid = '{374DE290-123F-4565-9164-39C4925E467B}'
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, sub_key) as key:
            location = winreg.QueryValueEx(key, downloads_guid)[0]
        return Path(location)
    else:  # Linux/Unix/MacOS
        return Path.home() / 'Downloads'

def main():
    parser = argparse.ArgumentParser(description='Analyze and summarize code files in a directory using Llama2')
    parser.add_argument('directory', help='Directory containing code files to analyze')
    args = parser.parse_args()

    directory_path = Path(args.directory).resolve()
    if not directory_path.exists() or not directory_path.is_dir():
        print(f"{Fore.RED}Error: {args.directory} is not a valid directory{Style.RESET_ALL}")
        sys.exit(1)

    # Create output filename in Downloads folder
    downloads_path = get_downloads_path()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pdf_output = downloads_path / f"code_summary_{timestamp}.pdf"

    analyzer = CodeAnalyzer()
    pdf_generator = PDFGenerator()

    print(f"{Fore.CYAN}Starting code analysis in: {directory_path}{Style.RESET_ALL}")
    
    summaries, stats = analyzer.process_directory(directory_path)
    
    if summaries:
        try:
            # Generate PDF summary in Downloads folder
            pdf_generator.create_pdf_summary(
                summaries,
                pdf_output,
                directory_path.name,
                stats
            )

            print(f"{Fore.GREEN}\nAnalysis complete! PDF report downloaded to: {pdf_output}{Style.RESET_ALL}")
            print(f"Processed {len(summaries)} files")

        except Exception as e:
            print(f"{Fore.RED}Error generating PDF: {str(e)}{Style.RESET_ALL}", file=sys.stderr)
    else:
        print(f"{Fore.YELLOW}No code files were successfully processed{Style.RESET_ALL}")

if __name__ == "__main__":
    colorama.init()
    main()

