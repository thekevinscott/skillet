---
name: firebase_ops
description: "Các thao tác vận hành với Firebase Backend."
tools:
  - name: deploy_database_rules
    description: "Chỉ cập nhật Security Rules cho Realtime Database mà không ảnh hưởng hosting."
    executable: firebase
    arguments:
      - "deploy"
      - "--only"
      - "database"
