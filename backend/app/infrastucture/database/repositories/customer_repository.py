from typing import Optional, List
from app.domain.entities.customers import Customer, CustomerStatus, CustomerType
from app.domain.repositories.customer_repository import CustomerRepository as CustomerRepositoryInterface
from app.infrastucture.database.models.customers import Customer as CustomerORM
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from datetime import datetime
from sqlalchemy import func

class CustomerRepository(CustomerRepositoryInterface):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, customer_id: str) -> Optional[Customer]:
        result = await self._session.execute(select(CustomerORM).where(CustomerORM.id == UUID(customer_id), CustomerORM.deleted_at == None))
        obj = result.scalar_one_or_none()
        return self._to_entity(obj) if obj else None

    async def get_by_email(self, email: str) -> Optional[Customer]:
        result = await self._session.execute(select(CustomerORM).where(CustomerORM.email == email, CustomerORM.deleted_at == None))
        obj = result.scalar_one_or_none()
        return self._to_entity(obj) if obj else None

    async def get_by_tax_id(self, tax_pin: str) -> Optional[Customer]:
        result = await self._session.execute(select(CustomerORM).where(CustomerORM.tax_pin == tax_pin, CustomerORM.deleted_at == None))
        obj = result.scalar_one_or_none()
        return self._to_entity(obj) if obj else None

    async def get_all(self, limit: int = 100, offset: int = 0) -> List[Customer]:
        result = await self._session.execute(select(CustomerORM).where(CustomerORM.deleted_at == None).offset(offset).limit(limit))
        objs = result.scalars().all()
        return [self._to_entity(obj) for obj in objs]

    async def get_active_customers(self) -> List[Customer]:
        result = await self._session.execute(select(CustomerORM).where(CustomerORM.status == CustomerStatus.ACTIVE.value, CustomerORM.deleted_at == None))
        objs = result.scalars().all()
        return [self._to_entity(obj) for obj in objs]

    async def get_by_status(self, status: CustomerStatus) -> List[Customer]:
        result = await self._session.execute(select(CustomerORM).where(CustomerORM.status == status.value, CustomerORM.deleted_at == None))
        objs = result.scalars().all()
        return [self._to_entity(obj) for obj in objs]

    async def get_with_filters(
        self, 
        tenant_id: Optional[UUID] = None,
        limit: int = 100, 
        offset: int = 0,
        status: Optional[str] = None,
        customer_type: Optional[str] = None,
        search: Optional[str] = None
    ) -> tuple[List[Customer], int]:
        """Get customers with optional filters and tenant-aware filtering"""
        query = select(CustomerORM).where(CustomerORM.deleted_at == None)
        
        # Apply tenant filter
        if tenant_id:
            query = query.where(CustomerORM.tenant_id == tenant_id)
        
        # Apply status filter
        if status:
            query = query.where(CustomerORM.status == status)
        
        # Apply customer_type filter
        if customer_type:
            query = query.where(CustomerORM.customer_type == customer_type)
        
        # Apply search filter (searches in name, email, phone_number)
        if search:
            search_pattern = f"%{search}%"
            query = query.where(
                (CustomerORM.name.ilike(search_pattern)) |
                (CustomerORM.email.ilike(search_pattern)) |
                (CustomerORM.phone_number.ilike(search_pattern))
            )
        
        # Get total count before pagination
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self._session.execute(count_query)
        total = total_result.scalar() or 0
        
        # Apply pagination
        query = query.offset(offset).limit(limit)
        
        # Execute query
        result = await self._session.execute(query)
        objs = result.scalars().all()
        
        return [self._to_entity(obj) for obj in objs], total

    async def create_customer(self, customer: Customer) -> Customer:
        obj = CustomerORM(
            id=customer.id,
            tenant_id=customer.tenant_id,
            customer_type=customer.customer_type.value,
            status=customer.status.value,
            name=customer.name,
            email=customer.email,
            phone_number=customer.phone_number,
            tax_pin=customer.tax_pin,
            incorporation_doc=customer.incorporation_doc,
            credit_days=customer.credit_days,
            credit_limit=customer.credit_limit,
            owner_sales_rep_id=customer.owner_sales_rep_id,
            created_at=customer.created_at,
            created_by=customer.created_by,
            updated_at=customer.updated_at,
            updated_by=customer.updated_by,
            deleted_at=customer.deleted_at,
            deleted_by=customer.deleted_by
        )
        self._session.add(obj)
        await self._session.commit()
        await self._session.refresh(obj)
        return self._to_entity(obj)

    async def update_customer(self, customer_id: str, customer: Customer) -> Optional[Customer]:
        result = await self._session.execute(
            select(CustomerORM).where(
                CustomerORM.id == UUID(customer_id), 
                CustomerORM.deleted_at == None
            )
        )
        obj = result.scalar_one_or_none()
        if not obj:
            return None
        
        # Update fields, handling enums properly
        obj.tenant_id = customer.tenant_id
        obj.customer_type = customer.customer_type.value
        obj.status = customer.status.value
        obj.name = customer.name
        obj.email = customer.email
        obj.phone_number = customer.phone_number
        obj.tax_pin = customer.tax_pin
        obj.incorporation_doc = customer.incorporation_doc
        obj.credit_days = customer.credit_days
        obj.credit_limit = customer.credit_limit
        # Handle owner_sales_rep_id UUID properly
        if customer.owner_sales_rep_id is not None:
            if isinstance(customer.owner_sales_rep_id, str):
                obj.owner_sales_rep_id = UUID(customer.owner_sales_rep_id)
            else:
                obj.owner_sales_rep_id = customer.owner_sales_rep_id
        # Set updated_at to current time if not provided
        if customer.updated_at is not None:
            obj.updated_at = customer.updated_at
        else:
            from datetime import datetime
            obj.updated_at = datetime.now()
        # Handle updated_by UUID properly
        if customer.updated_by is not None:
            if isinstance(customer.updated_by, str):
                obj.updated_by = UUID(customer.updated_by)
            else:
                obj.updated_by = customer.updated_by    
        obj.deleted_at = customer.deleted_at
        # Handle deleted_by UUID properly
        if customer.deleted_by is not None:
            if isinstance(customer.deleted_by, str):
                obj.deleted_by = UUID(customer.deleted_by)
            else:
                obj.deleted_by = customer.deleted_by
        
        await self._session.commit()
        await self._session.refresh(obj)
        return self._to_entity(obj)

    async def delete_customer(self, customer_id: str, deleted_by: Optional[UUID] = None) -> bool:
        result = await self._session.execute(select(CustomerORM).where(CustomerORM.id == UUID(customer_id), CustomerORM.deleted_at == None))
        obj = result.scalar_one_or_none()
        if not obj:
            return False
        obj.deleted_at = datetime.now()
        obj.deleted_by = deleted_by
        await self._session.commit()
        return True

    async def activate_customer(self, customer_id: str) -> Optional[Customer]:
        result = await self._session.execute(select(CustomerORM).where(CustomerORM.id == UUID(customer_id), CustomerORM.deleted_at == None))
        obj = result.scalar_one_or_none()
        if not obj:
            return None
        obj.status = CustomerStatus.ACTIVE.value
        obj.updated_at = datetime.now()
        await self._session.commit()
        await self._session.refresh(obj)
        return self._to_entity(obj)

    async def deactivate_customer(self, customer_id: str) -> Optional[Customer]:
        result = await self._session.execute(select(CustomerORM).where(CustomerORM.id == UUID(customer_id), CustomerORM.deleted_at == None))
        obj = result.scalar_one_or_none()
        if not obj:
            return None
        obj.status = CustomerStatus.INACTIVE.value
        obj.updated_at = datetime.now()
        await self._session.commit()
        await self._session.refresh(obj)
        return self._to_entity(obj)

    async def approve_customer(self, customer_id: str, approved_by: UUID) -> Optional[Customer]:
        result = await self._session.execute(select(CustomerORM).where(CustomerORM.id == UUID(customer_id), CustomerORM.deleted_at == None))
        obj = result.scalar_one_or_none()
        if not obj:
            return None
        obj.status = CustomerStatus.ACTIVE.value
        obj.updated_by = approved_by
        obj.updated_at = datetime.now()
        await self._session.commit()
        await self._session.refresh(obj)
        return self._to_entity(obj)

    async def reject_customer(self, customer_id: str, rejected_by: UUID) -> Optional[Customer]:
        result = await self._session.execute(select(CustomerORM).where(CustomerORM.id == UUID(customer_id), CustomerORM.deleted_at == None))
        obj = result.scalar_one_or_none()
        if not obj:
            return None
        obj.status = CustomerStatus.REJECTED.value
        obj.updated_by = rejected_by
        obj.updated_at = datetime.now()
        await self._session.commit()
        await self._session.refresh(obj)
        return self._to_entity(obj)

    async def reassign_owner(self, customer_id: str, new_owner_sales_rep_id: UUID, reassigned_by: UUID) -> Optional[Customer]:
        result = await self._session.execute(select(CustomerORM).where(CustomerORM.id == UUID(customer_id), CustomerORM.deleted_at == None))
        obj = result.scalar_one_or_none()
        if not obj:
            return None
        obj.owner_sales_rep_id = new_owner_sales_rep_id
        obj.updated_by = reassigned_by
        obj.updated_at = datetime.now()
        await self._session.commit()
        await self._session.refresh(obj)
        return self._to_entity(obj)

    async def inactivate_customer(self, customer_id: str, inactivated_by: UUID) -> Optional[Customer]:
        result = await self._session.execute(select(CustomerORM).where(CustomerORM.id == UUID(customer_id), CustomerORM.deleted_at == None))
        obj = result.scalar_one_or_none()
        if not obj:
            return None
        obj.status = CustomerStatus.INACTIVE.value
        obj.updated_by = inactivated_by
        obj.updated_at = datetime.now()
        await self._session.commit()
        await self._session.refresh(obj)
        return self._to_entity(obj)

    def _to_entity(self, obj: CustomerORM) -> Customer:
        return Customer(
            id=obj.id,
            tenant_id=obj.tenant_id,
            customer_type=CustomerType(obj.customer_type),
            status=CustomerStatus(obj.status),
            name=obj.name,
            email=obj.email,
            phone_number=obj.phone_number,
            tax_pin=obj.tax_pin,
            incorporation_doc=obj.incorporation_doc,
            credit_days=obj.credit_days,
            credit_limit=float(obj.credit_limit) if obj.credit_limit is not None else None,
            owner_sales_rep_id=obj.owner_sales_rep_id,
            created_at=obj.created_at,
            created_by=obj.created_by,
            updated_at=obj.updated_at,
            updated_by=obj.updated_by,
            deleted_at=obj.deleted_at,
            deleted_by=obj.deleted_by,
            addresses=[]  # Initialize addresses as empty list
        ) 