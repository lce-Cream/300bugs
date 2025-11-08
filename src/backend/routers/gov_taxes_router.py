# from typing import List, Optional
#
# from fastapi import APIRouter, HTTPException
#
# from configs.logger import LOGGER
# from schemas.gov_taxes_schemas import GovInfoSubject, GovShortInfoSubject
# from services.gov_service import get_info_by_regon, get_info_by_nip, get_account_short_descriptions_by_name
#
# gov_taxes_router = APIRouter()
#
#
# @gov_taxes_router.get(
#     "/regon/{regon}",
#     summary="Get info from gov.pl by 'regon' number",
#     description="Returns the organization details by 'regon' number.",
#     response_model=GovInfoSubject,
#     responses={
#         404: {
#             "description": "REGON not found",
#             "content": {
#                 "application/json": {
#                     "example": {"detail": "REGON 123456789 not found"}
#                 }
#             }
#         }
#     }
# )
# async def get_info_by_regon_endpoint(regon: str) -> GovInfoSubject:
#     """
#     Get organization details from gov.pl by 'regon' number.
#
#     Args:
#         regon (str): The REGON number to search for.
#
#     Returns:
#         GovInfoSubject: Organization details matching the REGON number.
#     """
#     LOGGER.debug(f"Get info by regon: {regon}")
#     try:
#         return await get_info_by_regon(regon)
#     except Exception as e:
#         LOGGER.error(f"Not found or error for regon {regon}: {e}")
#         raise HTTPException(status_code=404, detail=f"REGON {regon} not found")
#
#
# @gov_taxes_router.get(
#     "/nip/{nip}",
#     summary="Get info from gov.pl by 'nip' number",
#     description="Returns the organization details by 'nip' number.",
#     response_model=GovInfoSubject,
#     responses={
#         404: {
#             "description": "NIP not found",
#             "content": {
#                 "application/json": {
#                     "example": {"detail": "NIP 123456789 not found"}
#                 }
#             }
#         }
#     }
# )
# async def get_info_by_nip_endpoint(nip: str) -> GovInfoSubject:
#     """
#     Get organization details from gov.pl by 'nip' number.
#
#     Args:
#         nip (str): The NIP number to search for.
#
#     Returns:
#         GovInfoSubject: Organization details matching the NIP number.
#     """
#     LOGGER.debug(f"Get info by nip:: {nip}")
#     try:
#         return await get_info_by_nip(nip)
#     except Exception as e:
#         LOGGER.error(f"Not found or error for nip {nip}: {e}")
#         raise HTTPException(status_code=404, detail=f"NIP {nip} not found")
#
#
# @gov_taxes_router.get(
#     "/name/{name}",
#     summary="Get accounts short descriptions from gov.pl by any 'name'",
#     description="Returns accounts short descriptions by any 'name'.",
#     response_model=List[GovShortInfoSubject],
#     responses={
#         404: {
#             "description": "Name not found",
#             "content": {
#                 "application/json": {
#                     "example": {"detail": "Name 'some_name' not found"}
#                 }
#             }
#         }
#     }
# )
# async def get_accounts_by_name_endpoint(name: str) -> List[GovShortInfoSubject]:
#     """
#     Get accounts short descriptions from gov.pl by account name.
#
#     Args:
#         name (str): The account name to search for.
#
#     Returns:
#         List[GovShortInfoSubject]: List of possible short descriptions matching the account number.
#     """
#     LOGGER.debug(f"Get accounts short description by account name: {name}")
#     try:
#         return await get_account_short_descriptions_by_name(name)
#     except Exception as e:
#         LOGGER.error(f"Not found or error for name {name}: {e}")
#         raise HTTPException(status_code=404, detail=f"Name {name} not found")