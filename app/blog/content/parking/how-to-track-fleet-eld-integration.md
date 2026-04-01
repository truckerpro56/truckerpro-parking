---
title: "How to Track Your Fleet in Real-Time with ELD Integration"
slug: how-to-track-fleet-eld-integration
category: tips
meta_description: "How to track your truck fleet in real-time using ELD integration. Samsara setup, HOS compliance, GPS visibility, driver alerts, and what real ELD-TMS integration looks like."
meta_keywords: "fleet ELD tracking, real-time fleet tracking Canada, Samsara integration TMS, HOS compliance ELD, GPS fleet visibility, ELD mandate Canada, fleet management ELD"
date: "2026-03-28"
author: "TruckerPro Team"
cta_primary:
  text: "Try TruckerPro TMS Free"
  url: "https://www.truckerpro.ca/signup"
cta_secondary:
  text: "Try TMS"
  url: "https://tms.truckerpro.ca"
related_slugs:
  - fleet-parking-management
  - how-to-choose-tms-for-small-carrier
---

## Why Real-Time Fleet Tracking Changes How You Operate

Before ELDs became the standard for Canadian federally-regulated carriers, fleet managers relied on a combination of driver phone calls, paper logs, and periodic check-ins to understand where their trucks were and whether their drivers were within Hours of Service limits. The result was a system where the dispatcher's knowledge was always 30–60 minutes behind reality, where HOS violations were discovered after the fact rather than prevented, and where cargo status updates to customers involved calling the driver and relaying what they said.

Electronic Logging Devices, combined with a TMS that genuinely integrates their data, change this fundamentally. Real-time fleet visibility means a dispatcher can see every truck's location, speed, and HOS status simultaneously, without making a single phone call. ELD integration means HOS violations can be prevented rather than recorded. GPS data means customer ETAs can be calculated from actual position rather than driver estimates.

This guide explains how ELD integration works in practice, what data you should expect to see in your TMS, and how to use that data to run a safer and more efficient fleet.

## How the ELD Mandate Applies in Canada

Transport Canada's ELD mandate applies to federally-regulated commercial carriers — operators subject to the federal Commercial Vehicle Drivers Hours of Service Regulations. The mandate requires drivers to record their hours of service using a certified ELD device rather than paper logs.

**Who is covered:**
- Operators of commercial motor vehicles in interprovincial and international service
- Carriers transporting goods across provincial or national borders
- Drivers operating vehicles with a gross vehicle weight over 4,500 kg

**Who is exempt:**
- Carriers operating entirely within a single province under provincial HOS regulations (though most provinces have adopted or are adopting the same mandate)
- Vehicles operated in a 160-km radius from the home terminal on day trip exemption
- Certain agricultural vehicles during harvest periods

The mandate has been in effect since June 2021, with progressive enforcement. As of 2026, full enforcement applies and paper log exemptions for technical difficulties have strict time limits.

**ELD certification:** In Canada, ELDs must be certified against Transport Canada's technical standard. Not all devices sold in Canada are certified. Before purchasing or switching ELD providers, confirm certification status on Transport Canada's approved device list.

## What Data Your ELD Transmits

A certified ELD continuously records and transmits several data categories. Understanding what data is available helps you evaluate whether your TMS is actually using it.

**Location data:** GPS coordinates at regular intervals, typically every 1–5 minutes while the vehicle is moving, and at each change in duty status. Location data includes speed, heading, and odometer.

**Engine data:** Engine hours, ignition on/off events, and in modern units, fault codes (DTCs). This data is valuable for maintenance planning and fuel monitoring.

**Hours of Service data:** The ELD records every duty status change — On Duty, Driving, Off Duty, Sleeper Berth — with the precise time and location of each change. This generates the driver's electronic log, which must be available for roadside inspection on demand.

**Driver identification:** The ELD records which driver is logged in at any given time, supporting accurate per-driver HOS tracking in multi-driver operations.

**Malfunctions and data diagnostics:** When the ELD detects a malfunction, it records and flags the event. Drivers are required to note the malfunction in their records and switch to paper logs within a defined time limit.

## What Real TMS Integration Looks Like

The phrase "ELD integration" is used loosely by some TMS vendors to describe everything from a real-time bidirectional data connection to simply displaying a link to the ELD provider's separate portal. Here is what genuine integration should include.

<!-- cta -->

**Real-time driver status on the dispatch board:**
The TMS dispatch board should show each driver's current duty status without requiring the dispatcher to open a separate ELD portal. On-Duty, Driving, Off Duty, or Sleeper Berth status should update in near-real-time. A dispatcher managing 15 trucks should be able to see all 15 statuses on a single screen.

**Remaining hours displayed per driver:**
Each driver's entry on the dispatch board should show their remaining driving time in the current shift, remaining driving time to the end of their cycle, and time until their next reset or 8/10-hour off-duty break is satisfied. These numbers should update automatically from ELD data — not require a manual entry.

**HOS-aware load assignment:**
When a dispatcher assigns a load to a driver, the TMS should calculate whether the driver has sufficient hours to legally complete the estimated drive time. If the system calculates that the driver will run out of hours 50 km short of the destination, it should alert the dispatcher before the load is confirmed — not after the driver is already in violation.

**Live GPS map:**
A fleet map showing vehicle positions should update in real-time or near-real-time. Positions should reflect actual GPS data from the ELD, not extrapolated positions based on the last known point. The map should show vehicle direction, speed, and load assignment.

**Automated ETA updates:**
When a dispatcher or customer portal asks "when will this load arrive?", the system should calculate ETA from the driver's current GPS position, current road speed, and remaining HOS availability. An ETA that ignores HOS constraints is unreliable — a driver who has 2 hours of driving time left cannot be 4 hours from destination regardless of what GPS says.

