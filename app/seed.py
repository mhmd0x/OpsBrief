from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from app.config import APP_TIMEZONE
from app.database import SessionLocal
from app.models import AssetModel, WorkOrderModel
from app.schemas import (
    MaintenanceType,
    WorkOrderPriority,
    WorkOrderStatus,
)


def seed_demo_data() -> None:
    database = SessionLocal()

    try:
        existing_work_order = database.scalar(
            select(WorkOrderModel.id).limit(1)
        )

        if existing_work_order is not None:
            print("Demo data was not added because work orders already exist.")
            return

        assets = [
            AssetModel(
                name="Main Air Compressor",
                asset_tag="COMP-001",
                location="Utilities Area",
            ),
            AssetModel(
                name="Cooling Water Pump",
                asset_tag="PUMP-101",
                location="Cooling Station",
            ),
            AssetModel(
                name="Emergency Generator",
                asset_tag="GEN-201",
                location="Power House",
            ),
        ]

        database.add_all(assets)
        database.flush()

        local_now = datetime.now(APP_TIMEZONE)

        due_today = local_now.replace(
            hour=12,
            minute=0,
            second=0,
            microsecond=0,
        ).astimezone(UTC)

        month_start = local_now.replace(
            day=1,
            hour=12,
            minute=0,
            second=0,
            microsecond=0,
        )

        def pm_due_date(
            day: int,
            month: int | None = None,
        ) -> datetime:
            return month_start.replace(
                month=month or month_start.month,
                day=day,
            ).astimezone(UTC)

        work_orders = [
            WorkOrderModel(
                asset_id=assets[0].id,
                title="Investigate high discharge temperature",
                description="Compressor temperature exceeded its normal range.",
                priority=WorkOrderPriority.HIGH,
                status=WorkOrderStatus.OPEN,
                created_at=datetime.now(UTC) - timedelta(days=75),
                due_date=datetime.now(UTC) - timedelta(days=2),
                failure_code="HIGH-TEMP",
            ),
            WorkOrderModel(
                asset_id=assets[0].id,
                title="Inspect compressor cooling system",
                description="Repeat high-temperature alarm reported.",
                priority=WorkOrderPriority.HIGH,
                status=WorkOrderStatus.OPEN,
                created_at=datetime.now(UTC) - timedelta(days=45),
                due_date=due_today,
                failure_code="HIGH-TEMP",
            ),
            WorkOrderModel(
                asset_id=assets[0].id,
                title="Review previous compressor temperature trip",
                description="Document an earlier high-temperature shutdown.",
                priority=WorkOrderPriority.MEDIUM,
                status=WorkOrderStatus.COMPLETED,
                due_date=datetime.now(UTC) - timedelta(days=10),
                failure_code="HIGH-TEMP",
            ),
            WorkOrderModel(
                asset_id=assets[1].id,
                title="Replace pump mechanical seal",
                description="Minor leakage detected around the pump seal.",
                priority=WorkOrderPriority.MEDIUM,
                status=WorkOrderStatus.IN_PROGRESS,
                created_at=datetime.now(UTC) - timedelta(days=18),
                due_date=datetime.now(UTC) + timedelta(days=1),
                failure_code="SEAL-LEAK",
            ),
            WorkOrderModel(
                asset_id=assets[2].id,
                title="Perform generator battery inspection",
                description="Check battery voltage and terminal condition.",
                priority=WorkOrderPriority.LOW,
                maintenance_type=MaintenanceType.PREVENTIVE,
                status=WorkOrderStatus.OPEN,
                created_at=datetime.now(UTC) - timedelta(days=4),
                due_date=pm_due_date(26),
                failure_code=None,
            ),
            WorkOrderModel(
                asset_id=assets[0].id,
                title="Inspect compressor air filter",
                description="Complete the scheduled monthly filter inspection.",
                priority=WorkOrderPriority.MEDIUM,
                maintenance_type=MaintenanceType.PREVENTIVE,
                status=WorkOrderStatus.COMPLETED,
                completed_at=datetime.now(UTC),
                due_date=pm_due_date(3),
                failure_code=None,
            ),
            WorkOrderModel(
                asset_id=assets[1].id,
                title="Lubricate pump bearings",
                description="Complete scheduled bearing lubrication.",
                priority=WorkOrderPriority.MEDIUM,
                maintenance_type=MaintenanceType.PREVENTIVE,
                status=WorkOrderStatus.COMPLETED,
                completed_at=datetime.now(UTC),
                due_date=pm_due_date(6),
                failure_code=None,
            ),
            WorkOrderModel(
                asset_id=assets[2].id,
                title="Test generator battery capacity",
                description="Perform the scheduled monthly capacity test.",
                priority=WorkOrderPriority.HIGH,
                maintenance_type=MaintenanceType.PREVENTIVE,
                status=WorkOrderStatus.OPEN,
                due_date=pm_due_date(9),
                failure_code=None,
            ),
            WorkOrderModel(
                asset_id=assets[0].id,
                title="Replace compressor intake filter",
                description="Replace the scheduled intake-filter element.",
                priority=WorkOrderPriority.MEDIUM,
                maintenance_type=MaintenanceType.PREVENTIVE,
                status=WorkOrderStatus.OPEN,
                due_date=pm_due_date(14),
                failure_code=None,
            ),
            WorkOrderModel(
                asset_id=assets[1].id,
                title="Check pump and motor alignment",
                description="Complete the scheduled alignment inspection.",
                priority=WorkOrderPriority.MEDIUM,
                maintenance_type=MaintenanceType.PREVENTIVE,
                status=WorkOrderStatus.IN_PROGRESS,
                due_date=pm_due_date(20),
                failure_code=None,
            ),
        ]

        for month_number in range(1, local_now.month):
            completed_target = (
                1 if month_number % 3 == 0 else 2
            )

            for sequence in range(1, 3):
                due_date = pm_due_date(
                    day=10 + sequence * 5,
                    month=month_number,
                )
                is_completed = (
                    sequence <= completed_target
                )
                asset = assets[
                    (month_number + sequence)
                    % len(assets)
                ]
                month_name = due_date.astimezone(
                    APP_TIMEZONE
                ).strftime("%B")

                work_orders.append(
                    WorkOrderModel(
                        asset_id=asset.id,
                        title=(
                            f"{month_name} scheduled PM "
                            f"{sequence}"
                        ),
                        description=(
                            "Historical preventive-maintenance "
                            "plan record."
                        ),
                        priority=WorkOrderPriority.MEDIUM,
                        maintenance_type=(
                            MaintenanceType.PREVENTIVE
                        ),
                        status=(
                            WorkOrderStatus.COMPLETED
                            if is_completed
                            else WorkOrderStatus.OPEN
                        ),
                        completed_at=(
                            due_date + timedelta(hours=4)
                            if is_completed
                            else None
                        ),
                        due_date=due_date,
                        failure_code=None,
                    )
                )

        database.add_all(work_orders)
        database.commit()

        print("Demo data added successfully.")
        print(f"Assets created: {len(assets)}")
        print(f"Work orders created: {len(work_orders)}")

    except Exception:
        database.rollback()
        raise
    finally:
        database.close()


if __name__ == "__main__":
    seed_demo_data()