import math
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user, require_role
from app.models.user import User
from app.models.shipment import Shipment, ShipmentStatusHistory
from app.models.location import DeliveryLocation
from app.models.customer import Customer
from app.models.vehicle import Vehicle
from app.models.driver import Driver
from app.models.cost import TransportationCost
from app.models.route import Route
from app.services.maps_service import maps_service
from app.ml.cost_optimizer import cost_optimizer
from app.schemas.shipment import ShipmentCreate, ShipmentUpdate, ShipmentResponse, ShipmentHistoryResponse

router = APIRouter(prefix="/shipments", tags=["Shipments Management"])

def get_canonical_route_distance(db: Session, origin: DeliveryLocation, destination: DeliveryLocation) -> float:
    """
    Retrieves the canonical operational road route distance between two hubs.
    1. First checks for pre-computed highway Route corridors in the database.
    2. Otherwise utilizes maps_service road network calculation (accounting for winding factors).
    """
    db_route = db.query(Route).filter(
        Route.origin_id == origin.id,
        Route.destination_id == destination.id
    ).first()
    if db_route and db_route.planned_distance_km:
        return float(db_route.planned_distance_km)

    calc = maps_service.calculate_distance_and_duration(origin.latitude, origin.longitude, destination.latitude, destination.longitude)
    return float(calc.get("distance_km", 450.0))

def _calc_geo_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(max(50.0, R * c * 1.155), 1)

def enrich_shipment(s: Shipment, db: Session) -> ShipmentResponse:
    customer = db.query(Customer).filter(Customer.id == s.customer_id).first()
    origin = db.query(DeliveryLocation).filter(DeliveryLocation.id == s.origin_id).first()
    dest = db.query(DeliveryLocation).filter(DeliveryLocation.id == s.destination_id).first()
    vehicle = db.query(Vehicle).filter(Vehicle.id == s.vehicle_id).first() if s.vehicle_id else None
    driver = db.query(Driver).filter(Driver.id == s.driver_id).first() if s.driver_id else None
    cost = db.query(TransportationCost).filter(TransportationCost.shipment_id == s.id).first()
    
    history_records = db.query(ShipmentStatusHistory).filter(
        ShipmentStatusHistory.shipment_id == s.id
    ).order_by(ShipmentStatusHistory.timestamp.desc()).all()

    resp = ShipmentResponse.from_orm(s)
    resp.customer_name = customer.name if customer else "N/A"
    resp.origin_name = origin.name if origin else "N/A"
    resp.origin_city = origin.city if origin else "N/A"
    resp.origin_state = origin.state if origin else "N/A"
    resp.destination_name = dest.name if dest else "N/A"
    resp.destination_city = dest.city if dest else "N/A"
    resp.destination_state = dest.state if dest else "N/A"
    resp.vehicle_code = vehicle.vehicle_code if vehicle else None
    resp.driver_name = driver.name if driver else None
    
    if cost:
        resp.cost_total_usd = round(cost.total_cost, 2)
        resp.cost_breakdown = {
            "distance_km": cost.distance_km,
            "fuel_cost": cost.fuel_cost,
            "driver_cost": cost.driver_wage_cost,
            "toll_cost": cost.toll_cost,
            "maintenance_cost": cost.maintenance_cost,
            "cost_per_km": cost.cost_per_km,
            "currency": cost.currency
        }
    else:
        resp.cost_total_usd = None
        resp.cost_breakdown = None

    resp.history = [ShipmentHistoryResponse.from_orm(h) for h in history_records]
    return resp

