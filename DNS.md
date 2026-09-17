# DNS — academiaobscura.com → GitHub Pages

Updated **2026-09-17** via OVH `v1_domain` MCP (`scripts/ovh-domain-mcp.py`). Zone refreshed.

**Apex A (TTL 300):** GitHub Pages `185.199.108.153` … `.111.153`  
**Apex AAAA:** `2606:50c0:8000::153` … `8003::153`  
**www CNAME:** `glen-w.github.io.`

Kept: NS `dns16`/`ns16`, MX (OVH mail), SPF.

Removed: parking A `213.186.33.5`, ORT redirect TXT to glenwright.earth, ftp CNAME, parking title TXT.

After DNS is green: GitHub Pages → enforce HTTPS.
