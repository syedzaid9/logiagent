from sqlalchemy import text, inspect
from app.core.database import engine, SessionLocal, Base
import app.models

INDEX_COMMANDS = [
    # Shipments
    "CREATE INDEX IF NOT EXISTS idx_shipments_status ON shipments(status);",
    "CREATE INDEX IF NOT EXISTS idx_shipments_driver_id ON shipments(driver_id);",
    "CREATE INDEX IF NOT EXISTS idx_shipments_vehicle_id ON shipments(vehicle_id);",
    "CREATE INDEX IF NOT EXISTS idx_shipments_customer_id ON shipments(customer_id);",
    "CREATE INDEX IF NOT EXISTS idx_shipments_origin_id ON shipments(origin_id);",
    "CREATE INDEX IF NOT EXISTS idx_shipments_destination_id ON shipments(destination_id);",
    "CREATE INDEX IF NOT EXISTS idx_shipments_created_at ON shipments(created_at);",
    "CREATE INDEX IF NOT EXISTS idx_shipments_expected_delivery ON shipments(expected_delivery);",
    
    # Shipment History
    "CREATE INDEX IF NOT EXISTS idx_shipment_history_shipment_id ON shipment_status_history(shipment_id);",
    "CREATE INDEX IF NOT EXISTS idx_shipment_history_timestamp ON shipment_status_history(timestamp);",
    "CREATE INDEX IF NOT EXISTS idx_shipment_history_status ON shipment_status_history(status);",
    
    # Routes
    "CREATE INDEX IF NOT EXISTS idx_routes_shipment_id ON routes(shipment_id);",
    "CREATE INDEX IF NOT EXISTS idx_routes_origin_id ON routes(origin_id);",
    "CREATE INDEX IF NOT EXISTS idx_routes_destination_id ON routes(destination_id);",
    "CREATE INDEX IF NOT EXISTS idx_routes_status ON routes(status);",
    "CREATE INDEX IF NOT EXISTS idx_routes_created_at ON routes(created_at);",
    
    # Vehicles
    "CREATE INDEX IF NOT EXISTS idx_vehicles_status ON vehicles(status);",
    "CREATE INDEX IF NOT EXISTS idx_vehicles_type ON vehicles(type);",
    "CREATE INDEX IF NOT EXISTS idx_vehicles_driver_id ON vehicles(driver_id);",
    
    # Drivers
    "CREATE INDEX IF NOT EXISTS idx_drivers_email ON drivers(email);",
    "CREATE INDEX IF NOT EXISTS idx_drivers_status ON drivers(status);",
    "CREATE INDEX IF NOT EXISTS idx_drivers_license_type ON drivers(license_type);",
    "CREATE INDEX IF NOT EXISTS idx_drivers_vehicle_id ON drivers(current_vehicle_id);",
    
    # Users
    "CREATE INDEX IF NOT EXISTS idx_users_role_id ON users(role_id);",
    "CREATE INDEX IF NOT EXISTS idx_users_account_status ON users(account_status);",
    "CREATE INDEX IF NOT EXISTS idx_users_approval_status ON users(approval_status);",
    "CREATE INDEX IF NOT EXISTS idx_users_driver_id ON users(driver_id);",
    "CREATE INDEX IF NOT EXISTS idx_users_activation_token ON users(activation_token);",
    "CREATE INDEX IF NOT EXISTS idx_users_auth_user_id ON users(auth_user_id);",
    
    # Role Permissions Composite
    "CREATE INDEX IF NOT EXISTS idx_role_permissions_composite ON role_permissions(role_id, permission_id);",
    
    # Transportation Costs
    "CREATE INDEX IF NOT EXISTS idx_costs_shipment_id ON transportation_costs(shipment_id);",
    "CREATE INDEX IF NOT EXISTS idx_costs_vehicle_id ON transportation_costs(vehicle_id);"
]

def run_performance_migration():
    print("Running Phase 10 Performance & Database Indexing Migration...")
    
    # Ensure all tables exist
    Base.metadata.create_all(bind=engine)
    
    applied = 0
    with engine.connect() as conn:
        for cmd in INDEX_COMMANDS:
            try:
                conn.execute(text(cmd))
                applied += 1
            except Exception as e:
                print(f"Notice on index command '{cmd}': {e}")
        conn.commit()
        
    print(f"Phase 10 Performance Migration complete! Successfully verified {applied}/{len(INDEX_COMMANDS)} performance indexes.")

if __name__ == "__main__":
    run_performance_migration()
