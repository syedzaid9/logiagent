import json
import random
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from datetime import datetime, timedelta

from app.api.deps import get_db, get_current_user, require_role
from app.models.user import User
from app.models.route import Route
from app.models.shipment import Shipment
from app.models.location import DeliveryLocation
from app.models.vehicle import Vehicle
from app.models.driver import Driver
from app.models.customer import Customer
from app.models.cost import TransportationCost
from app.schemas.route import (
    RouteCreate,
    RouteUpdate,
    RouteCalculateRequest,
    RouteOptimizeRequest,
    RouteStatsResponse,
    RouteResponse,
    Waypoint
)
from app.services.maps_service import maps_service
from app.ml.cost_optimizer import cost_optimizer
from app.tools.route_optimization_tool import route_optimization_tool
from app.core.rate_limiter import rate_limit
from app.core.config import settings

router = APIRouter(prefix="/routes", tags=["Route Optimization & Maps"])

def derive_route_status(r: Route, shipment: Optional[Shipment]) -> str:
    if r.status and r.status != "Planned":
        return r.status
    if not shipment:
        return "Planned"
    
    st = shipment.status
    if st == "Delivered":
        return "Completed"
    elif st == "Cancelled":
        return "Cancelled"
    elif st in ["In Transit", "Picked Up"]:
        return "In Transit"
    elif st == "Delayed":
        return "Delayed"
    elif st == "Assigned":
        return "Assigned"
    return "Planned"

def generate_route_telemetry(origin: DeliveryLocation, dest: DeliveryLocation, distance_km: float):
    mid_lat = (origin.latitude + dest.latitude) / 2
    mid_lng = (origin.longitude + dest.longitude) / 2
    
    waypoints = [
        {
            "name": f"Origin: {origin.name}",
            "location": f"{origin.city}, {origin.state}",
            "lat": origin.latitude,
            "lng": origin.longitude,
            "type": "Origin",
            "estimated_arrival": "0m (Departure)"
        },
        {
            "name": "Interstate Logistics Rest & Inspection Depot",
            "location": "Corridor Inspection Checkpoint",
            "lat": round(mid_lat, 4),
            "lng": round(mid_lng, 4),
            "type": "Fuel & Rest",
            "estimated_arrival": f"{int((distance_km / 140.0) * 60)}m"
        },
        {
            "name": f"Destination: {dest.name}",
            "location": f"{dest.city}, {dest.state}",
            "lat": dest.latitude,
            "lng": dest.longitude,
            "type": "Destination",
            "estimated_arrival": f"{int((distance_km / 70.0) * 60)}m"
        }
    ]

    polyline = [
        [origin.latitude, origin.longitude],
        [round(mid_lat + 0.15, 4), round(mid_lng - 0.20, 4)],
        [round(mid_lat, 4), round(mid_lng, 4)],
        [round(mid_lat - 0.10, 4), round(mid_lng + 0.15, 4)],
        [dest.latitude, dest.longitude]
    ]

    return waypoints, polyline

