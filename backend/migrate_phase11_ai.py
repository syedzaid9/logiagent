import sys
import os
from sqlalchemy import inspect, text

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import engine, Base
from app.models.alert import Alert

def migrate():
    print("Starting Phase 11 AI & Alerts migration...")
    Base.metadata.create_all(bind=engine)
    
    insp = inspect(engine)
    tables = insp.get_table_names()
    print(f"Current tables in database: {tables}")
    
    if "alerts" in tables:
        indexes = [idx["name"] for idx in insp.get_indexes("alerts")]
        print(f"Alerts table verified with {len(indexes)} indexes: {indexes}")
        print("Phase 11 migration completed successfully!")
        return 0
    else:
        print("ERROR: alerts table was not created!")
        return 1

if __name__ == "__main__":
    sys.exit(migrate())
