import logging
from fastapi import APIRouter, HTTPException, status
from app.services.portal_service import portal_service

logger = logging.getLogger("hav_scrap")

router = APIRouter(prefix="/portal", tags=["Haveloc Portal & Session"])


@router.get("/status", summary="Retrieve portal connection & authentication status")
async def get_portal_status():
    """
    Returns current browser process status, authentication phase,
    target dashboard accessibility, and diagnostic flags.
    Never exposes credentials, session cookies, or tokens.
    """
    try:
        return portal_service.get_status()
    except Exception as e:
        logger.error(f"Error fetching portal status: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unable to retrieve portal telemetry: {str(e)}"
        )


@router.get("/info", summary="Retrieve safe portal configuration and paths")
async def get_portal_info():
    """
    Returns non-sensitive portal configuration details, including
    login URL, target dashboard URL, profile path, and driver availability.
    """
    try:
        return portal_service.get_info()
    except Exception as e:
        logger.error(f"Error fetching portal info: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unable to retrieve portal info: {str(e)}"
        )


@router.post("/connect", summary="Launch visible Chromium browser for manual authentication")
async def connect_portal():
    """
    Launches a visible Chromium persistent browser window and navigates to
    https://haveloc.com/ so the operator can manually enter credentials.
    Zero automated password entry or CAPTCHA bypass is performed.
    """
    try:
        result = await portal_service.connect()
        return {
            "success": result["authentication_status"] not in ["ERROR"],
            "data": result,
            "message": "Visible browser launched. Please enter credentials in the browser window to complete login."
            if result["authentication_status"] == "AWAITING_LOGIN"
            else result.get("last_error_message", "Portal connection updated.")
        }
    except Exception as e:
        logger.error(f"Error initiating portal connection: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initiate portal connection: {str(e)}"
        )


@router.post("/reconnect", summary="Attempt session restoration using existing persistent profile")
async def reconnect_portal():
    """
    Restores the persistent browser context and validates if previously saved
    session cookies are still accepted by the target placement dashboard.
    """
    try:
        result = await portal_service.reconnect()
        return {
            "success": result["authentication_status"] == "CONNECTED",
            "data": result,
            "message": "Session restored successfully. Dashboard is active."
            if result["authentication_status"] == "CONNECTED"
            else result.get("last_error_message", "Session could not be restored automatically.")
        }
    except Exception as e:
        logger.error(f"Error during session reconnection: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reconnect portal session: {str(e)}"
        )


@router.post("/disconnect", summary="Close browser and disconnect portal session")
async def disconnect_portal():
    """
    Safely terminates the Chromium browser instance and closes context without
    erasing the local profile directory.
    """
    try:
        result = await portal_service.disconnect()
        return {
            "success": True,
            "data": result,
            "message": "Portal session disconnected cleanly. Browser profile retained locally."
        }
    except Exception as e:
        logger.error(f"Error disconnecting portal: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to disconnect portal: {str(e)}"
        )