def enrich_route(r: Route, db: Session, preloaded: Optional[dict] = None) -> RouteResponse:
    if preloaded:
        orig = preloaded["locations"].get(r.origin_id)
        dest = preloaded["locations"].get(r.destination_id)
        shipment = preloaded["shipments"].get(r.shipment_id) if r.shipment_id else None
        customer = preloaded["customers"].get(shipment.customer_id) if shipment and shipment.customer_id else None
        v_id = shipment.vehicle_id if shipment else None
        vehicle = preloaded["vehicles"].get(v_id) if v_id else None
        d_id = shipment.driver_id if shipment else None
        driver = preloaded["drivers"].get(d_id) if d_id else None
        cost = preloaded["costs"].get(shipment.id) if shipment else None
    else:
        orig = db.query(DeliveryLocation).filter(DeliveryLocation.id == r.origin_id).first() if r.origin_id else None
        dest = db.query(DeliveryLocation).filter(DeliveryLocation.id == r.destination_id).first() if r.destination_id else None
        shipment = db.query(Shipment).filter(Shipment.id == r.shipment_id).first() if r.shipment_id else None
        customer = db.query(Customer).filter(Customer.id == shipment.customer_id).first() if shipment and shipment.customer_id else None
        v_id = shipment.vehicle_id if shipment else None
        vehicle = db.query(Vehicle).filter(Vehicle.id == v_id).first() if v_id else None
        d_id = shipment.driver_id if shipment else None
        driver = db.query(Driver).filter(Driver.id == d_id).first() if d_id else None
        cost = db.query(TransportationCost).filter(TransportationCost.shipment_id == shipment.id).first() if shipment else None

    orig_name = orig.name if orig else "Unknown Hub"
    orig_city = orig.city if orig else "Unknown City"
    orig_state = orig.state if orig else "US"
    orig_lat = orig.latitude if orig else 39.50
    orig_lng = orig.longitude if orig else -98.35

    dest_name = dest.name if dest else "Unknown Destination"
    dest_city = dest.city if dest else "Unknown City"
    dest_state = dest.state if dest else "US"
    dest_lat = dest.latitude if dest else 39.50
    dest_lng = dest.longitude if dest else -98.35

    # Parse or compute waypoints & polyline
    waypoints_data = []
    if r.waypoints_json:
        try:
            raw_w = json.loads(r.waypoints_json)
            waypoints_data = [Waypoint(**w) if isinstance(w, dict) else w for w in raw_w]
        except Exception:
            pass
            
    polyline_data = []
    if r.polyline_json:
        try:
            polyline_data = json.loads(r.polyline_json)
        except Exception:
            pass

    if not waypoints_data and orig and dest:
        wps, poly = generate_route_telemetry(orig, dest, r.planned_distance_km)
        waypoints_data = [Waypoint(**w) for w in wps]
        if not polyline_data:
            polyline_data = poly

    route_st = derive_route_status(r, shipment)
    
    # ETA Projection string
    eta_str = None
    if shipment:
        if shipment.status == "Delivered":
            del_time = shipment.actual_delivery.strftime("%Y-%m-%d %H:%M UTC") if shipment.actual_delivery else "Delivered"
            eta_str = f"Completed ({del_time})"
        elif shipment.estimated_eta:
            eta_str = shipment.estimated_eta.strftime("%Y-%m-%d %H:%M UTC")
        else:
            eta_str = f"+{r.planned_duration_min // 60}h {r.planned_duration_min % 60}m"

    v_type = vehicle.type if vehicle else "Semi-Truck (Dry Van)"
    calc_cost = cost.total_cost if cost else (r.estimated_cost or cost_optimizer.calculate_trip_cost(r.planned_distance_km, vehicle_type=v_type).get("total_cost", 0.0))

    return RouteResponse(
        id=r.id,
        route_code=r.route_code,
        status=route_st,
        shipment_id=r.shipment_id,
        shipment_code=shipment.shipment_code if shipment else None,
        shipment_status=shipment.status if shipment else None,
        cargo_type=shipment.cargo_type if shipment else None,
        weight_kg=shipment.weight_kg if shipment else None,
        customer_name=customer.name if customer else None,
        origin_id=r.origin_id,
        origin_code=orig.location_code if orig else None,
        origin_name=orig_name,
        origin_city=orig_city,
        origin_state=orig_state,
        origin_lat=orig_lat,
        origin_lng=orig_lng,
        destination_id=r.destination_id,
        destination_code=dest.location_code if dest else None,
        destination_name=dest_name,
        destination_city=dest_city,
        destination_state=dest_state,
        destination_lat=dest_lat,
        destination_lng=dest_lng,
        vehicle_id=vehicle.id if vehicle else None,
        vehicle_code=vehicle.vehicle_code if vehicle else None,
        vehicle_model=vehicle.model if vehicle else None,
        vehicle_type=vehicle.type if vehicle else None,
        vehicle_status=vehicle.status if vehicle else None,
        driver_id=driver.id if driver else None,
        driver_code=driver.driver_code if driver else None,
        driver_name=driver.name if driver else None,
        driver_phone=driver.phone if driver else None,
        driver_hos_remaining=driver.hours_of_service_remaining if driver else None,
        planned_distance_km=r.planned_distance_km,
        actual_distance_km=r.actual_distance_km,
        planned_duration_min=r.planned_duration_min,
        actual_duration_min=r.actual_duration_min,
        traffic_condition=r.traffic_condition or "Moderate",
        weather_condition=r.weather_condition or "Clear",
        estimated_cost=calc_cost,
        cost_total_usd=calc_cost,
        cost_per_km=cost.cost_per_km if cost else round(calc_cost / max(1.0, r.planned_distance_km), 2),
        fuel_cost=cost.fuel_cost if cost else round(calc_cost * 0.36, 2),
        driver_cost=cost.driver_wage_cost if cost else round(calc_cost * 0.48, 2),
        toll_cost=cost.toll_cost if cost else 25.0,
        maintenance_cost=cost.maintenance_cost if cost else round(calc_cost * 0.14, 2),
        eta_projection=eta_str,
        delay_minutes=shipment.delay_minutes if shipment else 0,
        waypoints=waypoints_data,
        polyline=polyline_data,
        created_at=r.created_at
    )


