# SOP-LOG-04: Driver Hours of Service (HOS) and Rest Regulations

## 1. Regulatory Overview
All LogiAgent driver schedules and dispatch route optimizations must strictly comply with the Federal Motor Carrier Safety Administration (FMCSA) and Department of Transportation (DOT) Hours of Service (HOS) rules.

## 2. Core Driving Limits (Property-Carrying Commercial Vehicles)
- **11-Hour Driving Limit**: A driver may drive a maximum of 11 hours after 10 consecutive hours off duty.
- **14-Hour On-Duty Window**: Driving cannot occur beyond the 14th consecutive hour after coming on duty, following 10 consecutive hours off duty.
- **30-Minute Rest Break**: Driving is prohibited if more than 8 consecutive hours have passed since the end of the driver's last off-duty or sleeper-berth period of at least 30 minutes.
- **60/70-Hour Duty Limits**: Driver may not drive after 60 hours on duty in 7 consecutive days, or 70 hours in 8 consecutive days (34-hour restart required to reset).

## 3. Automated Dispatch Restrictions in LogiAgent
- LogiAgent Route Optimization Tool automatically prohibits assigning routes whose estimated duration exceeds the driver's current `hours_of_service_remaining` minus a 45-minute safety buffer.
- If an in-transit shipment experiences traffic delays that will breach the 11-hour limit, the Delay Detection Tool flags risk status `HOS_BREACH_RISK` and prompts Dispatch to assign a team driver or schedule a mandatory rest waypoint.
