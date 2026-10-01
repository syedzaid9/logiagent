from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from app.api.deps import get_db, get_current_user, require_role
from app.models.user import User
from app.models.vehicle import Vehicle
from app.models.driver import Driver
from app.models.shipment import Shipment
from app.models.location import DeliveryLocation
from app.schemas.vehicle import VehicleCreate, VehicleUpdate, VehicleResponse, FleetStatsResponse

router = APIRouter(prefix="/vehicles", tags=["Vehicle Fleet Management"])

def enrich_vehicle(v: Vehicle, db: Session) -> VehicleResponse:
    driver = db.query(Driver).filter(Driver.id == v.driver_id).first() if v.driver_id else None
    
    # Check for active shipment assignment
    active_shipment = db.query(Shipment).filter(
        Shipment.vehicle_id == v.id,
        Shipment.status.in_(["Assigned", "In Transit", "Delayed", "Picked Up"])
    ).first()

    origin_hub = None
    destination_hub = None
    if active_shipment:
        orig = db.query(DeliveryLocation).filter(DeliveryLocation.id == active_shipment.origin_id).first()
        dest = db.query(DeliveryLocation).filter(DeliveryLocation.id == active_shipment.destination_id).first()
        origin_hub = f"{orig.name}, {orig.city}" if orig else None
        destination_hub = f"{dest.name}, {dest.city}" if dest else None

    utilization = round((v.current_load_kg / v.max_capacity_kg) * 100.0, 1) if v.max_capacity_kg > 0 else 0.0
    free_cap = max(0.0, v.max_capacity_kg - v.current_load_kg)
    free_vol = max(0.0, (v.max_volume_m3 or 80.0) - (v.current_volume_m3 or 0.0))

    resp = VehicleResponse.from_orm(v)
    resp.driver_name = driver.name if driver else None
    resp.driver_code = driver.driver_code if driver else None
    resp.driver_phone = driver.phone if driver else None
    resp.utilization_pct = utilization
    resp.available_capacity_kg = free_cap
    resp.available_volume_m3 = free_vol
    resp.active_shipment_code = active_shipment.shipment_code if active_shipment else None
    resp.active_shipment_id = active_shipment.id if active_shipment else None
    resp.active_shipment_status = active_shipment.status if active_shipment else None
    resp.active_shipment_weight_kg = active_shipment.weight_kg if active_shipment else None
    resp.origin_hub = origin_hub
    resp.destination_hub = destination_hub
    return resp

@router.get("/stats", response_model=FleetStatsResponse)
def get_fleet_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["Admin", "Logistics Manager", "Dispatcher", "Fleet Manager"]))
):
    """
    Returns live dynamic fleet metrics and operational KPIs directly from database records.
    """
    total = db.query(func.count(Vehicle.id)).scalar() or 0
    available = db.query(func.count(Vehicle.id)).filter(Vehicle.status == "Available").scalar() or 0
    assigned = db.query(func.count(Vehicle.id)).filter(Vehicle.status == "Assigned").scalar() or 0
    in_transit = db.query(func.count(Vehicle.id)).filter(Vehicle.status == "In Transit").scalar() or 0
    maintenance = db.query(func.count(Vehicle.id)).filter(Vehicle.status == "Maintenance").scalar() or 0
    
    tot_cap = db.query(func.sum(Vehicle.max_capacity_kg)).scalar() or 0.0
    tot_load = db.query(func.sum(Vehicle.current_load_kg)).scalar() or 0.0
    avg_util = round((tot_load / tot_cap) * 100.0, 1) if tot_cap > 0 else 0.0

    return FleetStatsResponse(
        total_vehicles=total,
        available_vehicles=available,
        assigned_vehicles=assigned,
        in_transit_vehicles=in_transit,
        maintenance_vehicles=maintenance,
        average_utilization_pct=avg_util,
        total_fleet_capacity_kg=round(tot_cap, 1),
        total_fleet_load_kg=round(tot_load, 1)
    )

@router.get("", response_model=List[VehicleResponse])
def list_vehicles(
    status: Optional[str] = Query(None, description="Filter by status (Available, Assigned, In Transit, Maintenance, Deactivated)"),
    vehicle_type: Optional[str] = Query(None, description="Filter by vehicle type"),
    search: Optional[str] = Query(None, description="Search by code, model, type, or location"),
    min_capacity_kg: Optional[float] = Query(None, description="Minimum available capacity in kg"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Vehicle)

    # Data scope: Driver only sees their assigned vehicle
    if current_user.role == "Driver":
        if not current_user.driver_id:
            return []
        driver = db.query(Driver).filter(Driver.id == current_user.driver_id).first()
        if not driver or not driver.current_vehicle_id:
            return []
        query = query.filter(Vehicle.id == driver.current_vehicle_id)

    if status and status.lower() != "all":
        query = query.filter(Vehicle.status.ilike(f"%{status}%"))
    if vehicle_type and vehicle_type.lower() != "all":
        query = query.filter(Vehicle.type.ilike(f"%{vehicle_type}%"))
    if search:
        s_clean = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Vehicle.vehicle_code.ilike(s_clean),
                Vehicle.model.ilike(s_clean),
                Vehicle.type.ilike(s_clean),
                Vehicle.current_location.ilike(s_clean)
            )
        )

    vehicles = query.order_by(Vehicle.vehicle_code.asc()).all()
    
    results = []
    for v in vehicles:
        remaining_cap = max(0.0, v.max_capacity_kg - v.current_load_kg)
        if min_capacity_kg is not None and remaining_cap < min_capacity_kg:
            continue
        results.append(enrich_vehicle(v, db))
        
    return results

