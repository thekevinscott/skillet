```
create table emp_skill (
	EMPNO number(3) CONSTRAINT FK_EMPNO references EMP (EMPCODE),
	SKILLID char(3) CONSTRAINT FK_SKILLID references SKILL (SKILLID) ON DELETE CASCADE,
	SKILL_EXPERIENCE number(3) CHECK (SKILL_EXPERIENCE > 0));
  ```
