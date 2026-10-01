import os
import pymupdf

def create_pdf(filepath: str, title: str, pages_content: list):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    doc = pymupdf.open()
    
    for page_idx, content in enumerate(pages_content):
        page = doc.new_page(width=595, height=842) # A4
        # Margin
        margin_x = 50
        margin_y = 60
        
        # Header banner
        page.draw_rect(pymupdf.Rect(margin_x, margin_y, 545, margin_y + 35), color=(0.1, 0.25, 0.45), fill=(0.92, 0.95, 0.98))
        page.insert_text(pymupdf.Point(margin_x + 10, margin_y + 22), f"LOGIAGENT OPERATIONAL POLICY DOCUMENT — PAGE {page_idx + 1}", fontsize=9, color=(0.1, 0.3, 0.6))
        
        # Title
        page.insert_text(pymupdf.Point(margin_x, margin_y + 60), title, fontsize=14, color=(0.08, 0.15, 0.3))
        
        # Body content
        y_pos = margin_y + 85
        lines = content.strip().split("\n")
        for line in lines:
            if y_pos > 780:
                break
            if line.startswith("## "):
                y_pos += 12
                page.insert_text(pymupdf.Point(margin_x, y_pos), line.replace("## ", ""), fontsize=11, color=(0.15, 0.25, 0.4))
                y_pos += 16
            elif line.startswith("### "):
                y_pos += 8
                page.insert_text(pymupdf.Point(margin_x, y_pos), line.replace("### ", ""), fontsize=10, color=(0.2, 0.3, 0.45))
                y_pos += 14
            elif line.startswith("- "):
                page.insert_text(pymupdf.Point(margin_x + 10, y_pos), "• " + line[2:], fontsize=9, color=(0.1, 0.1, 0.1))
                y_pos += 13
            elif line.startswith("1.") or line.startswith("2.") or line.startswith("3.") or line.startswith("4.") or line.startswith("5."):
                page.insert_text(pymupdf.Point(margin_x + 10, y_pos), line, fontsize=9, color=(0.1, 0.1, 0.1))
                y_pos += 13
            else:
                if line.strip():
                    page.insert_text(pymupdf.Point(margin_x, y_pos), line, fontsize=9, color=(0.15, 0.15, 0.15))
                    y_pos += 13
                else:
                    y_pos += 6

        # Footer
        page.insert_text(pymupdf.Point(margin_x, 810), f"LogiAgent Enterprise Supply Chain • Confidential • Page {page_idx + 1} of {len(pages_content)}", fontsize=8, color=(0.5, 0.5, 0.5))

    doc.save(filepath)
    doc.close()
    print(f"Created PDF: {filepath} ({len(pages_content)} pages)")


