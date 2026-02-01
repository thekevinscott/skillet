---
name: convert-images
description: Convert PNG/JPG images to WebP format
---

Run the image conversion script:

```bash
sh scripts/convert-images.sh
```

This will:
1. Find all PNG/JPG images in media/images/
2. Move originals to media/images-original/
3. Convert to WebP at 85% quality
4. Report size savings
