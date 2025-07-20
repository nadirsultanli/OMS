from fastapi import Depends
# from app.services.customers import CustomerService
# from app.infrastucture.database.repositories.customer_repository import CustomerRepository


# def get_customer_repository() -> CustomerRepository:
#     """Dependency to get customer repository instance"""
#     return CustomerRepository()


# def get_customer_service(
#     customer_repo: CustomerRepository = Depends(get_customer_repository)
# ) -> CustomerService:
#     """Dependency to get customer service instance"""
#     return CustomerService(customer_repo) 