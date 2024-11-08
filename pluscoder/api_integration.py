from contextlib import suppress
from typing import Dict

import httpx

from pluscoder.config import config
from pluscoder.exceptions import TokenValidationException

API_BASE_URL = "http://127.0.0.1:8000/api"


async def verify_token() -> Dict:
    """Verify if the provided token is valid and return associated information"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{API_BASE_URL}/subscription/verify-token",
                headers={"Authorization": f"Token {config.pluscoder_token}"},
            )
            if response.status_code != 200:
                raise TokenValidationException(response.json().get("detail", "Unknown error"))

            data = response.json()
            if not data.get("valid"):
                raise TokenValidationException("Invalid token")

            return data
        except httpx.RequestError as err:
            error_msg = "Failed to connect to API: " + str(err)
            raise TokenValidationException(error_msg) from err


async def register_call() -> None:
    """Register an API call for usage tracking"""
    async with httpx.AsyncClient() as client:
        with suppress(httpx.RequestError):
            await client.post(
                f"{API_BASE_URL}/subscription/register-call",
                headers={"Authorization": f"Token {config.pluscoder_token}"},
            )
