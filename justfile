alias l := lint
alias t := typecheck

lint:
  ruff format .
  ruff check --fix .

typecheck:
  mypy .
