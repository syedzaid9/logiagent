import json
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.core.database import Base, engine, SessionLocal
from app.core.security import get_password_hash
from app.models.role import Role, Permission, RolePermission
from app.models.approval_policy import ApprovalPolicy
from app.models.user import User
from app.models.customer import Customer
from app.models.location import DeliveryLocation
from app.models.driver import Driver
from app.models.vehicle import Vehicle
from app.models.order import Order
from app.models.shipment import Shipment, ShipmentStatusHistory
from app.models.route import Route
from app.models.cost import TransportationCost
from app.models.notification import Notification
from app.core.permissions import ALL_SYSTEM_PERMISSIONS, STANDARD_ROLES, ROLE_PERMISSIONS
from app.rag import initialize_rag
from app.core.logging_config import logger

def seed_database(force_recreate: bool = True):
    if force_recreate:
        logger.info("Dropping and recreating all database tables...")
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        
    db: Session = SessionLocal()
    try:
        if not force_recreate and db.query(User).first():
            logger.info("Database already seeded. Skipping.")
            return

        logger.info("Seeding database with realistic logistics operations dataset...")

        # 1. SEED ROLES & PERMISSIONS
        for r_info in STANDARD_ROLES:
            if not db.query(Role).filter(Role.name == r_info["name"]).first():
                db.add(Role(name=r_info["name"], description=r_info["description"]))
        db.commit()

        for p_info in ALL_SYSTEM_PERMISSIONS:
            if not db.query(Permission).filter(Permission.name == p_info["name"]).first():
                db.add(Permission(
                    name=p_info["name"],
                    resource=p_info["resource"],
                    action=p_info["action"],
                    description=p_info["description"]
                ))
        db.commit()

        roles_map = {r.name: r for r in db.query(Role).all()}
        perms_map = {p.name: p for p in db.query(Permission).all()}

        for role_name, perm_set in ROLE_PERMISSIONS.items():
            r_obj = roles_map.get(role_name)
            if not r_obj:
                continue
            for perm_name in perm_set:
                p_obj = perms_map.get(perm_name)
                if p_obj:
                    existing_rp = db.query(RolePermission).filter(
                        RolePermission.role_id == r_obj.id,
                        RolePermission.permission_id == p_obj.id
                    ).first()
                    if not existing_rp:
                        db.add(RolePermission(role_id=r_obj.id, permission_id=p_obj.id))
        db.commit()

        # 2. SEED APPROVAL POLICIES
        policies = [
            ApprovalPolicy(
                role_name="Driver",
                requires_approval=True,
                allowed_approver_roles=json.dumps(["Admin", "Logistics Manager", "Fleet Manager"]),
                description="Commercial driver accounts require manager or admin approval before activation."
            ),
            ApprovalPolicy(
                role_name="Dispatcher",
                requires_approval=True,
                allowed_approver_roles=json.dumps(["Admin", "Logistics Manager"]),
                description="Dispatcher accounts require logistics management approval."
            ),
            ApprovalPolicy(
                role_name="Fleet Manager",
                requires_approval=True,
                allowed_approver_roles=json.dumps(["Admin", "Logistics Manager"]),
                description="Fleet management accounts require director or admin approval."
            ),
            ApprovalPolicy(
                role_name="Logistics Manager",
                requires_approval=True,
                allowed_approver_roles=json.dumps(["Admin"]),
                description="Management accounts require administrator authorization."
            ),
            ApprovalPolicy(
                role_name="Analyst",
                requires_approval=False,
                allowed_approver_roles=json.dumps(["Admin", "Logistics Manager"]),
                description="Analyst accounts can be auto-approved or approved by managers."
            ),
            ApprovalPolicy(
                role_name="Admin",
                requires_approval=True,
                allowed_approver_roles=json.dumps(["Admin"]),
                description="Administrator accounts require primary admin approval."
            )
        ]
        for pol in policies:
            if not db.query(ApprovalPolicy).filter(ApprovalPolicy.role_name == pol.role_name).first():
                db.add(pol)
        db.commit()

        # 3. SEED DELIVERY LOCATIONS (Hubs & Centers)
        locations_data = [
            DeliveryLocation(location_code="HUB-CHI", name="Chicago Central Superhub", address="10500 W Irving Park Rd", city="Chicago", state="IL", postal_code="60666", latitude=41.9742, longitude=-87.9073, hub_type="Distribution Center"),
            DeliveryLocation(location_code="HUB-DFW", name="Dallas-Fort Worth Freight Depot", address="2400 Aviation Dr", city="Dallas", state="TX", postal_code="75261", latitude=32.8998, longitude=-97.0403, hub_type="Distribution Center"),
            DeliveryLocation(location_code="HUB-ATL", name="Atlanta Regional Fulfillment Hub", address="6000 N Terminal Pkwy", city="Atlanta", state="GA", postal_code="30320", latitude=33.6407, longitude=-84.4277, hub_type="Distribution Center"),
            DeliveryLocation(location_code="HUB-LAX", name="Los Angeles Gateway Terminal", address="1 World Way", city="Los Angeles", state="CA", postal_code="90045", latitude=33.9416, longitude=-118.4085, hub_type="Distribution Center"),
            DeliveryLocation(location_code="HUB-JFK", name="New York Metro Logistics Terminal", address="JFK Cargo Bldg 23", city="New York", state="NY", postal_code="11430", latitude=40.6413, longitude=-73.7781, hub_type="Distribution Center"),
            DeliveryLocation(location_code="HUB-SEA", name="Pacific Northwest Logistics Hub", address="17801 International Blvd", city="Seattle", state="WA", postal_code="98158", latitude=47.4502, longitude=-122.3088, hub_type="Warehouse"),
            DeliveryLocation(location_code="HUB-MIA", name="South Florida Cold-Chain Gateway", address="2100 NW 42nd Ave", city="Miami", state="FL", postal_code="33126", latitude=25.7959, longitude=-80.2870, hub_type="Distribution Center"),
            DeliveryLocation(location_code="HUB-DEN", name="Rocky Mountain Regional Hub", address="8500 Peña Blvd", city="Denver", state="CO", postal_code="80249", latitude=39.8561, longitude=-104.6737, hub_type="Warehouse"),
            DeliveryLocation(location_code="HUB-HOU", name="Houston Gulf Logistics Center", address="2800 N Terminal Rd", city="Houston", state="TX", postal_code="77032", latitude=29.9902, longitude=-95.3368, hub_type="Warehouse"),
            DeliveryLocation(location_code="HUB-DET", name="Detroit Automotive Supply Hub", address="2800 W Grand Blvd", city="Detroit", state="MI", postal_code="48202", latitude=42.3653, longitude=-83.0768, hub_type="Fulfillment Hub"),
            DeliveryLocation(location_code="HUB-PHX", name="Phoenix Valley Logistics Park", address="3400 E Sky Harbor Blvd", city="Phoenix", state="AZ", postal_code="85034", latitude=33.4352, longitude=-112.0101, hub_type="Warehouse"),
            DeliveryLocation(location_code="HUB-MEM", name="Memphis Mid-South Freight Terminal", address="2491 Winchester Rd", city="Memphis", state="TN", postal_code="38116", latitude=35.0424, longitude=-89.9767, hub_type="Distribution Center"),
            DeliveryLocation(location_code="SITE-BOS", name="Boston BioMed Receiving Site", address="400 Technology Square", city="Cambridge", state="MA", postal_code="02139", latitude=42.3626, longitude=-71.0906, hub_type="Customer Site"),
            DeliveryLocation(location_code="SITE-SFO", name="Silicon Valley Semiconductor Dock", address="3000 Hanover St", city="Palo Alto", state="CA", postal_code="94304", latitude=37.4275, longitude=-122.1432, hub_type="Customer Site"),
            DeliveryLocation(location_code="SITE-BNA", name="Nashville Retail Distribution Store #402", address="700 Opry Mills Dr", city="Nashville", state="TN", postal_code="37214", latitude=36.1498, longitude=-86.6924, hub_type="Store"),
        ]
        for loc in locations_data:
            if not db.query(DeliveryLocation).filter(DeliveryLocation.location_code == loc.location_code).first():
                db.add(loc)
        db.commit()

        # 4. SEED CUSTOMERS
        customers_data = [
            Customer(customer_code="CUST-101", name="Apex Global Retail", company_name="Apex Retail Corp", email="logistics@apexretail.com", phone="+1-555-0190", tier="Enterprise"),
            Customer(customer_code="CUST-102", name="BioPharma Health Logistics", company_name="BioPharma Global", email="supplychain@biopharma.org", phone="+1-555-0191", tier="Enterprise"),
            Customer(customer_code="CUST-103", name="NovaTech Components", company_name="NovaTech Electronics", email="shipping@novatech.com", phone="+1-555-0192", tier="Enterprise"),
            Customer(customer_code="CUST-104", name="FreshHarvest Organics", company_name="FreshHarvest Farms", email="orders@freshharvest.com", phone="+1-555-0193", tier="Premium"),
            Customer(customer_code="CUST-105", name="Titan Industrial Machinery", company_name="Titan Heavy Industries", email="freight@titanmachinery.com", phone="+1-555-0194", tier="Premium"),
            Customer(customer_code="CUST-106", name="Vanguard Automotive", company_name="Vanguard Motors", email="parts@vanguardauto.com", phone="+1-555-0195", tier="Enterprise"),
            Customer(customer_code="CUST-107", name="Summit Consumer Goods", company_name="Summit Brands LLC", email="supply@summitgoods.com", phone="+1-555-0196", tier="Standard"),
            Customer(customer_code="CUST-108", name="Cascade Beverage Co.", company_name="Cascade Beverages", email="distrib@cascadebev.com", phone="+1-555-0197", tier="Standard"),
            Customer(customer_code="CUST-109", name="Solaris Chem Solutions", company_name="Solaris Chemical Labs", email="hazmat@solarischem.com", phone="+1-555-0198", tier="Premium"),
            Customer(customer_code="CUST-110", name="Horizon Home Goods", company_name="Horizon Logistics Direct", email="dispatch@horizonhome.com", phone="+1-555-0199", tier="Standard"),
        ]
        for c in customers_data:
            if not db.query(Customer).filter(Customer.customer_code == c.customer_code).first():
                db.add(c)
        db.commit()

        # 5. SEED DRIVERS
        drivers_data = [
            Driver(driver_code="DRV-01", name="Robert McCall", email="robert.mccall@logiagent.com", phone="+1-555-0201", license_number="DL-IL-98412", license_type="CDL-A", status="On Duty", rating=4.9, hours_of_service_remaining=6.5, current_latitude=41.9742, current_longitude=-87.9073),
            Driver(driver_code="DRV-02", name="Carlos Mendez", email="carlos.mendez@logiagent.com", phone="+1-555-0202", license_number="DL-TX-44120", license_type="CDL-A", status="Available", rating=4.8, hours_of_service_remaining=10.5, current_latitude=32.8998, current_longitude=-97.0403),
            Driver(driver_code="DRV-03", name="James Kowalski", email="james.k@logiagent.com", phone="+1-555-0203", license_number="DL-GA-77192", license_type="CDL-A", status="On Duty", rating=4.7, hours_of_service_remaining=4.0, current_latitude=33.6407, current_longitude=-84.4277),
            Driver(driver_code="DRV-04", name="Darnell Washington", email="darnell.w@logiagent.com", phone="+1-555-0204", license_number="DL-CA-10294", license_type="CDL-A", status="On Duty", rating=5.0, hours_of_service_remaining=8.0, current_latitude=33.9416, current_longitude=-118.4085),
            Driver(driver_code="DRV-05", name="Aisha Al-Mansoor", email="aisha.m@logiagent.com", phone="+1-555-0205", license_number="DL-NY-66381", license_type="CDL-A", status="Available", rating=4.9, hours_of_service_remaining=11.0, current_latitude=40.6413, current_longitude=-73.7781),
            Driver(driver_code="DRV-06", name="Brian O'Connor", email="brian.oc@logiagent.com", phone="+1-555-0206", license_number="DL-WA-55419", license_type="CDL-A", status="Available", rating=4.6, hours_of_service_remaining=9.5, current_latitude=47.4502, current_longitude=-122.3088),
            Driver(driver_code="DRV-07", name="Mateo Silva", email="mateo.silva@logiagent.com", phone="+1-555-0207", license_number="DL-FL-88210", license_type="CDL-A", status="On Duty", rating=4.8, hours_of_service_remaining=5.2, current_latitude=25.7959, current_longitude=-80.2870),
            Driver(driver_code="DRV-08", name="Travis Vance", email="travis.v@logiagent.com", phone="+1-555-0208", license_number="DL-CO-33190", license_type="CDL-A", status="Available", rating=4.7, hours_of_service_remaining=10.0, current_latitude=39.8561, current_longitude=-104.6737),
            Driver(driver_code="DRV-09", name="Derrick Hall", email="derrick.h@logiagent.com", phone="+1-555-0209", license_number="DL-TN-11928", license_type="CDL-A", status="On Duty", rating=4.9, hours_of_service_remaining=3.5, current_latitude=35.0424, current_longitude=-89.9767),
            Driver(driver_code="DRV-10", name="Frank Castillo", email="frank.c@logiagent.com", phone="+1-555-0210", license_number="DL-MI-99412", license_type="CDL-B", status="Available", rating=4.5, hours_of_service_remaining=11.0, current_latitude=42.3653, current_longitude=-83.0768),
            Driver(driver_code="DRV-11", name="Ethan Miller", email="ethan.m@logiagent.com", phone="+1-555-0211", license_number="DL-AZ-22941", license_type="CDL-B", status="Rest", rating=4.8, hours_of_service_remaining=0.5, current_latitude=33.4352, current_longitude=-112.0101),
            Driver(driver_code="DRV-12", name="Liam Chen", email="liam.chen@logiagent.com", phone="+1-555-0212", license_number="DL-IL-55310", license_type="CDL-A", status="Available", rating=4.9, hours_of_service_remaining=11.0, current_latitude=41.9742, current_longitude=-87.9073),
        ]
        for d in drivers_data:
            if not db.query(Driver).filter(Driver.driver_code == d.driver_code).first():
                db.add(d)
        db.commit()

        # 6. SEED VEHICLES
        vehicles_data = [
            Vehicle(vehicle_code="TRK-101", model="Freightliner Cascadia 126", type="Semi-Truck (Dry Van)", max_capacity_kg=20000.0, current_load_kg=14500.0, status="In Transit", current_location="I-80 Corridor Mile 142", latitude=41.5868, longitude=-87.3456, fuel_level_pct=78.0, fuel_type="Diesel", driver_id=1),
            Vehicle(vehicle_code="TRK-102", model="Volvo VNL 860 Reefer", type="Reefer (Refrigerated)", max_capacity_kg=18000.0, current_load_kg=0.0, status="Available", current_location="Dallas Freight Depot", latitude=32.8998, longitude=-97.0403, fuel_level_pct=95.0, fuel_type="Diesel", driver_id=2),
            Vehicle(vehicle_code="TRK-103", model="Kenworth T680 Heavy", type="Semi-Truck (Dry Van)", max_capacity_kg=22000.0, current_load_kg=18200.0, status="In Transit", current_location="I-75 Southbound GA", latitude=33.8210, longitude=-84.3910, fuel_level_pct=62.0, fuel_type="Diesel", driver_id=3),
            Vehicle(vehicle_code="TRK-104", model="Peterbilt 579 UltraLoft", type="Semi-Truck (Dry Van)", max_capacity_kg=20000.0, current_load_kg=12000.0, status="In Transit", current_location="I-10 Eastbound CA", latitude=34.0522, longitude=-117.5000, fuel_level_pct=84.0, fuel_type="Diesel", driver_id=4),
            Vehicle(vehicle_code="TRK-105", model="International LT Reefer", type="Reefer (Refrigerated)", max_capacity_kg=18000.0, current_load_kg=0.0, status="Available", current_location="JFK Cargo Facility NY", latitude=40.6413, longitude=-73.7781, fuel_level_pct=100.0, fuel_type="Diesel", driver_id=5),
            Vehicle(vehicle_code="TRK-106", model="Mack Anthem Flatbed", type="Flatbed", max_capacity_kg=24000.0, current_load_kg=0.0, status="Available", current_location="Pacific Northwest Hub", latitude=47.4502, longitude=-122.3088, fuel_level_pct=88.0, fuel_type="Diesel", driver_id=6),
            Vehicle(vehicle_code="TRK-107", model="Volvo VNR Electric", type="Box Truck", max_capacity_kg=8500.0, current_load_kg=4200.0, status="In Transit", current_location="Miami Express Turnpike", latitude=25.8600, longitude=-80.2000, fuel_level_pct=72.0, fuel_type="Electric", driver_id=7),
            Vehicle(vehicle_code="TRK-108", model="Freightliner M2 106", type="Box Truck", max_capacity_kg=9000.0, current_load_kg=0.0, status="Available", current_location="Denver Logistics Park", latitude=39.8561, longitude=-104.6737, fuel_level_pct=91.0, fuel_type="Diesel", driver_id=8),
            Vehicle(vehicle_code="TRK-109", model="Kenworth T880 Flatbed", type="Flatbed", max_capacity_kg=25000.0, current_load_kg=19500.0, status="In Transit", current_location="Memphis Freight Hub", latitude=35.0424, longitude=-89.9767, fuel_level_pct=54.0, fuel_type="Diesel", driver_id=9),
            Vehicle(vehicle_code="TRK-110", model="Mercedes-Benz Sprinter 3500", type="Sprinter Van", max_capacity_kg=2500.0, current_load_kg=0.0, status="Available", current_location="Detroit Automotive Hub", latitude=42.3653, longitude=-83.0768, fuel_level_pct=100.0, fuel_type="Diesel", driver_id=10),
            Vehicle(vehicle_code="TRK-111", model="Ford E-Transit Cargo", type="Sprinter Van", max_capacity_kg=2200.0, current_load_kg=0.0, status="Maintenance", current_location="Phoenix Service Center", latitude=33.4352, longitude=-112.0101, fuel_level_pct=40.0, fuel_type="Electric", driver_id=None),
            Vehicle(vehicle_code="TRK-112", model="Freightliner eCascadia", type="Semi-Truck (Dry Van)", max_capacity_kg=19000.0, current_load_kg=0.0, status="Available", current_location="Chicago Central Superhub", latitude=41.9742, longitude=-87.9073, fuel_level_pct=100.0, fuel_type="Electric", driver_id=12),
        ]
        for v in vehicles_data:
            if not db.query(Vehicle).filter(Vehicle.vehicle_code == v.vehicle_code).first():
                db.add(v)
        db.commit()

        # Update driver vehicle mappings
        for d in db.query(Driver).all():
            v = db.query(Vehicle).filter(Vehicle.driver_id == d.id).first()
            if v:
                d.current_vehicle_id = v.id
        db.commit()

        # 7. SEED USERS (with proper driver_id linking)
        def_pwd = get_password_hash("LogiAgent2026!")
        drv1 = db.query(Driver).filter(Driver.driver_code == "DRV-01").first()
        drv2 = db.query(Driver).filter(Driver.driver_code == "DRV-02").first()
        drv3 = db.query(Driver).filter(Driver.driver_code == "DRV-03").first()

        users_data = [
            User(email="admin@logiagent.io", hashed_password=def_pwd, full_name="Sarah Jenkins (Admin)", role="Admin", role_id=getattr(roles_map.get("Admin"), "id", None), is_active=True, account_status="Active", approval_status="Approved"),
            User(email="manager@logiagent.io", hashed_password=def_pwd, full_name="David Vance (Logistics Director)", role="Logistics Manager", role_id=getattr(roles_map.get("Logistics Manager"), "id", None), is_active=True, account_status="Active", approval_status="Approved"),
            User(email="dispatcher@logiagent.io", hashed_password=def_pwd, full_name="Marcus Reed (Senior Dispatcher)", role="Dispatcher", role_id=getattr(roles_map.get("Dispatcher"), "id", None), is_active=True, account_status="Active", approval_status="Approved"),
            User(email="fleet@logiagent.io", hashed_password=def_pwd, full_name="Carlson Vance (Fleet Manager)", role="Fleet Manager", role_id=getattr(roles_map.get("Fleet Manager"), "id", None), is_active=True, account_status="Active", approval_status="Approved"),
            User(email="driver@logiagent.io", hashed_password=def_pwd, full_name="Robert McCall (Commercial Driver)", role="Driver", role_id=getattr(roles_map.get("Driver"), "id", None), driver_id=drv1.id if drv1 else None, is_active=True, account_status="Active", approval_status="Approved"),
            User(email="rajesh@logiagent.io", hashed_password=None, full_name="Rajesh Kumar (Commercial Driver)", role="Driver", role_id=getattr(roles_map.get("Driver"), "id", None), driver_id=drv2.id if drv2 else None, is_active=True, account_status="Active", approval_status="Approved"),
            User(email="raj@logiagent.io", hashed_password=def_pwd, full_name="Rajesh Operational (Driver)", role="Driver", role_id=getattr(roles_map.get("Driver"), "id", None), driver_id=drv3.id if drv3 else None, is_active=True, account_status="Active", approval_status="Approved"),
            User(email="analyst@logiagent.io", hashed_password=def_pwd, full_name="Dr. Aris Thorne (Supply Chain Analyst)", role="Analyst", role_id=getattr(roles_map.get("Analyst"), "id", None), is_active=True, account_status="Active", approval_status="Approved"),
            User(email="ops@logiagent.io", hashed_password=def_pwd, full_name="Elena Rostova (Operations Lead)", role="Operations Team", role_id=getattr(roles_map.get("Operations Team"), "id", None), is_active=True, account_status="Active", approval_status="Approved"),
        ]
        for u in users_data:
            if not db.query(User).filter(User.email == u.email).first():
                db.add(u)
        db.commit()

        # Update driver vehicle mappings
        for d in db.query(Driver).all():
            v = db.query(Vehicle).filter(Vehicle.driver_id == d.id).first()
            if v:
                d.current_vehicle_id = v.id
        db.commit()

        # 8. SEED ORDERS
        now = datetime.utcnow()
        orders_data = []
        for i in range(1, 37):
            cust_id = ((i - 1) % 10) + 1
            orders_data.append(Order(
                order_code=f"ORD-{5000 + i}",
                customer_id=cust_id,
                order_date=now - timedelta(days=(i % 10) + 1),
                total_value=round(1200.0 + (i * 350.75), 2),
                item_count=max(1, (i * 3) % 45),
                status="Shipped" if i <= 20 else "Confirmed" if i <= 30 else "Delivered"
            ))
        for o in orders_data:
            if not db.query(Order).filter(Order.order_code == o.order_code).first():
                db.add(o)
        db.commit()

        # 7. SEED SHIPMENTS (36 Shipments with comprehensive statuses)
        shipments_data = []

        # Key Demo Shipments
        # SHP-1001: The Star In-Transit Shipment (Chicago -> Dallas)
        shipments_data.append(Shipment(
            shipment_code="SHP-1001",
            order_id=1,
            customer_id=1,
            origin_id=1, # Chicago
            destination_id=2, # Dallas
            vehicle_id=1, # TRK-101
            driver_id=1, # Robert McCall
            status="In Transit",
            cargo_type="High-Value Consumer Electronics",
            weight_kg=14500.0,
            volume_m3=55.0,
            temperature_controlled=False,
            current_latitude=41.5868,
            current_longitude=-87.3456,
            current_location_name="I-80 / I-57 Interchange, South Chicagoland",
            pickup_time=now - timedelta(hours=3),
            expected_delivery=now + timedelta(hours=14),
            estimated_eta=now + timedelta(hours=15, minutes=15),
            delay_minutes=75,
            delay_reason="Interstate Highway Construction & High Toll Plaza Congestion",
            delay_risk_score=68.0,
            delay_risk_level="High",
            special_instructions="White-glove delivery; driver must verify serial barcodes upon arrival."
        ))

        # SHP-1002: BioPharma Cold Chain Vaccine (Delayed Reefer)
        shipments_data.append(Shipment(
            shipment_code="SHP-1002",
            order_id=2,
            customer_id=2,
            origin_id=7, # Miami
            destination_id=13, # Boston BioMed
            vehicle_id=5, # TRK-105
            driver_id=5,
            status="Delayed",
            cargo_type="Pharmaceutical Biologics & Vaccines",
            weight_kg=3500.0,
            volume_m3=18.0,
            temperature_controlled=True,
            target_temp_celsius=4.0,
            current_latitude=36.8529,
            current_longitude=-76.2859,
            current_location_name="Norfolk Logistics Staging Hub, VA",
            pickup_time=now - timedelta(hours=18),
            expected_delivery=now + timedelta(hours=4),
            estimated_eta=now + timedelta(hours=8, minutes=30),
            delay_minutes=270,
            delay_reason="Severe Coastal Storm & Mandatory Safety Speed Reduction",
            delay_risk_score=85.0,
            delay_risk_level="Critical",
            special_instructions="Strict +2°C to +8°C temperature logging required. Notify QA if excursion occurs."
        ))

        # SHP-1003: Automotive Parts (Detroit -> Atlanta)
        shipments_data.append(Shipment(
            shipment_code="SHP-1003",
            order_id=3,
            customer_id=6,
            origin_id=10, # Detroit
            destination_id=3, # Atlanta
            vehicle_id=3, # TRK-103
            driver_id=3,
            status="In Transit",
            cargo_type="Precision Transmission Gearboxes",
            weight_kg=18200.0,
            volume_m3=62.0,
            current_latitude=33.8210,
            current_longitude=-84.3910,
            current_location_name="I-75 North Interchange, Atlanta Metro Perimeter",
            pickup_time=now - timedelta(hours=8),
            expected_delivery=now + timedelta(hours=3),
            estimated_eta=now + timedelta(hours=3, minutes=10),
            delay_minutes=10,
            delay_reason="Minor terminal staging queue",
            delay_risk_score=22.0,
            delay_risk_level="Low"
        ))

        # SHP-1004: Solar Chemicals (Dallas -> Houston HAZMAT)
        shipments_data.append(Shipment(
            shipment_code="SHP-1004",
            order_id=4,
            customer_id=9,
            origin_id=2, # Dallas
            destination_id=9, # Houston
            vehicle_id=9,
            driver_id=9,
            status="In Transit",
            cargo_type="Industrial Solvents (Class 3 Flammable)",
            weight_kg=19500.0,
            volume_m3=45.0,
            current_latitude=30.6280,
            current_longitude=-95.5500,
            current_location_name="I-45 South Corridor, Huntsville Staging",
            pickup_time=now - timedelta(hours=2),
            expected_delivery=now + timedelta(hours=3),
            estimated_eta=now + timedelta(hours=3),
            delay_minutes=0,
            delay_reason=None,
            delay_risk_score=15.0,
            delay_risk_level="Low",
            special_instructions="HAZMAT Placarding UN-1993 required. Must bypass metro tunnel corridors."
        ))

        # SHP-1005: Fresh Harvest Organics (Los Angeles -> Seattle Reefer)
        shipments_data.append(Shipment(
            shipment_code="SHP-1005",
            order_id=5,
            customer_id=4,
            origin_id=4, # LAX
            destination_id=6, # Seattle
            vehicle_id=4,
            driver_id=4,
            status="In Transit",
            cargo_type="Organic Fresh Strawberries & Produce",
            weight_kg=12000.0,
            volume_m3=50.0,
            temperature_controlled=True,
            target_temp_celsius=2.5,
            current_latitude=38.5816,
            current_longitude=-121.4944,
            current_location_name="I-5 North Central Valley, Sacramento Hub",
            pickup_time=now - timedelta(hours=9),
            expected_delivery=now + timedelta(hours=12),
            estimated_eta=now + timedelta(hours=12, minutes=20),
            delay_minutes=20,
            delay_reason="Agricultural Checkpoint Inspection",
            delay_risk_score=35.0,
            delay_risk_level="Medium"
        ))

        # SHP-1006: Failed Delivery Exception Test Case (New York -> Boston)
        shipments_data.append(Shipment(
            shipment_code="SHP-1006",
            order_id=6,
            customer_id=3,
            origin_id=5, # New York
            destination_id=13, # Boston
            vehicle_id=None,
            driver_id=None,
            status="Failed",
            cargo_type="Server Rack Equipment",
            weight_kg=2800.0,
            volume_m3=12.0,
            current_latitude=42.3626,
            current_longitude=-71.0906,
            current_location_name="Boston Receiving Bay #2 (Holding)",
            pickup_time=now - timedelta(days=1),
            expected_delivery=now - timedelta(hours=4),
            actual_delivery=None,
            delay_minutes=480,
            delay_reason="Receiver Facility Closed - Unreachable after 3 contact attempts (SOP-LOG-02)",
            delay_risk_score=100.0,
            delay_risk_level="Critical",
            special_instructions="Exception logged EXC-FAIL-01. Subject to 24h grace period re-delivery."
        ))

        # Add 30 additional realistic shipments (SHP-1007 to SHP-1036)
        statuses_cycle = ["Delivered", "Delivered", "In Transit", "Delivered", "Pending", "Assigned", "Picked Up", "Delivered", "Delayed", "In Transit"]
        cargo_types = [
            ("Apex Consumer Electronics", 4500.0, False),
            ("Titan Industrial Bearings", 16000.0, False),
            ("Cascade Bottled Beverages", 18500.0, False),
            ("BioPharma Diagnostic Kits", 2200.0, True),
            ("Summit Paper Goods & Pulp", 14000.0, False),
            ("Vanguard EV Battery Packs", 11000.0, False),
            ("FreshHarvest Frozen Berries", 8500.0, True),
            ("Horizon Furniture Suites", 7800.0, False),
        ]

        for i in range(7, 37):
            code = f"SHP-{1000 + i}"
            st = statuses_cycle[(i - 7) % len(statuses_cycle)]
            c_type, w, is_temp = cargo_types[(i - 7) % len(cargo_types)]
            cust_id = ((i - 7) % 10) + 1
            orig_id = ((i - 7) % 12) + 1
            dest_id = ((i + 3) % 15) + 1
            if orig_id == dest_id:
                dest_id = (dest_id % 15) + 1

            delay_m = 0
            d_reason = None
            risk_sc = 12.0
            risk_lvl = "Low"

            if st == "Delayed":
                delay_m = 45 + ((i * 17) % 180)
                d_reason = "Highway Construction & Detour" if i % 2 == 0 else "Warehouse Inbound Staging Congestion"
                risk_sc = 75.0
                risk_lvl = "High"
            elif st == "In Transit" and i % 3 == 0:
                delay_m = 25
                d_reason = "Moderate Rain Slowdown"
                risk_sc = 52.0
                risk_lvl = "Medium"

            v_id = ((i - 7) % 12) + 1 if st in ["In Transit", "Picked Up", "Delayed", "Delivered"] else None
            drv_id = v_id

            shipment = Shipment(
                shipment_code=code,
                order_id=i,
                customer_id=cust_id,
                origin_id=orig_id,
                destination_id=dest_id,
                vehicle_id=v_id,
                driver_id=drv_id,
                status=st,
                cargo_type=c_type,
                weight_kg=w,
                volume_m3=round(w / 350.0, 1),
                temperature_controlled=is_temp,
                target_temp_celsius=4.0 if is_temp else None,
                pickup_time=now - timedelta(hours=(i * 2) % 48) if st != "Pending" else None,
                expected_delivery=now + timedelta(hours=max(2, 24 - (i % 20))),
                actual_delivery=now - timedelta(hours=2) if st == "Delivered" else None,
                estimated_eta=now + timedelta(hours=max(2, 24 - (i % 20)), minutes=delay_m) if st != "Delivered" else None,
                delay_minutes=delay_m,
                delay_reason=d_reason,
                delay_risk_score=risk_sc,
                delay_risk_level=risk_lvl
            )
            shipments_data.append(shipment)

        for s in shipments_data:
            if not db.query(Shipment).filter(Shipment.shipment_code == s.shipment_code).first():
                db.add(s)
        db.commit()

        # 9. SEED ROUTES & TRANSPORTATION COSTS & STATUS HISTORIES
        for s in db.query(Shipment).all():
            orig = db.query(DeliveryLocation).filter(DeliveryLocation.id == s.origin_id).first()
            dest = db.query(DeliveryLocation).filter(DeliveryLocation.id == s.destination_id).first()
            
            if not orig or not dest:
                continue

            # Approximate distance
            dist = round(abs(orig.latitude - dest.latitude) * 111.0 + abs(orig.longitude - dest.longitude) * 85.0 + 80.0, 1)
            dur = int((dist / 68.0) * 60)
            traffic = "Heavy" if s.delay_minutes > 40 else "Moderate" if s.delay_minutes > 0 else "Light"

            route_code = f"RTE-{s.shipment_code.replace('SHP-', '')}"
            if not db.query(Route).filter(Route.route_code == route_code).first():
                route = Route(
                    route_code=route_code,
                    shipment_id=s.id,
                    origin_id=s.origin_id,
                    destination_id=s.destination_id,
                    planned_distance_km=dist,
                    actual_distance_km=round(dist * 1.04, 1) if s.status in ["In Transit", "Delivered", "Delayed"] else dist,
                    planned_duration_min=dur,
                    actual_duration_min=dur + s.delay_minutes,
                    traffic_condition=traffic,
                    weather_condition="Rain" if s.delay_risk_score > 70 else "Clear",
                    estimated_cost=round(dist * 2.15, 2)
                )
                db.add(route)

            # Cost record
            if not db.query(TransportationCost).filter(TransportationCost.shipment_id == s.id).first():
                fuel = round((dist / 100.0) * 32.0 * 1.15, 2)
                wage = round((dur / 60.0) * 32.0, 2)
                toll = 35.0 if dist > 300 else 15.0
                maint = round(dist * 0.14, 2)
                tot = round(fuel + wage + toll + maint, 2)

                cost = TransportationCost(
                    shipment_id=s.id,
                    vehicle_id=s.vehicle_id,
                    distance_km=dist,
                    fuel_cost=fuel,
                    driver_wage_cost=wage,
                    toll_cost=toll,
                    maintenance_cost=maint,
                    total_cost=tot,
                    cost_per_km=round(tot / dist, 2) if dist > 0 else 2.15
                )
                db.add(cost)

            # History record
            if not db.query(ShipmentStatusHistory).filter(ShipmentStatusHistory.shipment_id == s.id).first():
                hist1 = ShipmentStatusHistory(
                    shipment_id=s.id,
                    status="Created",
                    location_name=orig.name,
                    latitude=orig.latitude,
                    longitude=orig.longitude,
                    notes="Bill of Lading generated and shipment registered in LogiAgent.",
                    timestamp=now - timedelta(hours=36)
                )
                hist2 = ShipmentStatusHistory(
                    shipment_id=s.id,
                    status=s.status,
                    location_name=s.current_location_name or dest.name,
                    latitude=s.current_latitude or dest.latitude,
                    longitude=s.current_longitude or dest.longitude,
                    notes=f"Telemetry checkpoint recorded. Status: {s.status}.",
                    timestamp=now - timedelta(hours=2)
                )
                db.add_all([hist1, hist2])

        db.commit()

        # 10. SEED NOTIFICATIONS
        notifs_data = [
            Notification(title="Severe Delay Alert: SHP-1002 (Cold Chain)", message="BioPharma shipment delayed 4.5h due to coastal storm. Reefer telemetry active at +4.0°C.", notification_type="delay", severity="critical", channel="Push", recipient="ops-team@logiagent.io", status="unread", shipment_id=2),
            Notification(title="Traffic Bottleneck: SHP-1001 (Chicago Corridor)", message="SHP-1001 experiencing 75 min delay on I-80 corridor. ETA updated to 15h 15m.", notification_type="eta_change", severity="high", channel="Email", recipient="manager@logiagent.io", status="unread", shipment_id=1),
            Notification(title="Delivery Failure Logged: SHP-1006", message="Customer receiving dock closed at Boston BioMed. SOP-LOG-02 exception protocol triggered.", notification_type="delivery_failure", severity="critical", channel="SMS", recipient="dispatcher@logiagent.io", status="unread", shipment_id=6),
            Notification(title="Route Clearance: TRK-104", message="I-10 westbound cleared. Resuming normal highway cruise speed.", notification_type="critical_event", severity="low", channel="In-App", recipient="dispatcher@logiagent.io", status="read", shipment_id=4),
            Notification(title="HOS Advisory: Driver Robert McCall", message="Driver has 6.5 hours remaining in driving duty window.", notification_type="critical_event", severity="medium", channel="In-App", recipient="dispatcher@logiagent.io", status="read", shipment_id=1),
        ]
        if db.query(Notification).count() == 0:
            db.add_all(notifs_data)
            db.commit()

        # 9. INITIALIZE RAG VECTOR STORE WITH ALL SOPS
        indexed_chunks_count = initialize_rag()
        logger.info(f"RAG Knowledge Base initialized with {indexed_chunks_count} indexed chunks.")

        logger.info("Database seeding completed successfully!")

    except Exception as e:
        db.rollback()
        logger.error(f"Error during seeding: {e}", exc_info=True)
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
