"""
Config Router - Handles configuration management endpoints
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import logging
import yaml
from pathlib import Path

logger = logging.getLogger(__name__)

# Pydantic models
class ConfigUpdateRequest(BaseModel):
    """Request to update configuration"""
    section: str
    values: Dict[str, Any]

class ConfigResponse(BaseModel):
    """Response for configuration operations"""
    success: bool
    message: Optional[str] = None
    config: Optional[Dict[str, Any]] = None

# Global references
_config = None
_rebuild_callback = None

def set_config(config):
    """Set the config instance"""
    global _config
    _config = config

def set_rebuild_callback(callback):
    """Set the callback for rebuilding components after config change"""
    global _rebuild_callback
    _rebuild_callback = callback

# Create router
router = APIRouter(prefix="/api/config", tags=["configuration"])

@router.get("/reload")
async def reload_config() -> ConfigResponse:
    """
    Reload configuration from file
    
    Returns:
        Success status and message
    """
    logger.info("[CONFIG] Reloading configuration")
    
    if _config is None:
        raise HTTPException(
            status_code=503,
            detail="Configuration service not available"
        )
    
    try:
        _config.reload()
        logger.info("[CONFIG] Configuration reloaded successfully")
        
        # Trigger rebuild if callback is set
        if _rebuild_callback:
            try:
                _rebuild_callback()
                logger.info("[CONFIG] Components rebuilt after config reload")
            except Exception as e:
                logger.error(f"[CONFIG] Failed to rebuild components: {e}")
        
        return ConfigResponse(
            success=True,
            message="Configuration reloaded successfully"
        )
        
    except Exception as e:
        logger.error(f"[CONFIG] Failed to reload: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reload configuration: {str(e)}"
        )

@router.get("/current")
async def get_current_config() -> ConfigResponse:
    """
    Get current configuration
    
    Returns:
        Current configuration dictionary
    """
    logger.info("[CONFIG] Getting current configuration")
    
    if _config is None:
        raise HTTPException(
            status_code=503,
            detail="Configuration service not available"
        )
    
    try:
        # Get all configuration sections
        config_dict = {}
        
        # Common sections
        sections = [
            'store', 'llm', 'embedder', 'pipeline', 
            'policy', 'chunker', 'reranker', 'ingester'
        ]
        
        for section in sections:
            config_dict[section] = _config.get_section(section)
        
        return ConfigResponse(
            success=True,
            config=config_dict
        )
        
    except Exception as e:
        logger.error(f"[CONFIG] Failed to get config: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get configuration: {str(e)}"
        )

@router.post("/update")
async def update_config(request: ConfigUpdateRequest) -> ConfigResponse:
    """
    Update configuration section
    
    Args:
        request: Configuration update request
        
    Returns:
        Success status and message
    """
    logger.info(f"[CONFIG] Updating section: {request.section}")
    
    if _config is None:
        raise HTTPException(
            status_code=503,
            detail="Configuration service not available"
        )
    
    try:
        # Load current config file
        config_path = Path("config/config.yaml")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
        
        # Update the specified section
        if request.section not in config_data:
            config_data[request.section] = {}
        
        config_data[request.section].update(request.values)
        
        # Save updated config
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config_data, f, allow_unicode=True, sort_keys=False)
        
        # Reload config
        _config.reload()
        
        # Trigger rebuild if callback is set
        if _rebuild_callback:
            try:
                _rebuild_callback()
                logger.info("[CONFIG] Components rebuilt after config update")
            except Exception as e:
                logger.warning(f"[CONFIG] Failed to rebuild components: {e}")
        
        logger.info(f"[CONFIG] Successfully updated section: {request.section}")
        
        return ConfigResponse(
            success=True,
            message=f"Configuration section '{request.section}' updated successfully",
            config={request.section: config_data[request.section]}
        )
        
    except Exception as e:
        logger.error(f"[CONFIG] Failed to update: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update configuration: {str(e)}"
        )

@router.get("/section/{section}")
async def get_config_section(section: str) -> ConfigResponse:
    """
    Get specific configuration section
    
    Args:
        section: Name of the configuration section
        
    Returns:
        Configuration section data
    """
    logger.info(f"[CONFIG] Getting section: {section}")
    
    if _config is None:
        raise HTTPException(
            status_code=503,
            detail="Configuration service not available"
        )
    
    try:
        section_data = _config.get_section(section)
        
        if section_data is None:
            raise HTTPException(
                status_code=404,
                detail=f"Configuration section '{section}' not found"
            )
        
        return ConfigResponse(
            success=True,
            config={section: section_data}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[CONFIG] Failed to get section: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get configuration section: {str(e)}"
        )