@router.get("/stats", response_model=RouteStatsResponse)
def get_route_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["Admin", "Logistics Manager", "Dispatcher", "Fleet Manager"]))
):
    """
    Computes dynamic route network statistics from Supabase database.
    """
    routes = db.query(Route).all()
    total = len(routes)
    if total == 0:
        return RouteStatsResponse(
            total_routes=0,
            active_routes=0,
            planned_routes=0,
            completed_routes=0,
            delayed_routes=0,
            average_distance_km=0.0,
            average_duration_min=0,
            average_efficiency_pct=100.0,
            total_network_distance_km=0.0
        )

    # Prefetch shipments for status mapping
    shipment_ids = [r.shipment_id for r in routes if r.shipment_id]
    shipments = db.query(Shipment).filter(Shipment.id.in_(shipment_ids)).all() if shipment_ids else []
    shipments_map = {s.id: s for s in shipments}

    active_count = 0
    completed_count = 0
    delayed_count = 0
    planned_count = 0
    total_dist = 0.0
    total_dur = 0

    for r in routes:
        shp = shipments_map.get(r.shipment_id)
        st = derive_route_status(r, shp)
        if st in ["In Transit", "Assigned"]:
            active_count += 1
        elif st == "Completed":
            completed_count += 1
        elif st == "Delayed":
            delayed_count += 1
        else:
            planned_count += 1

        total_dist += r.planned_distance_km or 0.0
        total_dur += r.planned_duration_min or 0

    avg_dist = round(total_dist / total, 1)
    avg_dur = int(total_dur / total)
    
    # Efficiency is ratio of completed/on-time vs total active
    efficiency = round(max(75.0, min(98.5, 100.0 - (delayed_count / max(1, total) * 100.0))), 1)

    return RouteStatsResponse(
        total_routes=total,
        active_routes=active_count,
        planned_routes=planned_count,
        completed_routes=completed_count,
        delayed_routes=delayed_count,
        average_distance_km=avg_dist,
        average_duration_min=avg_dur,
        average_efficiency_pct=efficiency,
        total_network_distance_km=round(total_dist, 1)
    )


