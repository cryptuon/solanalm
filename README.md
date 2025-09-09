# SolanaLM

A decentralized machine learning platform on Solana.

## Setup

1. Install Poetry if you haven't already:
   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```

2. Install dependencies:
   ```bash
   poetry install
   ```

3. Activate the virtual environment:
   ```bash
   poetry shell
   ```

## Dependencies

This project uses Poetry for dependency management. Key dependencies include:

- PyTorch (installed via pip due to complexity)
- Solana SDK
- Hugging Face Transformers
- FastAPI for web services

## Known Issues

- There are compatibility warnings between NumPy 2.x and PyTorch, but the libraries still function correctly.
- Some dependencies may require additional setup for full functionality.

## Development

- Run tests: `poetry run pytest`
- Format code: `poetry run black .`
- Lint code: `poetry run flake8 .`
- Type check: `poetry run mypy .`

## Verification

To verify that the environment is set up correctly, run:
```bash
poetry run python scripts/verify_setup.py
```