@router.get("/{vehicle_code}", response_model=VehicleResponse)
def get_vehicle(
    vehicle_code: str, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    code_clean = vehicle_code.strip().upper()
    v = db.query(Vehicle).filter(Vehicle.vehicle_code == code_clean).first()
    if not v:
        v = db.query(Vehicle).filter(Vehicle.vehicle_code.like(f"%{code_clean}%")).first()
    if not v:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Vehicle '{vehicle_code}' not found.")

    # Data scope: Driver cannot access other vehicles
    if current_user.role == "Driver":
        driver = db.query(Driver).filter(Driver.id == current_user.driver_id).first()
        if not driver or v.id != driver.current_vehicle_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. Drivers can only access their assigned vehicle."
            )

    return enrich_vehicle(v, db)

@router.post("", response_model=VehicleResponse, status_code=status.HTTP_201_CREATED)
def create_vehicle(
    vehicle_in: VehicleCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_role(["Admin", "Logistics Manager", "Dispatcher", "Fleet Manager", "Operations Team"]))
):
    code_clean = vehicle_in.vehicle_code.strip().upper()
    existing = db.query(Vehicle).filter(Vehicle.vehicle_code == code_clean).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Vehicle code '{code_clean}' already exists."
        )

    v_dict = vehicle_in.dict()
    v_dict["vehicle_code"] = code_clean
    vehicle = Vehicle(**v_dict)
    
    # If driver is assigned upon creation, update driver status
    if vehicle.driver_id:
        driver = db.query(Driver).filter(Driver.id == vehicle.driver_id).first()
        if driver and driver.status == "Available":
            driver.status = "Assigned"

    db.add(vehicle)
    db.commit()
    db.refresh(vehicle)
    return enrich_vehicle(vehicle, db)

@router.put("/{vehicle_code}", response_model=VehicleResponse)
def update_vehicle(
    vehicle_code: str,
    update_data: VehicleUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(require_role(["Admin", "Logistics Manager", "Dispatcher", "Fleet Manager"]))
):
    code_clean = vehicle_code.strip().upper()
    v = db.query(Vehicle).filter(Vehicle.vehicle_code == code_clean).first()
    if not v:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Vehicle '{vehicle_code}' not found.")

    prev_driver_id = v.driver_id

    # Handle driver reassignment
    if update_data.driver_id is not None and update_data.driver_id != prev_driver_id:
        if prev_driver_id:
            old_d = db.query(Driver).filter(Driver.id == prev_driver_id).first()
            if old_d and old_d.status == "Assigned":
                old_d.status = "Available"
        if update_data.driver_id:
            new_d = db.query(Driver).filter(Driver.id == update_data.driver_id).first()
            if new_d and new_d.status == "Available":
                new_d.status = "Assigned"

    for field, val in update_data.dict(exclude_unset=True).items():
        setattr(v, field, val)

    db.commit()
    db.refresh(v)
    return enrich_vehicle(v, db)

@router.delete("/{vehicle_code}")
def deactivate_vehicle(
    vehicle_code: str,
    db: Session = Depends(get_db),
    current_user = Depends(require_role(["Admin", "Logistics Manager", "Dispatcher", "Fleet Manager"]))
):
    """
    Status-based deactivation preserving historical shipment relationships and telemetry audit trail.
    """
    code_clean = vehicle_code.strip().upper()
    v = db.query(Vehicle).filter(Vehicle.vehicle_code == code_clean).first()
    if not v:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Vehicle '{vehicle_code}' not found.")

    # Check if currently assigned to active shipments
    active_shp = db.query(Shipment).filter(
        Shipment.vehicle_id == v.id,
        Shipment.status.in_(["Assigned", "In Transit", "Delayed", "Picked Up"])
    ).first()

    if active_shp:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot deactivate vehicle '{code_clean}': currently assigned to active shipment '{active_shp.shipment_code}'. Please reassign or deliver shipment first."
        )

    # Release assigned driver if any
    if v.driver_id:
        drv = db.query(Driver).filter(Driver.id == v.driver_id).first()
        if drv and drv.status == "Assigned":
            drv.status = "Available"
        v.driver_id = None

    v.status = "Deactivated"
    v.current_load_kg = 0.0
    v.current_volume_m3 = 0.0
    
    db.commit()
    db.refresh(v)

    return {
        "success": True,
        "message": f"Vehicle '{code_clean}' successfully deactivated.",
        "vehicle": enrich_vehicle(v, db)
    }