@router.get("", response_model=List[RouteResponse])
def list_routes(
    search: Optional[str] = Query(None, description="Search route code, shipment code, city, vehicle, driver"),
    status: Optional[str] = Query(None, description="Filter status (Planned, Assigned, In Transit, Delayed, Completed, Cancelled)"),
    origin_id: Optional[int] = Query(None, description="Filter by origin hub ID"),
    destination_id: Optional[int] = Query(None, description="Filter by destination hub ID"),
    vehicle_id: Optional[int] = Query(None, description="Filter by vehicle ID"),
    driver_id: Optional[int] = Query(None, description="Filter by driver ID"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Route)

    # Data scope: Driver only sees their assigned shipment routes
    if current_user.role == "Driver":
        if not current_user.driver_id:
            return []
        driver_shp_ids = [s.id for s in db.query(Shipment.id).filter(Shipment.driver_id == current_user.driver_id).all()]
        if not driver_shp_ids:
            return []
        query = query.filter(Route.shipment_id.in_(driver_shp_ids))

    if origin_id:
        query = query.filter(Route.origin_id == origin_id)
    if destination_id:
        query = query.filter(Route.destination_id == destination_id)

    routes = query.order_by(Route.created_at.desc()).offset(offset).limit(limit).all()
    if not routes:
        return []

    # Bulk load related records for maximum performance
    loc_ids = set()
    shp_ids = set()
    for r in routes:
        if r.origin_id: loc_ids.add(r.origin_id)
        if r.destination_id: loc_ids.add(r.destination_id)
        if r.shipment_id: shp_ids.add(r.shipment_id)

    locations_map = {l.id: l for l in db.query(DeliveryLocation).filter(DeliveryLocation.id.in_(loc_ids)).all()} if loc_ids else {}
    shipments_map = {s.id: s for s in db.query(Shipment).filter(Shipment.id.in_(shp_ids)).all()} if shp_ids else {}
    
    cust_ids = {s.customer_id for s in shipments_map.values() if s.customer_id}
    veh_ids = {s.vehicle_id for s in shipments_map.values() if s.vehicle_id}
    drv_ids = {s.driver_id for s in shipments_map.values() if s.driver_id}

    customers_map = {c.id: c for c in db.query(Customer).filter(Customer.id.in_(cust_ids)).all()} if cust_ids else {}
    vehicles_map = {v.id: v for v in db.query(Vehicle).filter(Vehicle.id.in_(veh_ids)).all()} if veh_ids else {}
    drivers_map = {d.id: d for d in db.query(Driver).filter(Driver.id.in_(drv_ids)).all()} if drv_ids else {}
    costs_map = {c.shipment_id: c for c in db.query(TransportationCost).filter(TransportationCost.shipment_id.in_(shp_ids)).all()} if shp_ids else {}

    preloaded = {
        "locations": locations_map,
        "shipments": shipments_map,
        "customers": customers_map,
        "vehicles": vehicles_map,
        "drivers": drivers_map,
        "costs": costs_map
    }

    # Enrich all routes with preloaded lookups
    enriched_routes = [enrich_route(r, db, preloaded=preloaded) for r in routes]

    # Filter in-memory for joined fields (search, status, vehicle_id, driver_id)
    filtered = enriched_routes
    if status and status.lower() != "all":
        filtered = [r for r in filtered if r.status.lower() == status.strip().lower()]

    if vehicle_id:
        filtered = [r for r in filtered if r.vehicle_id == vehicle_id]

    if driver_id:
        filtered = [r for r in filtered if r.driver_id == driver_id]

    if search and search.strip():
        q = search.strip().lower()
        filtered = [
            r for r in filtered
            if q in r.route_code.lower()
            or (r.shipment_code and q in r.shipment_code.lower())
            or q in r.origin_city.lower()
            or q in r.destination_city.lower()
            or (r.vehicle_code and q in r.vehicle_code.lower())
            or (r.driver_name and q in r.driver_name.lower())
        ]

    return filtered


@router.get("/shipment/{shipment_code}")
def get_route_for_shipment(
    shipment_code: str, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    code_clean = shipment_code.strip().upper()
    
    # Check Driver scope if driver
    if current_user.role == "Driver":
        shp = db.query(Shipment).filter(Shipment.shipment_code == code_clean).first()
        if not shp or shp.driver_id != current_user.driver_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied. Drivers can only view routes for their assigned shipments.")
            
    res = route_optimization_tool.execute(shipment_code=code_clean)
    if not res.get("success"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=res.get("error"))
    return res


@router.get("/locations", response_model=List[dict])
def list_locations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    locs = db.query(DeliveryLocation).order_by(DeliveryLocation.city.asc()).all()
    return [
        {
            "id": l.id,
            "location_code": l.location_code,
            "name": l.name,
            "city": l.city,
            "state": l.state,
            "latitude": l.latitude,
            "longitude": l.longitude,
            "hub_type": l.hub_type
        } for l in locs
    ]


@router.get("/{route_code}", response_model=RouteResponse)
def get_route(
    route_code: str, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    code_clean = route_code.strip().upper()
    r = db.query(Route).filter(Route.route_code == code_clean).first()
    if not r:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Route '{route_code}' not found.")

    # Data scope: Driver cannot access other drivers' routes
    if current_user.role == "Driver":
        shipment = db.query(Shipment).filter(Shipment.id == r.shipment_id).first() if r.shipment_id else None
        if not shipment or shipment.driver_id != current_user.driver_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. Drivers can only access their assigned routes."
            )

    return enrich_route(r, db)


@router.post("", response_model=RouteResponse, status_code=status.HTTP_201_CREATED)
def create_route(
    route_in: RouteCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_role(["Admin", "Logistics Manager", "Dispatcher", "Fleet Manager", "Operations Team"]))
):
    orig = db.query(DeliveryLocation).filter(DeliveryLocation.id == route_in.origin_id).first()
    if not orig:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Origin location ID {route_in.origin_id} not found.")

    dest = db.query(DeliveryLocation).filter(DeliveryLocation.id == route_in.destination_id).first()
    if not dest:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Destination location ID {route_in.destination_id} not found.")

    if orig.id == dest.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Origin and destination must be distinct facilities.")

    shipment = None
    if route_in.shipment_id:
        shipment = db.query(Shipment).filter(Shipment.id == route_in.shipment_id).first()
        if not shipment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Shipment ID {route_in.shipment_id} not found.")

    vehicle = None
    if route_in.vehicle_id:
        vehicle = db.query(Vehicle).filter(Vehicle.id == route_in.vehicle_id).first()
        if not vehicle:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Vehicle ID {route_in.vehicle_id} not found.")
        if shipment and shipment.weight_kg > (vehicle.max_capacity_kg or 999999):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cargo weight {shipment.weight_kg:,.1f} kg exceeds vehicle {vehicle.vehicle_code} maximum capacity of {vehicle.max_capacity_kg:,.1f} kg."
            )

    driver = None
    if route_in.driver_id:
        driver = db.query(Driver).filter(Driver.id == route_in.driver_id).first()
        if not driver:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Driver ID {route_in.driver_id} not found.")

    # Calculate canonical distance & duration
    calc = maps_service.calculate_distance_and_duration(orig.latitude, orig.longitude, dest.latitude, dest.longitude)
    distance_km = calc.get("distance_km", 100.0)
    duration_min = calc.get("duration_minutes", 90)

    # Cost calculation
    v_type = vehicle.type if vehicle else "Semi-Truck (Dry Van)"
    cost_res = cost_optimizer.calculate_trip_cost(distance_km=distance_km, vehicle_type=v_type)
    est_cost = cost_res.get("total_cost", 0.0)

    # Generate waypoints & polyline
    wps, poly = generate_route_telemetry(orig, dest, distance_km)

    # Generate route code
    if route_in.route_code:
        r_code = route_in.route_code.strip().upper()
    elif shipment:
        r_code = f"RTE-{shipment.shipment_code}"
    else:
        r_code = f"RTE-R{random.randint(7000, 9999)}"

    existing = db.query(Route).filter(Route.route_code == r_code).first()
    if existing:
        r_code = f"RTE-R{random.randint(1000, 9999)}"

    new_route = Route(
        route_code=r_code,
        shipment_id=shipment.id if shipment else None,
        origin_id=orig.id,
        destination_id=dest.id,
        planned_distance_km=distance_km,
        actual_distance_km=None,
        planned_duration_min=duration_min,
        actual_duration_min=None,
        traffic_condition=route_in.traffic_condition or "Moderate",
        weather_condition=route_in.weather_condition or "Clear",
        waypoints_json=json.dumps(wps),
        polyline_json=json.dumps(poly),
        estimated_cost=est_cost,
        status="Assigned" if (shipment or vehicle or driver) else "Planned",
        created_at=datetime.utcnow()
    )

    db.add(new_route)
    db.commit()
    db.refresh(new_route)

    return enrich_route(new_route, db)