@router.get("", response_model=List[ShipmentResponse])
def list_shipments(
    status: Optional[str] = Query(None, description="Filter by status"),
    search: Optional[str] = Query(None, description="Search by code, customer, city"),
    delayed_only: bool = Query(False, description="Filter delayed shipments"),
    limit: int = Query(50, le=100),
    offset: int = Query(0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Shipment)

    # Data scope: Driver only sees their own assigned shipments
    if current_user.role == "Driver":
        if not current_user.driver_id:
            return []
        query = query.filter(Shipment.driver_id == current_user.driver_id)
    
    if delayed_only:
        query = query.filter((Shipment.status == "Delayed") | (Shipment.delay_minutes > 0))
    elif status and status.lower() != "all":
        query = query.filter(Shipment.status.ilike(f"%{status}%"))

    if search:
        s_term = f"%{search.strip()}%"
        query = query.filter(
            (Shipment.shipment_code.ilike(s_term)) |
            (Shipment.cargo_type.ilike(s_term)) |
            (Shipment.delay_reason.ilike(s_term))
        )

    shipments = query.order_by(Shipment.created_at.desc()).offset(offset).limit(limit).all()
    if not shipments:
        return []

    # Batch prefetch lookup dicts in 5 single queries
    customer_ids = {s.customer_id for s in shipments if s.customer_id}
    loc_ids = {s.origin_id for s in shipments if s.origin_id} | {s.destination_id for s in shipments if s.destination_id}
    vehicle_ids = {s.vehicle_id for s in shipments if s.vehicle_id}
    driver_ids = {s.driver_id for s in shipments if s.driver_id}
    shipment_ids = {s.id for s in shipments}

    customers_map = {c.id: c for c in db.query(Customer).filter(Customer.id.in_(customer_ids)).all()} if customer_ids else {}
    locs_map = {l.id: l for l in db.query(DeliveryLocation).filter(DeliveryLocation.id.in_(loc_ids)).all()} if loc_ids else {}
    vehicles_map = {v.id: v for v in db.query(Vehicle).filter(Vehicle.id.in_(vehicle_ids)).all()} if vehicle_ids else {}
    drivers_map = {d.id: d for d in db.query(Driver).filter(Driver.id.in_(driver_ids)).all()} if driver_ids else {}
    costs_map = {c.shipment_id: c for c in db.query(TransportationCost).filter(TransportationCost.shipment_id.in_(shipment_ids)).all()} if shipment_ids else {}

    results = []
    for s in shipments:
        customer = customers_map.get(s.customer_id)
        origin = locs_map.get(s.origin_id)
        dest = locs_map.get(s.destination_id)
        vehicle = vehicles_map.get(s.vehicle_id) if s.vehicle_id else None
        driver = drivers_map.get(s.driver_id) if s.driver_id else None
        cost = costs_map.get(s.id)

        resp = ShipmentResponse.model_validate(s)
        resp.customer_name = customer.name if customer else "N/A"
        resp.origin_name = origin.name if origin else "N/A"
        resp.origin_city = origin.city if origin else "N/A"
        resp.origin_state = origin.state if origin else "N/A"
        resp.destination_name = dest.name if dest else "N/A"
        resp.destination_city = dest.city if dest else "N/A"
        resp.destination_state = dest.state if dest else "N/A"
        resp.vehicle_code = vehicle.vehicle_code if vehicle else None
        resp.driver_name = driver.name if driver else None
        
        if cost:
            resp.cost_total_usd = round(cost.total_cost, 2)
            resp.cost_breakdown = {
                "distance_km": cost.distance_km,
                "fuel_cost": cost.fuel_cost,
                "driver_cost": cost.driver_wage_cost,
                "toll_cost": cost.toll_cost,
                "maintenance_cost": cost.maintenance_cost,
                "cost_per_km": cost.cost_per_km,
                "currency": cost.currency
            }
        else:
            resp.cost_total_usd = None
            resp.cost_breakdown = None

        resp.history = []
        results.append(resp)
    return results

@router.get("/meta/customers", response_model=List[dict])
def list_customers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    customers = db.query(Customer).order_by(Customer.name.asc()).all()
    return [
        {
            "id": c.id,
            "customer_code": c.customer_code,
            "name": c.name,
            "company_name": c.company_name,
            "email": c.email,
            "tier": c.tier
        } for c in customers
    ]

@router.get("/{shipment_code}", response_model=ShipmentResponse)
def get_shipment_by_code(
    shipment_code: str, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    code_clean = shipment_code.strip().upper()
    shipment = db.query(Shipment).filter(Shipment.shipment_code == code_clean).first()
    if not shipment:
        shipment = db.query(Shipment).filter(Shipment.shipment_code.like(f"%{code_clean}%")).first()
    
    if not shipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Shipment '{shipment_code}' not found."
        )

    # Data scope: Driver cannot access other drivers' shipments
    if current_user.role == "Driver" and shipment.driver_id != current_user.driver_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Drivers can only access their assigned shipments."
        )

    return enrich_shipment(shipment, db)

