# /tester Skill

테스트 스킬. 테스트 작성 및 실행.

## 사용법

```
/tester
/tester --unit
/tester --arch
```

## 실행 흐름

1. `module_context(class_type="TEST")` → 테스트 규칙 조회
2. 테스트 코드 작성
3. `./gradlew test` 실행
4. 결과 리포트
