alias l := lint
alias t := typecheck

lint:
  ruff format .
  ruff check --fix --select I .
  ruff check .

typecheck:
  mypy .
