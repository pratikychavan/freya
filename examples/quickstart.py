"""
examples/quickstart.py

The simplest possible Freya example.

Type any objective. Freya detects the domain, plans phases,
then autonomously generates a workspace/<project>/ folder
containing agents/, tools/, and policies/.

Run:
    .venv/bin/python examples/quickstart.py

Example objectives to try:
  • "Create a simple python calculator"
  • "Build a FastAPI server with a single endpoint"
  • "Create a CSV parser utility"
  • "Detect and recover from payment service degradation"
  • "Run a compliance audit for SOC2"
"""
from freya import Freya

freya = Freya()
freya.input()
freya.plan()
freya.run()
