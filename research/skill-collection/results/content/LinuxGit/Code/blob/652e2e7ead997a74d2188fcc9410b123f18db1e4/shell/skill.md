1. awk last column
```bash
df -h | grep "/$" | awk '{print $(NF-2)}'
```

