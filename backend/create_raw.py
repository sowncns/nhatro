import asyncio
import asyncpg
import os

async def main():
    import sys
    sys.path.append('.')
    from app.core.config import settings
    
    url = settings.DATABASE_URL
    if url.startswith('postgresql+asyncpg://'):
        url = url.replace('postgresql+asyncpg://', 'postgresql://')
        
    conn = await asyncpg.connect(url, statement_cache_size=0)
    
    try:
        await conn.execute("CREATE TYPE debtstatus AS ENUM ('OPEN', 'SETTLED', 'WRITTEN_OFF');")
    except Exception as e:
        print("Type debtstatus already exists:", e)

    sql = '''
    CREATE TABLE IF NOT EXISTS debt_records (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        organization_id UUID NOT NULL REFERENCES organizations(id),
        contract_id UUID NOT NULL REFERENCES contracts(id),
        tenant_id UUID NOT NULL REFERENCES tenants(id),
        invoice_id UUID REFERENCES invoices(id),
        amount BIGINT NOT NULL DEFAULT 0,
        status debtstatus NOT NULL DEFAULT 'OPEN',
        risk_flag BOOLEAN DEFAULT false,
        note TEXT,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
        updated_at TIMESTAMP WITH TIME ZONE
    );
    CREATE INDEX IF NOT EXISTS ix_debt_records_tenant_id ON debt_records (tenant_id);
    CREATE INDEX IF NOT EXISTS ix_debt_records_org_status ON debt_records (organization_id, status);
    CREATE INDEX IF NOT EXISTS ix_debt_records_organization_id ON debt_records (organization_id);
    CREATE INDEX IF NOT EXISTS ix_debt_records_contract_id ON debt_records (contract_id);
    '''
    
    await conn.execute(sql)
    await conn.close()
    print("Successfully created debt_records via raw asyncpg")

asyncio.run(main())
