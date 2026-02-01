---
name: alembic-discipline
version: 1.0.0
purpose: >
  Estandarizar migraciones Alembic y procedimientos de rollback.
constraints:
  - request_approval_for_commands
---

# Alembic Discipline Skill
- Definir comandos canónicos (upgrade/downgrade)
- Definir cómo se inicializa DB en DEV
- Evitar scripts sueltos como fuente de verdad (documentar transición)