@router.post("", response_model=ShipmentResponse, status_code=status.HTTP_201_CREATED)
def create_shipment(
    shipment_in: ShipmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["Admin", "Logistics Manager", "Dispatcher"]))
):
    code_clean = shipment_in.shipment_code.strip().upper()
    existing = db.query(Shipment).filter(Shipment.shipment_code == code_clean).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Shipment code '{code_clean}' already exists."
        )

    # Validate relationships
    customer = db.query(Customer).filter(Customer.id == shipment_in.customer_id).first()
    if not customer:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Customer ID {shipment_in.customer_id} not found.")

    orig = db.query(DeliveryLocation).filter(DeliveryLocation.id == shipment_in.origin_id).first()
    dest = db.query(DeliveryLocation).filter(DeliveryLocation.id == shipment_in.destination_id).first()
    if not orig or not dest:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Origin and destination hubs must exist.")

    # Validate payload capacity if vehicle is assigned
    if shipment_in.vehicle_id:
        veh = db.query(Vehicle).filter(Vehicle.id == shipment_in.vehicle_id).first()
        if veh and shipment_in.weight_kg > veh.max_capacity_kg:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cargo weight {shipment_in.weight_kg:,.1f} kg exceeds vehicle {veh.vehicle_code} maximum capacity of {veh.max_capacity_kg:,.1f} kg."
            )

    shipment_dict = shipment_in.dict()
    shipment_dict["shipment_code"] = code_clean
    shipment_dict["current_location_name"] = orig.name
    shipment_dict["current_latitude"] = orig.latitude
    shipment_dict["current_longitude"] = orig.longitude
    
    shipment = Shipment(**shipment_dict)
    db.add(shipment)
    db.commit()
    db.refresh(shipment)

    # 1. Add initial history event
    hist = ShipmentStatusHistory(
        shipment_id=shipment.id,
        status="Created",
        location_name=orig.name,
        latitude=orig.latitude,
        longitude=orig.longitude,
        notes=shipment.special_instructions or "Shipment registered into LogiAgent operations system.",
        timestamp=datetime.utcnow()
    )
    db.add(hist)

    # 2. Automatically generate and persist TransportationCost record using canonical operational route distance
    dist = get_canonical_route_distance(db, orig, dest)
    vehicle = db.query(Vehicle).filter(Vehicle.id == shipment.vehicle_id).first() if shipment.vehicle_id else None
    v_type = vehicle.type if vehicle else "Semi-Truck (Dry Van)"
    cost_calc = cost_optimizer.calculate_trip_cost(distance_km=dist, vehicle_type=v_type)

    cost_record = TransportationCost(
        shipment_id=shipment.id,
        vehicle_id=shipment.vehicle_id,
        distance_km=dist,
        fuel_cost=cost_calc.get("fuel_cost", 0.0),
        driver_wage_cost=cost_calc.get("driver_cost", 0.0),
        toll_cost=cost_calc.get("toll_cost", 0.0),
        maintenance_cost=cost_calc.get("maintenance_cost", 0.0),
        accessorial_cost=0.0,
        total_cost=cost_calc.get("total_cost", 0.0),
        cost_per_km=cost_calc.get("cost_per_km", 0.0),
        currency="USD",
        calculated_at=datetime.utcnow()
    )
    db.add(cost_record)

    # 3. Update vehicle & driver assignment statuses if present
    if vehicle:
        vehicle.current_load_kg = (vehicle.current_load_kg or 0.0) + shipment.weight_kg
        if vehicle.status == "Available":
            vehicle.status = "Assigned"

    if shipment.driver_id:
        driver = db.query(Driver).filter(Driver.id == shipment.driver_id).first()
        if driver and driver.status == "Available":
            driver.status = "Assigned"

    db.commit()
    db.refresh(shipment)

    return enrich_shipment(shipment, db)

