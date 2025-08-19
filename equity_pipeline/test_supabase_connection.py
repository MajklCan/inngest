#!/usr/bin/env python3
"""
Test Supabase connection
"""

from src.equity_pipeline.config import Config

def test_supabase():
    try:
        config = Config()
        print(f"SUPABASE_URL: {config.supabase_url}")
        print(f"SUPABASE_KEY starts with: {config.supabase_key[:20]}...")
        print(f"SUPABASE_KEY length: {len(config.supabase_key)}")
        
        from src.equity_pipeline.database import DatabaseManager
        db = DatabaseManager(config)
        print("✅ Supabase connection successful!")
        
        # Test fetching companies
        companies = db.fetch_companies(limit=1)
        print(f"✅ Successfully fetched {len(companies)} companies")
        if companies:
            print(f"First company: {companies[0]}")
        
    except Exception as e:
        print(f"❌ Supabase connection failed: {e}")

if __name__ == "__main__":
    test_supabase()