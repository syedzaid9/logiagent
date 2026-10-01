from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from app.api.deps import get_db, get_current_user, require_role
from app.models.user import User
from app.models.driver import Driver
from app.models.vehicle import Vehicle
from app.models.shipment import Shipment
from app.models.location import DeliveryLocation
from app.schemas.driver import DriverCreate, DriverUpdate, DriverResponse, DriverStatsResponse

router = APIRouter(prefix="/drivers", tags=["Driver Management"])

ACTIVE_SHIPMENT_STATUSES = ["Assigned", "Picked Up", "In Transit", "Delayed"]

def enrich_driver(d: Driver, db: Session) -> DriverResponse:
    # Query assigned vehicle
    vehicle = db.query(Vehicle).filter(Vehicle.id == d.current_vehicle_id).first() if d.current_vehicle_id else None
    
    # Query active shipments for this driver
    active_shipments = db.query(Shipment).filter(
        Shipment.driver_id == d.id,
        Shipment.status.in_(ACTIVE_SHIPMENT_STATUSES)
    ).order_by(Shipment.created_at.desc()).all()
    
    # Query delivery counts
    completed_count = db.query(func.count(Shipment.id)).filter(
        Shipment.driver_id == d.id,
        Shipment.status == "Delivered"
    ).scalar() or 0
    
    active_count = len(active_shipments)
    primary_active = active_shipments[0] if active_shipments else None
    
    origin_name = None
    dest_name = None
    if primary_active:
        orig = db.query(DeliveryLocation).filter(DeliveryLocation.id == primary_active.origin_id).first()
        dest = db.query(DeliveryLocation).filter(DeliveryLocation.id == primary_active.destination_id).first()
        origin_name = f"{orig.city}, {orig.state}" if orig else None
        dest_name = f"{dest.city}, {dest.state}" if dest else None

    # HOS Compliance calculation
    hos = d.hours_of_service_remaining if d.hours_of_service_remaining is not None else 11.0
    if hos > 2.0:
        hos_status = "Compliant"
    elif hos > 0.0:
        hos_status = "Rest Required Soon"
    else:
        hos_status = "Violation Risk"

    resp = DriverResponse(
        id=d.id,
        driver_code=d.driver_code,
        name=d.name,
        email=d.email,
        phone=d.phone,
        license_number=d.license_number,
        license_type=d.license_type or "CDL-A",
        status=d.status or "Available",
        rating=d.rating if d.rating is not None else 4.8,
        hours_of_service_remaining=hos,
        current_vehicle_id=d.current_vehicle_id,
        current_latitude=d.current_latitude,
        current_longitude=d.current_longitude,
        assigned_vehicle_code=vehicle.vehicle_code if vehicle else None,
        assigned_vehicle_model=vehicle.model if vehicle else None,
        assigned_vehicle_type=vehicle.type if vehicle else None,
        assigned_vehicle_location=vehicle.current_location if vehicle else None,
        active_shipment_code=primary_active.shipment_code if primary_active else None,
        active_shipment_id=primary_active.id if primary_active else None,
        active_shipment_status=primary_active.status if primary_active else None,
        active_shipment_origin=origin_name,
        active_shipment_destination=dest_name,
        active_shipment_weight_kg=primary_active.weight_kg if primary_active else None,
        completed_deliveries_count=completed_count,
        active_deliveries_count=active_count,
        hos_compliance_status=hos_status,
        created_at=d.created_at
    )
    return resp


