# DNS — academiaobscura.com → GitHub Pages

Verified **2026-09-17** via OVH `v1_domain` MCP (`Documents/server/scripts/ovh-domain-mcp.py`). Zone refreshed again.

**Apex A (TTL 300):** GitHub Pages `185.199.108.153` … `.111.153`  
**Apex AAAA:** `2606:50c0:8000::153` … `8003::153`  
**www CNAME:** `glen-w.github.io.`

Kept: NS `dns16`/`ns16`, MX (OVH mail), SPF.

Removed earlier: parking A `213.186.33.5`, ORT redirect TXT to glenwright.earth, ftp CNAME, parking title TXT.

Public resolvers (`8.8.8.8`, `1.1.1.1`) already return the GitHub A records. HTTP on the custom domain works. GitHub custom-domain TLS cert is **not issued yet** — Enforce HTTPS returns “certificate does not exist yet”; re-check Settings → Pages in a bit (often minutes–hours after DNS is correct).