**Alert triggers:**
The TMS should support configurable alerts: driver has less than 1 hour of remaining drive time, driver has been stationary for more than X minutes during a delivery window, vehicle speed exceeds a set threshold, unauthorized after-hours movement.

## Samsara Integration: What It Enables

Samsara is one of the most widely used ELD platforms among Canadian carriers, with a robust open API that enables deep TMS integration. Here is what Samsara integration with a properly connected TMS enables in practice.

**Automatic load status updates:**
When a Samsara-equipped driver stops at a customer location and transitions to On Duty (Not Driving), the TMS can be configured to automatically update the load status to "Arrived at Delivery." When the driver departs, the status advances to "Departed Delivery." This eliminates the requirement for the driver to manually check in and out via the TMS app on every stop.

**Fault code monitoring:**
Samsara transmits engine fault codes (DTCs) in real-time. A TMS connected to this data can alert fleet maintenance when a fault code appears that requires same-day attention — a brake system fault, an EGR malfunction, or an emissions-related fault that could trigger a roadside pull-in — before the driver is anywhere near a maintenance shop or a CVSA inspection point.

**Fuel monitoring:**
Samsara's fuel monitoring module tracks fuel consumption per trip. When this data feeds into the TMS, the carrier gets actual fuel consumption per load rather than calculated estimates. Over time, this data identifies trucks with abnormal consumption patterns that indicate engine issues, fuel card fraud, or routing inefficiencies.

**Driver scoring:**
Samsara's safety scoring system generates per-driver metrics on harsh braking, harsh acceleration, speeding, and phone use. When these scores feed into the TMS, fleet managers can track driver safety trends over time and build driver coaching programs around data rather than anecdote.

## HOS Compliance: Prevention vs. Recording

The fundamental shift that ELD integration enables is moving HOS compliance from a recording exercise to a prevention exercise.

With paper logs, HOS violations were often discovered during a compliance audit, a roadside inspection, or a safety review — after they had occurred, after the regulatory record was already affected. Retroactive compliance is expensive and stressful.

With real-time ELD integration in a TMS, HOS violations are visible before they happen. A driver with 1 hour and 20 minutes of remaining drive time who has been assigned a load estimated at 3 hours represents a pending violation — which the TMS should flag for the dispatcher immediately, not after the driver has run out of hours on the highway.

The practical prevention protocol looks like this:
1. Dispatcher assigns a load. TMS checks estimated drive time against driver's remaining hours.
2. If drive time exceeds remaining hours, TMS alerts dispatcher before confirming the load.
3. Dispatcher either assigns a different driver, adjusts the schedule to accommodate a required break, or confirms a legal relay point where a second driver takes over.
4. The load moves without a violation.

This protocol works only if the TMS is genuinely integrating ELD data into its HOS calculations — not just displaying it as a reference.

## GPS Fleet Visibility: Beyond Just "Where Is My Truck"

GPS fleet visibility is often framed as a customer service tool — you can give customers accurate ETAs. That is true and valuable. But real-time GPS visibility has operational value beyond customer communication.

**Detention time documentation:**
When a driver arrives at a customer and GPS records their location, then records that they were stationary at that location for 3 hours beyond the scheduled appointment time, you have automatic detention time documentation. This eliminates the "driver didn't note it on the BOL" problem and gives your billing team the data needed to charge legitimate detention fees.

**Driver safety and incident response:**
When a vehicle is stationary in an unusual location at an unusual time, GPS visibility allows a dispatcher to call and check on the driver. A truck parked on a highway shoulder at 2 AM triggers a welfare check. Without GPS visibility, this situation might not be noticed until morning.

**Route compliance:**
GPS tracking verifies that drivers are following authorized routes, especially relevant for oversize loads with specified routing, HazMat shipments on restricted roads, or FAST-lane crossings with specific approach requirements.

**Theft detection:**
GPS alerts on unauthorized vehicle movement — outside driver hours, outside normal operating areas — are an early warning system for trailer theft or unauthorized equipment use.

## Setting Up Your Fleet for ELD Integration

Getting real-time tracking working correctly requires attention at the setup phase. These are the steps that most commonly go wrong.

**Step 1: Verify ELD certification.** Confirm your ELD devices are on Transport Canada's approved list before purchasing or relying on them for compliance. Uncertified devices expose your drivers to roadside violations.

**Step 2: Confirm TMS integration scope.** Before signing a TMS contract, get in writing exactly which ELD providers the system integrates with and what data flows bidirectionally. Ask for a demo of the specific features described above with your ELD provider's data.

**Step 3: Train dispatchers on HOS tools.** The TMS HOS tools are only useful if dispatchers know how to use them. A dispatcher who ignores the HOS alert on a load assignment has defeated the purpose of integration. Include HOS-aware dispatch in your dispatcher training and make it part of standard operating procedure.

**Step 4: Configure alerts.** Default alert thresholds are rarely optimal for every fleet. Adjust speed alert thresholds to match your company's policies, set remaining-hours alerts at the time interval that gives dispatchers enough lead time to adjust, and configure any route deviation or geofence alerts relevant to your operation.

**Step 5: Review data weekly.** The value of ELD data accumulates over time. Weekly review of driver HOS patterns, speeding events, and fuel consumption creates the baseline that makes individual anomalies visible. A driver who suddenly starts using 15% more fuel than their own baseline three weeks ago is signaling something worth investigating.

Real-time fleet tracking through ELD integration is not a luxury for large fleets — it is a compliance and operational management tool that pays for itself in violation prevention, fuel monitoring, and detention documentation for any fleet running federally-regulated operations.