@router.get("/stats", response_model=DriverStatsResponse)
def get_driver_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["Admin", "Logistics Manager", "Dispatcher", "Fleet Manager"]))
):
    """
    Computes dynamic driver fleet statistics from Supabase records.
    """
    drivers = db.query(Driver).all()
    total = len(drivers)
    
    available = sum(1 for d in drivers if (d.status or "").lower() == "available")
    assigned = sum(1 for d in drivers if (d.status or "").lower() == "assigned")
    on_duty = sum(1 for d in drivers if (d.status or "").lower() == "on duty")
    off_duty = sum(1 for d in drivers if (d.status or "").lower() == "off duty")
    rest = sum(1 for d in drivers if (d.status or "").lower() == "rest")
    deactivated = sum(1 for d in drivers if (d.status or "").lower() == "deactivated")
    
    active_drivers = [d for d in drivers if (d.status or "").lower() != "deactivated"]
    avg_hos = (
        sum(d.hours_of_service_remaining for d in active_drivers if d.hours_of_service_remaining is not None) / len(active_drivers)
        if active_drivers else 11.0
    )
    avg_rating = (
        sum(d.rating for d in active_drivers if d.rating is not None) / len(active_drivers)
        if active_drivers else 4.8
    )
    
    # Query distinct driver IDs with active shipments
    active_shipment_driver_ids = db.query(Shipment.driver_id).filter(
        Shipment.driver_id.isnot(None),
        Shipment.status.in_(ACTIVE_SHIPMENT_STATUSES)
    ).distinct().all()
    drivers_with_active = len(active_shipment_driver_ids)
    
    return DriverStatsResponse(
        total_drivers=total,
        available_drivers=available,
        assigned_drivers=assigned,
        on_duty_drivers=on_duty,
        off_duty_drivers=off_duty,
        rest_drivers=rest,
        deactivated_drivers=deactivated,
        average_hos_remaining=round(avg_hos, 1),
        average_rating=round(avg_rating, 2),
        drivers_with_active_shipments=drivers_with_active
    )


@router.get("", response_model=List[DriverResponse])
def list_drivers(
    search: Optional[str] = Query(None, description="Search across driver code, name, email, phone, license"),
    status: Optional[str] = Query(None, description="Filter by status (Available, Assigned, On Duty, Off Duty, Rest, Deactivated)"),
    license_type: Optional[str] = Query(None, description="Filter by license type (CDL-A, CDL-B, Standard)"),
    min_hos: Optional[float] = Query(None, description="Minimum hours of service remaining"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Driver)

    # Data scope: Driver only sees their own profile
    if current_user.role == "Driver":
        if not current_user.driver_id:
            return []
        query = query.filter(Driver.id == current_user.driver_id)
    
    if search and search.strip():
        term = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Driver.driver_code.ilike(term),
                Driver.name.ilike(term),
                Driver.email.ilike(term),
                Driver.phone.ilike(term),
                Driver.license_number.ilike(term)
            )
        )
    
    if status and status.lower() != "all":
        query = query.filter(Driver.status.ilike(f"%{status.strip()}%"))
    
    if license_type and license_type.lower() != "all":
        query = query.filter(Driver.license_type.ilike(f"%{license_type.strip()}%"))
        
    if min_hos:
        query = query.filter(Driver.hours_of_service_remaining >= min_hos)

    drivers = query.order_by(Driver.name.asc()).all()
    return [enrich_driver(d, db) for d in drivers]


@router.get("/{driver_code}", response_model=DriverResponse)
def get_driver(
    driver_code: str, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    code_clean = driver_code.strip().upper()
    d = db.query(Driver).filter(Driver.driver_code == code_clean).first()
    if not d:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Driver '{driver_code}' not found.")

    # Data scope: Driver can only view their own profile
    if current_user.role == "Driver" and d.id != current_user.driver_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Drivers can only view their own profile."
        )

    return enrich_driver(d, db)


@router.post("", response_model=DriverResponse, status_code=status.HTTP_201_CREATED)
def create_driver(
    driver_in: DriverCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_role(["Admin", "Logistics Manager", "Dispatcher", "Operations Team", "Fleet Manager"]))
):
    code_clean = driver_in.driver_code.strip().upper()
    existing = db.query(Driver).filter(Driver.driver_code == code_clean).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Driver code '{code_clean}' already exists."
        )
        
    license_clean = driver_in.license_number.strip().upper()
    existing_license = db.query(Driver).filter(Driver.license_number == license_clean).first()
    if existing_license:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Commercial license number '{license_clean}' is already registered to {existing_license.name} ({existing_license.driver_code})."
        )

    d_dict = driver_in.dict()
    d_dict["driver_code"] = code_clean
    d_dict["license_number"] = license_clean
    
    # Auto adjust status if vehicle assigned
    if d_dict.get("current_vehicle_id"):
        vehicle = db.query(Vehicle).filter(Vehicle.id == d_dict["current_vehicle_id"]).first()
        if not vehicle:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Assigned vehicle ID {d_dict['current_vehicle_id']} not found."
            )
        if d_dict.get("status") == "Available":
            d_dict["status"] = "Assigned"

    driver = Driver(**d_dict)
    db.add(driver)
    db.flush()

    # Synchronize vehicle assignment if vehicle was assigned
    if driver.current_vehicle_id:
        vehicle = db.query(Vehicle).filter(Vehicle.id == driver.current_vehicle_id).first()
        if vehicle:
            vehicle.driver_id = driver.id
            if vehicle.status == "Available":
                vehicle.status = "Assigned"

    db.commit()
    db.refresh(driver)
    return enrich_driver(driver, db)


