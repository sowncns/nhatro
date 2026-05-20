"""Cache Constants for NhaTro Manager"""

# ─── Cache TTLs (in seconds) ──────────────────────────────────────────────────
TTL_DASHBOARD = 60
TTL_ROOM_LIST = 300
TTL_ROOM_DETAIL = 600
TTL_TENANT_LIST = 300
TTL_TENANT_DETAIL = 300
TTL_INVOICE_LIST = 120
TTL_INVOICE_DETAIL = 120
TTL_UTILITY_LIST = 300
TTL_UTILITY_DETAIL = 300
TTL_CONTRACT_LIST = 300
TTL_CONTRACT_DETAIL = 300

# ─── Cache Key Patterns ────────────────────────────────────────────────────────
# Templates for forming Cache Keys dynamically
CACHE_ROOM_LIST = "rooms:list:{org_id}"
CACHE_ROOM_DETAIL = "rooms:detail:{org_id}:{room_id}"

CACHE_TENANT_LIST = "tenants:list:{org_id}"
CACHE_TENANT_DETAIL = "tenants:detail:{org_id}:{tenant_id}"

CACHE_INVOICE_LIST = "invoices:list:{org_id}"
CACHE_INVOICE_DETAIL = "invoices:detail:{org_id}:{invoice_id}"

CACHE_UTILITY_LIST = "mr:list:{org_id}"
CACHE_UTILITY_DETAIL = "mr:detail:{org_id}:{reading_id}"

CACHE_CONTRACT_LIST = "contracts:list:{org_id}"
CACHE_CONTRACT_DETAIL = "contracts:detail:{org_id}:{contract_id}"

CACHE_DASHBOARD_STATS = "dashboard:stats:{org_id}"
CACHE_DASHBOARD_REV = "dashboard:rev:{org_id}"
CACHE_DASHBOARD_OCC = "dashboard:occ:{org_id}"