@router.put("/{shipment_code}", response_model=ShipmentResponse)
def update_shipment(
    shipment_code: str,
    update_data: ShipmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    code_clean = shipment_code.strip().upper()
    shipment = db.query(Shipment).filter(Shipment.shipment_code == code_clean).first()
    if not shipment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Shipment '{shipment_code}' not found.")

    # Driver authorization check: Driver can only update their own assigned shipment
    if current_user.role == "Driver":
        if shipment.driver_id != current_user.driver_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. Drivers can only update their own assigned shipments."
            )
        # Driver cannot reassign vehicle, driver, or delete
        if update_data.driver_id is not None and update_data.driver_id != current_user.driver_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Drivers cannot reassign drivers.")
        if update_data.vehicle_id is not None and update_data.vehicle_id != shipment.vehicle_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Drivers cannot reassign vehicles.")
    elif current_user.role not in ["Admin", "Logistics Manager", "Dispatcher", "Operations Team"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized.")

    prev_status = shipment.status
    prev_vehicle_id = shipment.vehicle_id
    prev_driver_id = shipment.driver_id

    # Update basic fields
    for field, val in update_data.dict(exclude_unset=True).items():
        if field != "notes":
            setattr(shipment, field, val)

    # Handle status transitions
    if update_data.status and update_data.status != prev_status:
        new_status = update_data.status
        dest = db.query(DeliveryLocation).filter(DeliveryLocation.id == shipment.destination_id).first()
        
        # When Delivered: record actual delivery timestamp, update location to destination hub, reconcile ETA, and clear active risk
        if new_status == "Delivered":
            if not shipment.actual_delivery:
                shipment.actual_delivery = datetime.utcnow()
            
            # If location wasn't explicitly changed in the update payload or was en-route, set to destination dock
            if not update_data.current_location_name or update_data.current_location_name == shipment.current_location_name:
                if dest:
                    shipment.current_location_name = f"{dest.name}, {dest.city}, {dest.state}" if dest.state else dest.name
                    shipment.current_latitude = dest.latitude
                    shipment.current_longitude = dest.longitude

            shipment.estimated_eta = shipment.actual_delivery
            shipment.delay_risk_score = 0.0
            shipment.delay_risk_level = "Low"

        elif new_status == "Cancelled":
            shipment.delay_risk_score = 0.0
            shipment.delay_risk_level = "Low"

        # If delivered, cancelled, or failed, release assigned vehicle & driver
        if new_status in ["Delivered", "Cancelled", "Failed"]:
            if shipment.vehicle_id:
                veh = db.query(Vehicle).filter(Vehicle.id == shipment.vehicle_id).first()
                if veh:
                    veh.current_load_kg = max(0.0, (veh.current_load_kg or 0.0) - shipment.weight_kg)
                    if veh.current_load_kg == 0.0 and veh.status in ["Assigned", "In Transit"]:
                        veh.status = "Available"
            if shipment.driver_id:
                drv = db.query(Driver).filter(Driver.id == shipment.driver_id).first()
                if drv and drv.status in ["Assigned", "On Duty"]:
                    drv.status = "Available"

        hist = ShipmentStatusHistory(
            shipment_id=shipment.id,
            status=new_status,
            location_name=shipment.current_location_name or (dest.name if dest else "Facility"),
            latitude=shipment.current_latitude or (dest.latitude if dest else None),
            longitude=shipment.current_longitude or (dest.longitude if dest else None),
            notes=update_data.notes or (
                f"Delivered successfully at {shipment.current_location_name}."
                if new_status == "Delivered"
                else f"Status transition from {prev_status} to {new_status}."
            ),
            timestamp=datetime.utcnow()
        )
        db.add(hist)

    # Handle vehicle reassignment
    if update_data.vehicle_id is not None and update_data.vehicle_id != prev_vehicle_id:
        if prev_vehicle_id:
            old_veh = db.query(Vehicle).filter(Vehicle.id == prev_vehicle_id).first()
            if old_veh:
                old_veh.current_load_kg = max(0.0, (old_veh.current_load_kg or 0.0) - shipment.weight_kg)
                if old_veh.current_load_kg == 0.0 and old_veh.status in ["Assigned", "In Transit"]:
                    old_veh.status = "Available"
        if update_data.vehicle_id:
            new_veh = db.query(Vehicle).filter(Vehicle.id == update_data.vehicle_id).first()
            if new_veh:
                w = update_data.weight_kg or shipment.weight_kg
                if w > new_veh.max_capacity_kg:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Cargo weight {w:,.1f} kg exceeds vehicle {new_veh.vehicle_code} maximum capacity of {new_veh.max_capacity_kg:,.1f} kg."
                    )
                new_veh.current_load_kg = (new_veh.current_load_kg or 0.0) + shipment.weight_kg
                if new_veh.status == "Available":
                    new_veh.status = "Assigned"

    # Handle driver reassignment
    if update_data.driver_id is not None and update_data.driver_id != prev_driver_id:
        if prev_driver_id:
            old_drv = db.query(Driver).filter(Driver.id == prev_driver_id).first()
            if old_drv and old_drv.status == "Assigned":
                old_drv.status = "Available"
        if update_data.driver_id:
            new_drv = db.query(Driver).filter(Driver.id == update_data.driver_id).first()
            if new_drv and new_drv.status == "Available":
                new_drv.status = "Assigned"
            if shipment.status in ["Delivered", "Created", "Pending"]:
                shipment.status = "Assigned"

    db.commit()
    db.refresh(shipment)
    return enrich_shipment(shipment, db)

