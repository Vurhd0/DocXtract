# DocXtract

**DocXtract** is a simple Python library that extracts all text, symbols, and image references from `.docx` files. It also unzips the `.docx` structure behind the scenes to access embedded media and content for processing.

---

## Features

- Extracts all plain text and special symbols from DOCX files  
- Captures image references and outputs image file paths  
- Automatically unzips the `.docx` (Word) file to access internal structure  
- Cleans and structures output data for easy parsing  

---

## Installation

```bash
pip install DocXtract
```

## Usage

```bash
from DocXtract import DocxExtractor


extractor = DocxExtractor()
data = extractor.extract("sample.docx")
print(data)

```