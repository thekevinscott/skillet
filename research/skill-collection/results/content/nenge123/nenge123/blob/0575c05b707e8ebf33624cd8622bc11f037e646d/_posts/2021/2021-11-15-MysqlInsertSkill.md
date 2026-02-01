---
layout: post
title:  MYSQL 收集
date:   2021-11-15 19:28:39 +0800
category: MySQL
---
### 有则更新无则插入  
> 会查询两次  

```sql
INSERT  INTO `mydb` (`id`, `contents`,`title`)
values ('1','nenge.net','nenge') AS `new` ON DUPLICATE KEY UPDATE
`contents`=`new`.`contents`,`title`=`new`.`title`;
```