@router.delete("/{shipment_code}")
def cancel_shipment(
    shipment_code: str,
    db: Session = Depends(get_db),
    current_user = Depends(require_role(["Admin", "Logistics Manager", "Dispatcher"]))
):
    """
    Status-based cancellation preserving historical audit records per system architecture.
    """
    code_clean = shipment_code.strip().upper()
    shipment = db.query(Shipment).filter(Shipment.shipment_code == code_clean).first()
    if not shipment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Shipment '{shipment_code}' not found.")

    prev_status = shipment.status
    shipment.status = "Cancelled"
    
    # Release vehicle and driver
    if shipment.vehicle_id:
        veh = db.query(Vehicle).filter(Vehicle.id == shipment.vehicle_id).first()
        if veh:
            veh.current_load_kg = max(0.0, (veh.current_load_kg or 0.0) - shipment.weight_kg)
            if veh.current_load_kg == 0.0 and veh.status in ["Assigned", "In Transit"]:
                veh.status = "Available"
    if shipment.driver_id:
        drv = db.query(Driver).filter(Driver.id == shipment.driver_id).first()
        if drv and drv.status in ["Assigned", "On Duty"]:
            drv.status = "Available"

    hist = ShipmentStatusHistory(
        shipment_id=shipment.id,
        status="Cancelled",
        location_name=shipment.current_location_name,
        latitude=shipment.current_latitude,
        longitude=shipment.current_longitude,
        notes="Shipment cancelled by logistics operator.",
        timestamp=datetime.utcnow()
    )
    db.add(hist)
    db.commit()
    db.refresh(shipment)

    return {
        "success": True,
        "message": f"Shipment '{code_clean}' successfully cancelled.",
        "shipment": enrich_shipment(shipment, db)
    }

