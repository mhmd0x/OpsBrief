# OpsBrief Case Study

## Overview

OpsBrief is a maintenance decision-support application that transforms asset and work-order data into a focused daily operational brief.

The project was designed to demonstrate how maintenance data can be converted into actionable priorities rather than presented only as raw records.

## The Problem

Maintenance supervisors often work with information spread across CMMS records, spreadsheets, emails, messages, and shift handovers.

This fragmentation makes it harder to answer important daily questions:

- Which work orders are overdue?
- What is due today or within the next seven days?
- Is the monthly preventive-maintenance plan on schedule?
- How many PMs must be completed each day to recover a plan gap?
- Which items require immediate attention?
- Which assets are experiencing recurring failures?
- What should the maintenance team prioritize first?

## Project Goals

OpsBrief was built to:

- Provide structured asset and work-order management
- Identify schedule and priority risks automatically
- Detect recurring equipment failures
- Generate a concise Daily Operations Brief
- Present operational signals through a responsive dashboard
- Protect data-changing operations with API-key authentication
- Demonstrate production-oriented development practices

## Solution

OpsBrief provides a FastAPI backend, PostgreSQL persistence, and a responsive dashboard.

The application converts work-order records into operational signals:

- Overdue work orders
- Work orders due today
- Work orders due within seven days
- High-attention work orders
- Recurring failures by asset and failure code
- Monthly preventive-maintenance compliance
- Year-to-date preventive-maintenance compliance trends
- Work-order backlog aging analysis
- Asset reliability ranking based on active, overdue, high-priority, and recurring work-order signals
- Required calendar-day completion pace to reach the monthly target

Supervisors can open the planned, completed, remaining, and overdue PM totals to inspect the exact work orders behind each KPI.

![OpsBrief monthly PM work-order drill-down](images/opsbrief-pm-work-orders.png)

![OpsBrief work-order detail dialog](images/opsbrief-work-order-details.png)

![OpsBrief recurring-issue reliability dialog](images/opsbrief-recurring-issue-details.png)

These signals are presented together in the OpsBrief dashboard, helping supervisors quickly identify what requires attention and inspect the work orders behind each KPI.

## Architecture

The project uses a layered structure:

```text
Dashboard
    ↓
FastAPI routes
    ↓
Operational signal logic
    ↓
SQLAlchemy
    ↓
PostgreSQL
```

## Testing and Quality

OpsBrief includes 42 automated tests covering:

- Health checks
- Asset creation, retrieval, updating, and deletion
- Duplicate asset-tag handling
- Work-order creation, retrieval, filtering, updating, and deletion
- Work-order status-transition rules
- Overdue, due-today, due-soon, and high-attention signals
- Recurring failure detection
- Daily Operations Brief generation
- API-key authorization
- Dashboard and static-file delivery
- Monthly PM compliance, plan-status, and recovery-pace calculations
- Year-to-date PM compliance calculations
- Work-order backlog aging calculations
- Asset reliability ranking and risk-score calculations

Tests use an isolated in-memory SQLite database, preventing test data from modifying the PostgreSQL development database.

GitHub Actions runs the complete test suite automatically whenever changes are pushed.

## Containerized Development

Docker Compose runs the FastAPI application and PostgreSQL together. Health checks confirm that both services are ready.

A new developer can start the complete stack with:

```bash
cp .env.example .env
docker compose up --build -d
```