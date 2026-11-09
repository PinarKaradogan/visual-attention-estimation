# visual-attention-estimation
## Development Setup (Windows)

### Requirements
- Python 3.11.9
- Git

### Installation
```powershell
git clone https://github.com/PinarKaradogan/visual-attention-estimation.git
cd visual-attention-estimation
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
```

### Validation
```powershell
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m pytest tests/test_environment.py -v
.\.venv\Scripts\python.exe -m ruff check tests/test_environment.py
```

Expected result: 3 tests passed and Ruff checks passed.

Do not commit `.venv/`, real participant data or secrets.