@router.put("/{route_code}", response_model=RouteResponse)
def update_route(
    route_code: str,
    update_data: RouteUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(require_role(["Admin", "Logistics Manager", "Dispatcher", "Fleet Manager", "Operations Team"]))
):
    code_clean = route_code.strip().upper()
    r = db.query(Route).filter(Route.route_code == code_clean).first()
    if not r:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Route '{route_code}' not found.")

    update_dict = update_data.dict(exclude_unset=True)

    # Handle Destination change (recomputes distance, duration, cost, and polyline)
    if "destination_id" in update_dict and update_dict["destination_id"] != r.destination_id:
        new_dest_id = update_dict["destination_id"]
        dest = db.query(DeliveryLocation).filter(DeliveryLocation.id == new_dest_id).first()
        if not dest:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Destination ID {new_dest_id} not found.")
        
        orig = db.query(DeliveryLocation).filter(DeliveryLocation.id == r.origin_id).first()
        if orig:
            calc = maps_service.calculate_distance_and_duration(orig.latitude, orig.longitude, dest.latitude, dest.longitude)
            r.planned_distance_km = calc.get("distance_km", r.planned_distance_km)
            r.planned_duration_min = calc.get("duration_minutes", r.planned_duration_min)
            wps, poly = generate_route_telemetry(orig, dest, r.planned_distance_km)
            r.waypoints_json = json.dumps(wps)
            r.polyline_json = json.dumps(poly)
            
            # Recalculate trip cost
            cost_res = cost_optimizer.calculate_trip_cost(r.planned_distance_km)
            r.estimated_cost = cost_res.get("total_cost", r.estimated_cost)

        r.destination_id = new_dest_id

    # Handle vehicle reassignment
    if "vehicle_id" in update_dict and r.shipment_id:
        v_id = update_dict["vehicle_id"]
        shp = db.query(Shipment).filter(Shipment.id == r.shipment_id).first()
        if shp:
            shp.vehicle_id = v_id
            if v_id:
                v = db.query(Vehicle).filter(Vehicle.id == v_id).first()
                if v and v.status == "Available":
                    v.status = "Assigned"

    # Handle driver reassignment
    if "driver_id" in update_dict and r.shipment_id:
        d_id = update_dict["driver_id"]
        shp = db.query(Shipment).filter(Shipment.id == r.shipment_id).first()
        if shp:
            shp.driver_id = d_id
            if d_id:
                d = db.query(Driver).filter(Driver.id == d_id).first()
                if d and d.status == "Available":
                    d.status = "Assigned"

    if "traffic_condition" in update_dict:
        r.traffic_condition = update_dict["traffic_condition"]
    if "weather_condition" in update_dict:
        r.weather_condition = update_dict["weather_condition"]
    if "actual_distance_km" in update_dict:
        r.actual_distance_km = update_dict["actual_distance_km"]
    if "actual_duration_min" in update_dict:
        r.actual_duration_min = update_dict["actual_duration_min"]
    if "status" in update_dict:
        new_st = update_dict["status"]
        r.status = new_st
        if r.shipment_id:
            shp = db.query(Shipment).filter(Shipment.id == r.shipment_id).first()
            if shp:
                if new_st == "In Transit":
                    shp.status = "In Transit"
                elif new_st == "Completed":
                    shp.status = "Delivered"
                elif new_st == "Delayed":
                    shp.status = "Delayed"

    db.commit()
    db.refresh(r)
    return enrich_route(r, db)


