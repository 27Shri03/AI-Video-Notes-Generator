# 🎓 AI-Powered Educational Video Summarizer

![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=Streamlit&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)

A professional web application that extracts, processes, and summarizes YouTube video transcripts using AI.

## ✨ Features

- **YouTube Video Processing**: Accepts any public YouTube URL
- **Transcript Extraction**: Retrieves both manual and auto-generated captions
- **Advanced Text Cleaning**:
  - Removes timestamps and metadata
  - Filters audio artifacts like `[Music]` and `[Applause]`
  - Preserves educational content quality
- **Customizable Limits**: Set word count thresholds (default: 3000 words)
- **Professional UI**:
  - Real-time processing pipeline visualization
  - Expandable transcript viewer
  - Downloadable summaries in Markdown format
  - Responsive design with custom styling

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- pip package manager

## Installation

### Clone repository

```bash
git clone https://github.com/yourusername/ai-video-summarizer.git
```
```bash
cd ai-video-summarizer
```

### Install dependencies
```bash
pip install -r requirements.txt
```

### Run the project

```bash
streamlit run app.py
```



