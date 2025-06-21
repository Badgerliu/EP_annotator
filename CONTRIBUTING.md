# Contributing to EP_annotator

Thank you for your interest in contributing to EP_annotator!

## Development Setup

1. Clone the repository (requires access to private repo):
```bash
git clone https://github.com/Badgerliu/EP_annotator.git
cd EP_annotator
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Install the package in development mode:
```bash
pip install -e .
```

## Development Workflow

1. Create a new branch for your feature:
```bash
git checkout -b feature/your-feature-name
```

2. Make your changes and commit them:
```bash
git add .
git commit -m "Add your descriptive commit message"
```

3. Push your branch and create a pull request:
```bash
git push origin feature/your-feature-name
```

## Code Style

- Use Black for code formatting: `black src/`
- Use flake8 for linting: `flake8 src/`
- Write tests for new functionality in the `tests/` directory

## Testing

Run tests with pytest:
```bash
pytest tests/
```

## Project Structure

```
EP_annotator/
├── src/ep_annotator/          # Main package code
├── tests/                     # Test files
├── docs/                      # Documentation
├── examples/                  # Usage examples
├── original_code/             # Original reference code (not in git)
├── requirements.txt           # Python dependencies
└── README.md                  # Project documentation
```

## Data Files

Large data files (*.allValidPairs, *.bed, etc.) are excluded from version control.
Keep them in the `original_code/` directory or create a separate `data/` directory for your datasets. 