@router.delete("/{route_code}")
def deactivate_route(
    route_code: str,
    db: Session = Depends(get_db),
    current_user = Depends(require_role(["Admin", "Logistics Manager"]))
):
    code_clean = route_code.strip().upper()
    r = db.query(Route).filter(Route.route_code == code_clean).first()
    if not r:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Route '{route_code}' not found.")

    shipment = db.query(Shipment).filter(Shipment.id == r.shipment_id).first() if r.shipment_id else None
    if r.status in ["In Transit", "Delayed"] or (shipment and shipment.status in ["In Transit", "Picked Up", "Delayed"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel route '{code_clean}': route or associated shipment is currently active in transit. Please complete or reassign shipment first."
        )

    r.status = "Cancelled"
    db.commit()
    db.refresh(r)

    return {
        "success": True,
        "message": f"Route '{code_clean}' cancelled successfully.",
        "route": enrich_route(r, db)
    }


@router.post(
    "/calculate",
    dependencies=[Depends(rate_limit(max_requests=settings.RATE_LIMIT_ROUTE_OPTIMIZE, window_seconds=60, key_prefix="route_calc"))]
)
def calculate_route(
    req: RouteCalculateRequest,
    current_user: User = Depends(get_current_user)
):
    res = route_optimization_tool.execute(
        origin_id=req.origin_id,
        destination_id=req.destination_id,
        priority=req.priority
    )
    if not res.get("success"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=res.get("error"))
    return res


@router.post(
    "/optimize",
    dependencies=[Depends(rate_limit(max_requests=settings.RATE_LIMIT_ROUTE_OPTIMIZE, window_seconds=60, key_prefix="route_opt"))]
)
@router.post(
    "/{route_code}/optimize",
    dependencies=[Depends(rate_limit(max_requests=settings.RATE_LIMIT_ROUTE_OPTIMIZE, window_seconds=60, key_prefix="route_opt"))]
)
def optimize_route(
    req: RouteOptimizeRequest,
    route_code: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(require_role(["Admin", "Logistics Manager", "Dispatcher", "Fleet Manager", "Operations Team"]))
):
    target_code = route_code or req.route_code
    target_shipment = req.shipment_code

    r = None
    if target_code:
        r = db.query(Route).filter(Route.route_code == target_code.strip().upper()).first()
    elif target_shipment:
        shp = db.query(Shipment).filter(Shipment.shipment_code == target_shipment.strip().upper()).first()
        if shp:
            r = db.query(Route).filter(Route.shipment_id == shp.id).first()

    orig_id = r.origin_id if r else None
    dest_id = r.destination_id if r else None

    res = route_optimization_tool.execute(
        shipment_code=target_shipment,
        origin_id=orig_id,
        destination_id=dest_id,
        priority=req.priority,
        user_context={"role": current_user.role, "driver_id": current_user.driver_id, "email": current_user.email}
    )

    if not res.get("success"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=res.get("error"))

    # If apply_optimization is requested and route exists, persist optimized parameters
    if req.apply_optimization and r:
        rec = res.get("recommended_route", {})
        r.planned_distance_km = rec.get("distance_km", r.planned_distance_km)
        r.planned_duration_min = rec.get("duration_minutes", r.planned_duration_min)
        r.traffic_condition = rec.get("traffic_condition", r.traffic_condition)
        r.weather_condition = rec.get("weather_condition", r.weather_condition)
        r.estimated_cost = rec.get("estimated_cost_usd", r.estimated_cost)
        if "stops" in res:
            r.waypoints_json = json.dumps(res["stops"])
        if "polyline_coordinates" in res:
            r.polyline_json = json.dumps(res["polyline_coordinates"])

        db.commit()
        db.refresh(r)
        res["persisted_route"] = enrich_route(r, db)

    return res
