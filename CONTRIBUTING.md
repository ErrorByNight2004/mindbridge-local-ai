# Contributing to MindBridge

Thanks for your interest in contributing to MindBridge, a local-first mental wellness and CBT-inspired journaling application.

**Maintainer:** Nishanth S Reddy  
**GitHub:** https://github.com/ErrorByNight2004

## Before You Start

- Open an issue before making substantial changes so the scope can be discussed.
- Keep pull requests focused and easy to review.
- Add or update tests when practical.
- Preserve existing license notices and third-party attributions.

## Local Setup

Prerequisites:

- Python compatible with the project's dependencies.
- Git.
- Ollama.
- Sufficient memory and disk space for the selected model and embedding index.

Clone your repository:

```bash
git clone https://github.com/ErrorByNight2004/YOUR-REPOSITORY.git
cd YOUR-REPOSITORY
```

For Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

If PowerShell blocks activation, use Command Prompt instead:

```bat
.venv\Scripts\activate.bat
```

Pull the model configured for your application. For the current Qwen setup:

```bash
ollama pull qwen3.5:4b
```

Start Ollama, then run the backend from the project root:

```bash
python -m uvicorn backend.server:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000` in your browser.

These commands may need adjustment if the repository's dependencies, model configuration, or startup process change.

## Contribution Areas

- CBT knowledge-base quality and retrieval.
- Conversation prompts, memory, and response handling.
- Frontend usability, accessibility, and localization.
- Journaling, mood tracking, assessments, and reports.
- Privacy, security, and safety guardrails.
- Documentation, installation, and testing.

## Pull Requests

Please include:

- A description of what changed and why.
- A link to the related issue, if applicable.
- Screenshots for significant UI changes.
- Tests or manual verification steps.
- Notes about any configuration or migration requirements.

## Privacy and Safety

- Never commit API keys, passwords, `.env` files, personal records, or local databases.
- Do not introduce hosted-model dependencies into local workflows without documenting them.
- Keep mental health claims conservative; the application is not a substitute for professional care.
- Test changes involving user data, model tools, and local service exposure carefully.

## License and Attribution

Contributions must comply with the repository's license and applicable third-party licenses. Preserve required copyright notices and attribution for the original project and other included components.