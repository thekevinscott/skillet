# LSP Dependency Analysis Skill

## When to Use

When you need to map incoming and outgoing dependencies for a module or file.

## Steps

1. Use **find-references** to identify all places that import or call from the module
2. Use **go-to-definition** to follow dependency chains
3. Map both incoming (who uses this) and outgoing (what this uses) dependencies
