# AI-Powered Social Media Content Generator

This project is a Flask-based web application that generates social media content using various AI providers, including Hugging Face, OpenAI, and Ollama. It allows users to input parameters such as subject, platform, tone, and hashtags to create engaging and shareable posts.

## Features

- **AI Provider Options**: Supports Hugging Face, OpenAI, and Ollama APIs for content generation.
- **Customizable Inputs**: Users can specify the subject, platform, tone, and whether to include hashtags.
- **Fallback Mechanism**: A local fallback option is available if API calls fail.
- **Extensible**: Add new AI providers or enhance existing functionality.

## Requirements

- Python 3.8+
- Flask
- `python-dotenv` for environment variable management
- API keys for Hugging Face and OpenAI (optional)

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd <repository-folder>
    ```