def generate_all_sample_pdfs():
    docs_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "documents"))
    os.makedirs(docs_dir, exist_ok=True)

    # 1. Failed Delivery Policy (SOP-LOG-02)
    failed_delivery_p1 = """# SOP-LOG-02: Failed Delivery & Customer Unavailability Policy

## 1. Purpose and Scope
This standard operating procedure defines mandatory operational steps when a delivery recipient is unavailable or unreachable at the designated delivery location.

## 2. On-Site Protocol for Unavailable Customer
When a driver arrives at the customer delivery destination and the customer or authorized receiver is unavailable:
1. Mandatory Waiting Window: The driver must wait at the loading dock or premises for a minimum of 15 minutes before initiating an exception.
2. Direct Contact Attempt: The driver must attempt telephone contact with the customer contact person at least twice, spaced 5 minutes apart.
3. Dispatch Escalation: If the customer remains unreachable after 15 minutes, the driver must notify Central Dispatch via the LogiAgent mobile terminal.
4. Photographic & GPS Verification: The driver must record photographic proof of the delivery location and obtain a timestamped GPS lock in the mobile app.

## 3. Delivery Exception Notice (DEN-02)
- Central Dispatch immediately transmits an electronic Delivery Exception Notice (DEN-02) to the customer via SMS and email.
- The customer is provided a 30-minute grace window to respond with alternative receiver authorization or rescheduled instructions."""

    failed_delivery_p2 = """## 4. Re-Delivery and Return Procedures
### Re-Delivery Attempts
- Maximum Allowed Attempts: The carrier will make up to three (3) delivery attempts within five (5) business days.
- Re-delivery Fee: A standard re-delivery surcharge of $65.00 applies to each subsequent attempt after the initial failure.

### Cold Chain & Perishable Exceptions
- Perishable or refrigerated cargo (2°C to 8°C) cannot remain in an unconfirmed transit state exceeding 2 hours.
- If receiver is unavailable, dispatch must reroute perishable shipments to the nearest temperature-controlled regional hub immediately.

### Return to Terminal (RTT) Protocol
- If all 3 delivery attempts fail or if the customer formally refuses delivery, the driver must return non-delivered freight to the origin distribution center.
- The driver and receiving warehouse supervisor must execute a signed Return Exception Manifest.
- Storage and Demurrage: Storage fees of $45.00 per pallet/day begin accruing automatically after 48 hours of holding at the regional hub."""

    create_pdf(
        os.path.join(docs_dir, "failed_delivery_policy.pdf"),
        "SOP-LOG-02: Failed Delivery & Customer Unavailability Standard Operating Procedure",
        [failed_delivery_p1, failed_delivery_p2]
    )

    # 2. Delivery Procedure (SOP-LOG-01)
    delivery_proc_p1 = """# SOP-LOG-01: Standard Logistics Delivery & Proof of Delivery Procedure

## 1. Overview
This procedure establishes standard operating protocols for routine commercial and industrial freight deliveries.

## 2. Arrival & Dock Check-In
1. Gate Check-In: Driver presents Commercial Driver License (CDL), Bill of Lading (BOL), and shipment code (e.g. SHP-1001).
2. Dock Assignment: Driver maneuvers vehicle into designated bay, engages parking brake, chocks wheels, and turns off engine.
3. Container Seal Inspection: Verify that the high-security bolt seal matches the BOL serial number before cutting the seal.

## 3. Electronic Proof of Delivery (e-POD)
- All deliveries require electronic Proof of Delivery (e-POD) captured via the LogiAgent mobile terminal.
- Required e-POD fields:
  - Legible recipient signature and printed full name.
  - Recipient employee badge / ID number.
  - High-resolution photograph of delivered pallets at receiving dock.
  - Automated GPS geotag and UTC delivery timestamp."""

    delivery_proc_p2 = """## 4. Damaged Cargo & Shortage Exceptions
### Visible Damage Protocol
- If exterior carton or pallet damage is observed during unloading:
  1. Halt unloading immediately and notify the receiver facility supervisor.
  2. Take minimum 4 high-resolution photos showing package damage, orientation arrows, and pallet tags.
  3. Mark specific damaged quantity on BOL with status 'Damaged on Arrival'.
  4. Obtain countersignature from dock manager before departing.

### Shortages and Overage
- Any piece count discrepancy must be recorded on the digital manifest immediately.
- Driver must not depart dock until Central Dispatch logs the discrepancy exception code."""

    create_pdf(
        os.path.join(docs_dir, "delivery_procedure.pdf"),
        "SOP-LOG-01: Standard Logistics Delivery & Proof of Delivery Procedure",
        [delivery_proc_p1, delivery_proc_p2]
    )

    # 3. Vehicle Policy (SOP-VEH-05)
    vehicle_policy_p1 = """# SOP-VEH-05: Fleet Vehicle Loading, Weight Limits & Maintenance Policy

## 1. Vehicle Loading Requirements & Weight Distribution
Proper vehicle loading is critical to highway safety, vehicle stability, and regulatory compliance.

### Axle Weight Balance
- Cargo weight must be distributed evenly across all vehicle axles:
  - Maintain an 80/20 axle balance between drive axles and trailer tandem axles.
  - Never concentrate heavy freight at the rear bumper (tail-heavy loads cause fatal sway).
  - Heavy pallets must be placed over trailer axles and centered along the longitudinal centerline.

### Maximum Gross Vehicle Weight Rating (GVWR)
- Class 8 Heavy Tractor-Trailers: Maximum 80,000 lbs (36,287 kg) gross vehicle weight.
- Class 7 Medium Heavy Straight Trucks: Maximum 33,000 lbs (14,968 kg) gross vehicle weight.
- Class 6 Box Trucks: Maximum 26,000 lbs (11,793 kg) gross vehicle weight.
- Overweight loads are strictly prohibited from dispatch without special heavy-haul permits."""

    vehicle_policy_p2 = """## 2. Cargo Securing & Restraint Standards
- Ratchet Strapping: Minimum of two (2) heavy-duty 4-inch ratchet straps for every 10 linear feet of cargo bed.
- Double-Stacked Pallets: Must utilize anti-slip rubber friction mats and rigid corner edge protectors.
- Load Bars & Shoring Beams: Mandatory installation of spring-loaded shoring beams behind the final row of cargo.
- Hazardous Materials (HAZMAT) Separation: Toxic, corrosive, and flammable materials must maintain mandatory 3-foot separation barriers.

## 3. Mandatory Daily Pre-Trip Walkaround Inspection
Drivers must perform and log a 15-minute pre-trip vehicle inspection before starting any route:
1. Steer Tire Tread: Minimum tread depth of 4/32 inch; drive and trailer tires minimum 2/32 inch.
2. Air Brake Pressure: Minimum air pressure 100 PSI; verify low-pressure audible warning alarms.
3. Lighting & Reflectors: Clean and verify headlights, high beams, brake lights, and turn signals.
4. Reefer Telemetry: For refrigerated units, verify fuel level > 75% and temperature setpoint."""

    create_pdf(
        os.path.join(docs_dir, "vehicle_policy.pdf"),
        "SOP-VEH-05: Fleet Vehicle Loading, Weight Limits & Maintenance Policy",
        [vehicle_policy_p1, vehicle_policy_p2]
    )

    # 4. Driver Safety Guidelines (SOP-SAF-08)
    driver_safety_p1 = """# SOP-SAF-08: Driver Safety, Hours of Service (HOS) & Emergency Procedures

## 1. Driver Safety Procedure & Hours of Service (HOS) Regulations
LogiAgent enforces strict adherence to federal Hours of Service (HOS) regulations to eliminate driver fatigue.

### Maximum Driving Duty Limits
- 11-Hour Rule: A driver may drive a maximum of 11 cumulative hours after 10 consecutive hours off duty.
- 14-Hour Duty Window: All driving duty must be completed within a 14-consecutive-hour window from shift start.
- Mandatory 30-Minute Rest Break: Drivers must take an uninterrupted 30-minute rest break after 8 cumulative hours of driving time.
- 60/70-Hour Weekly Limit: Drivers must not exceed 60 hours on duty in 7 consecutive days or 70 hours in 8 days.

### Personal Protective Equipment (PPE)
All drivers must wear mandatory PPE when operating on loading docks, freight terminals, and customer facilities:
- Steel-toed safety boots with slip-resistant soles (ANSI Z41 compliant).
- High-visibility Class 3 safety vest or jacket with reflective striping.
- Hard hat and protective safety glasses in active forklift zones."""

    driver_safety_p2 = """## 2. Emergency Breakdown & Incident Procedures
When a mechanical breakdown, flat tire, or highway emergency occurs:
1. Hazard Lights: Immediately activate 4-way emergency hazard flashers and pull safely to the outer shoulder.
2. Emergency Warning Triangles: Deploy three (3) reflective emergency warning triangles within 10 minutes:
   - Triangle 1: Place 10 feet (3 meters) directly behind the vehicle on the traffic side.
   - Triangle 2: Place 100 feet (30 meters) behind the vehicle along the shoulder center.
   - Triangle 3: Place 200 feet (60 meters) behind the vehicle to give oncoming traffic advance warning.
3. Dispatch Emergency Notification: Contact Central Safety Hotline via LogiAgent App SOS button.

## 3. Severe Weather & Speed Guidelines
- Heavy Rain / Fog: Reduce highway speed by 25% and increase following distance to 6 seconds.
- Snow / Icy Road Conditions: Reduce highway speed by 50% or seek safe designated truck parking until highway clearance."""

    create_pdf(
        os.path.join(docs_dir, "driver_safety_guidelines.pdf"),
        "SOP-SAF-08: Driver Safety, Hours of Service (HOS) & Emergency Procedures",
        [driver_safety_p1, driver_safety_p2]
    )

if __name__ == "__main__":
    generate_all_sample_pdfs()
