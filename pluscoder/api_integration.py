from contextlib import suppress
from json import JSONDecodeError
from typing import Dict

import httpx

from pluscoder.config import config
from pluscoder.exceptions import TokenValidationException

API_BASE_URL = "https://api.pluscoder.cl/api"


async def verify_token() -> Dict:
    """Verify if the provided token is valid and return associated information"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{API_BASE_URL}/subscription/verify-token",
                headers={"Authorization": f"Token {config.pluscoder_token}", "Content-Type": "application/json"},
            )
            if response.status_code != 200:
                raise TokenValidationException(response.json()["detail"])
            return response.json()
        except httpx.RequestError as err:
            error_msg = "Failed to connect to API: " + str(err)
            raise TokenValidationException(error_msg) from err
        except JSONDecodeError:
            raise TokenValidationException("Invalid token")  # noqa: B904


async def register_call() -> None:
    """Register an API call for usage tracking"""
    async with httpx.AsyncClient() as client:
        with suppress(httpx.RequestError):
            await client.post(
                f"{API_BASE_URL}/subscription/register-call",
                headers={"Authorization": f"Token {config.pluscoder_token}", "Content-Type": "application/json"},
            )
