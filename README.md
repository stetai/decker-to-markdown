# Instructions

1. Copy the .py script to another directory to avoid accidentally pushing your html to version control.
2. Setup your environment by installing the required packages (see [below](#setup)).
3. Add a new directory called `html_decks` containing the `.html` decker files. `html_decks` should be on the same level as the `.py` file.
4. Execute the script by running 
    ```bash
    uv run decker2md.py
    ```
    The output `.md` file will be in the same directory as the script.

# Setup

Setup your environment by installing the required packages.

One-time: declares bs4 + lxml as this script's dependencies, writes inline metadata into the file.
```bash 
uv add --script decker2md.py beautifulsoup4 lxml
```

Every time after: creates an isolated env and runs it, installing deps automatically.
```bash
uv run decker2md.py
```