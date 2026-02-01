# /reviewer Skill

코드 리뷰 스킬. Convention Hub 규칙 기반.

## 사용법

```
/reviewer
/reviewer --staged
/reviewer --fix
```

## 실행 흐름

1. `validation_context()` → Zero-Tolerance 규칙 로드
2. 변경 파일 분석
3. 규칙 대조 및 위반 사항 리포트
4. `--fix` 옵션 시 자동 수정
