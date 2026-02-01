---
name: deploy
description: Build and deploy the website to Cloudflare Pages
---

Run the deploy script to build and deploy the site:

```bash
sh scripts/deploy.sh
```

This will:
1. Convert any PNG/JPG images to WebP format
2. Rebuild the Haskell project
3. Regenerate the site
4. Deploy to Cloudflare Pages (jxxcarlson.org)