@router.put("/{driver_code}", response_model=DriverResponse)
def update_driver(
    driver_code: str,
    update_data: DriverUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    code_clean = driver_code.strip().upper()
    d = db.query(Driver).filter(Driver.driver_code == code_clean).first()
    if not d:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Driver '{driver_code}' not found.")

    # Driver role authorization check
    if current_user.role == "Driver":
        if d.id != current_user.driver_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied. Drivers can only update their own profile.")
        if update_data.license_number and update_data.license_number != d.license_number:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Drivers cannot modify commercial license number.")
        if update_data.current_vehicle_id is not None and update_data.current_vehicle_id != d.current_vehicle_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Drivers cannot reassign vehicles.")
    elif current_user.role not in ["Admin", "Logistics Manager", "Dispatcher", "Operations Team", "Fleet Manager"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized.")

    update_dict = update_data.dict(exclude_unset=True)
    
    # Check license uniqueness if changing license
    if "license_number" in update_dict and update_dict["license_number"]:
        lic_clean = update_dict["license_number"].strip().upper()
        existing_lic = db.query(Driver).filter(Driver.license_number == lic_clean, Driver.id != d.id).first()
        if existing_lic:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"License number '{lic_clean}' is already registered to another driver."
            )
        update_dict["license_number"] = lic_clean

    # Handle Vehicle Assignment Synchronization
    if "current_vehicle_id" in update_dict:
        old_vehicle_id = d.current_vehicle_id
        new_vehicle_id = update_dict["current_vehicle_id"]

        if old_vehicle_id != new_vehicle_id:
            # 1. Release old vehicle if any
            if old_vehicle_id:
                old_v = db.query(Vehicle).filter(Vehicle.id == old_vehicle_id).first()
                if old_v and old_v.driver_id == d.id:
                    old_v.driver_id = None
                    if old_v.status == "Assigned":
                        old_v.status = "Available"
            
            # 2. Claim new vehicle if any
            if new_vehicle_id:
                new_v = db.query(Vehicle).filter(Vehicle.id == new_vehicle_id).first()
                if not new_v:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Vehicle ID {new_vehicle_id} not found."
                    )
                new_v.driver_id = d.id
                if new_v.status == "Available":
                    new_v.status = "Assigned"
                
                # Auto-promote driver status to Assigned if currently Available
                if d.status == "Available" and "status" not in update_dict:
                    update_dict["status"] = "Assigned"
            else:
                # Vehicle unassigned: if driver was Assigned, revert to Available
                if d.status == "Assigned" and "status" not in update_dict:
                    update_dict["status"] = "Available"

    # Apply remaining field updates
    for field, val in update_dict.items():
        setattr(d, field, val)

    db.commit()
    db.refresh(d)
    return enrich_driver(d, db)


@router.delete("/{driver_code}")
def deactivate_driver(
    driver_code: str,
    db: Session = Depends(get_db),
    current_user = Depends(require_role(["Admin", "Logistics Manager", "Fleet Manager"]))
):
    code_clean = driver_code.strip().upper()
    d = db.query(Driver).filter(Driver.driver_code == code_clean).first()
    if not d:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Driver '{driver_code}' not found.")

    # Guard: Prevent deactivation if driver has active shipments
    active_shipments = db.query(Shipment).filter(
        Shipment.driver_id == d.id,
        Shipment.status.in_(ACTIVE_SHIPMENT_STATUSES)
    ).all()

    if active_shipments:
        active_codes = ", ".join(f"'{s.shipment_code}'" for s in active_shipments)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot deactivate driver '{code_clean}': currently assigned to active shipment(s) {active_codes}. Please reassign or deliver shipment first."
        )

    # Release assigned vehicle
    if d.current_vehicle_id:
        v = db.query(Vehicle).filter(Vehicle.id == d.current_vehicle_id).first()
        if v and v.driver_id == d.id:
            v.driver_id = None
            if v.status == "Assigned":
                v.status = "Available"
        d.current_vehicle_id = None

    d.status = "Deactivated"
    db.commit()
    db.refresh(d)

    return {
        "success": True,
        "message": f"Driver '{code_clean}' ({d.name}) deactivated successfully.",
        "driver": enrich_driver(d, db)
    }
