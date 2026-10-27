# MindBridge — Local-First CBT Journal and AI Mental Wellness Assistant

MindBridge is a local-first mental wellness application that combines CBT-inspired self-reflection, journaling, mood and sleep tracking, and conversational AI powered by Ollama.

This repository contains my modifications to the original MindBridge/CBT assistant project. The goal is to maintain a practical local application while improving its configuration, model integration, documentation, and development workflow.

## Maintainer

**Nishanth S Reddy**

- GitHub: https://github.com/ErrorByNight2004

## Features

Depending on the components enabled in your checkout, MindBridge includes:

- **Thought Diary:** Record situations, automatic thoughts, emotions, and alternative perspectives.
- **Mood and Sleep Tracking:** Record daily mood and sleep information.
- **Self-Reflection Exercises:** Use structured CBT-inspired exercises to examine thought patterns.
- **AI Chat Assistant:** Have supportive conversations with a locally running Ollama model.
- **Knowledge Retrieval:** Retrieve relevant material from a local knowledge base when the retrieval system is available.
- **Personal Records:** Store supported journal entries and conversation history locally.

## Requirements

- Windows, macOS, or Linux, depending on the available launch scripts.
- Python and the dependencies specified by `requirements.txt`.
- Ollama installed and running.
- Sufficient RAM and disk space for the selected language model and embedding model.

## Installation

Clone your own repository:

```bash
git clone https://github.com/ErrorByNight2004/YOUR-REPOSITORY.git
cd YOUR-REPOSITORY
```

Create and activate a Python virtual environment on Windows:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Pull the Qwen model configured for the current application:

```bash
ollama pull qwen3.5:4b
```

Start the backend from the project root:

```bash
python -m uvicorn backend.server:app --host 127.0.0.1 --port 8000
```

Then open:

http://127.0.0.1:8000

If your checkout includes a supported launcher, you may use it instead after verifying its model and environment settings.

## Configuration

The model settings are defined in `config/model_config.yaml`. The application also supports persisted model selection through its settings mechanism.

Review the selected model, generation parameters, and local data directories before running the application.

## Privacy and Safety

MindBridge is intended for self-reflection and general wellness support. It is not a therapist, medical device, emergency service, or substitute for professional mental health care.

Local model inference does not automatically mean every feature is offline. Optional voice, media, or other integrations may use external services. Review the application's configuration and privacy documentation before using sensitive information.

Do not expose the local server to untrusted networks without first addressing authentication, CORS, and other security requirements.

## Development and Contributions

See [CONTRIBUTING.md](CONTRIBUTING.md) for setup and contribution guidance.

Please report security vulnerabilities using the process in [SECURITY.md](SECURITY.md), rather than public issues.

## Original Project and License

This repository is based on an existing project originally attributed to KazKozDev. The original MIT License and required copyright notices must be preserved.

My changes are documented as modifications to that project; original authorship and third-party attributions remain acknowledged.

See [LICENSE](LICENSE) for the applicable license terms.