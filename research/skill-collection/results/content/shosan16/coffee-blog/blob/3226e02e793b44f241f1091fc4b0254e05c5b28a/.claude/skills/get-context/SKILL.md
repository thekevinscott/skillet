---
name: get-context
description: プロジェクトの全体像を素早く把握するためのコマンド。作業前にプロジェクトのコンテキストを把握する。
user-invocable: false
---

Read README.md, THEN run `git ls-files | grep -v -f (sed 's|^|^|; s|$|/|' .cursorignore | psub)` to understand the context of the project
