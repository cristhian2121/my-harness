# Verification

On backend:
Gold rule: the agent don't say "works", **it proves it**. all feature ends with evidence verified.

on front:
Gold rule: all componet has to be its tests

## Verifications Levels

### level 1 - unit tests (required)

all function inside `back/app`has at least 1 test in `back/tests` with cases what:

- happy path
- at least one error path, possibles errors at the function
