About:
This Python script implements a tool for summarizing the contents of code files using a language model (Llama3.2) accessed via a local server called Ollama. 
The tool processes one or more code files, generates summaries, and optionally saves them to an output file.


Run on your machine 
1. Download Ollama :https://ollama.com/download
2. Run the following commands:
    ollama pull llama3.2
    ollama serve
3. Run python codesummarizer.py "path to your file"
