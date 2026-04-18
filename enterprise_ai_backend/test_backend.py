"""Shim so `python test_backend.py` still works from the project root."""
from tests.test_backend import main

if __name__ == "__main__":
    main()
