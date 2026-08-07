from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from app.config import APP_TIMEZONE
from app.database import SessionLocal
from app.models import AssetModel, WorkOrderModel
from app.schemas import WorkOrderPriority, WorkOrderStatus


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

        work_orders = [
            WorkOrderModel(
                asset_id=assets[0].id,
                title="Investigate high discharge temperature",
                description="Compressor temperature exceeded its normal range.",
                priority=WorkOrderPriority.HIGH,
                status=WorkOrderStatus.OPEN,
                due_date=datetime.now(UTC) - timedelta(days=2),
                failure_code="HIGH-TEMP",
            ),
            WorkOrderModel(
                asset_id=assets[0].id,
                title="Inspect compressor cooling system",
                description="Repeat high-temperature alarm reported.",
                priority=WorkOrderPriority.HIGH,
                status=WorkOrderStatus.OPEN,
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
                due_date=datetime.now(UTC) + timedelta(days=1),
                failure_code="SEAL-LEAK",
            ),
            WorkOrderModel(
                asset_id=assets[2].id,
                title="Perform generator battery inspection",
                description="Check battery voltage and terminal condition.",
                priority=WorkOrderPriority.LOW,
                status=WorkOrderStatus.OPEN,
                due_date=datetime.now(UTC) + timedelta(days=7),
                failure_code=None,
            ),
        ]

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