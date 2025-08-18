from typing import Dict, Type, TypeVar, Union, List, Optional
from pydantic import BaseModel
from sms_gateway.ports.messaging import MessagingPort
from sms_gateway.common.logging import get_logger

logger = get_logger("adapter.registry")

class AdapterType:
    """Available adapter types"""
    SMS = "sms"  # Must match config keys exactly
    INTEGRATION = "integration"  # Must match config keys exactly

class AdapterRegistry:
    """Central registry for managing messaging adapters"""
    
    _adapters: Dict[str, Dict[str, Type[MessagingPort]]] = {
        AdapterType.SMS: {},
        AdapterType.INTEGRATION: {}
    }

    @classmethod
    def register(
        cls,
        adapter_type: str,
        name: str
    ) -> callable:
        """Register an adapter class with the registry
        
        Args:
            adapter_type: Type of adapter (SMS/Integration)
            name: Name of the adapter implementation
            
        Returns:
            Decorator function to register the adapter class
        """
        # Convert type and name to lowercase for consistent lookup
        adapter_type = adapter_type.lower()
        name = name.lower()
        
        # Ensure valid adapter type
        if adapter_type not in cls._adapters:
            valid_types = list(cls._adapters.keys())
            raise ValueError(f"Invalid adapter type '{adapter_type}'. Must be one of: {valid_types}")
        
        def decorator(adapter_cls: Type[MessagingPort]) -> Type[MessagingPort]:
            cls._adapters[adapter_type][name] = adapter_cls
            logger.info(f"Registered {adapter_type} adapter: {name}")
            return adapter_cls
        return decorator

    @classmethod
    def get_adapter_class(
        cls,
        adapter_type: str,
        name: str
    ) -> Optional[Type[MessagingPort]]:
        """Get an adapter class from the registry
        
        Args:
            adapter_type: Type of adapter (SMS/Integration)
            name: Name of the adapter implementation
            
        Returns:
            The adapter class if found, None otherwise
        """
        # Convert type and name to lowercase for consistent lookup
        adapter_type = adapter_type.lower()
        name = name.lower()
        
        if adapter_type not in cls._adapters:
            return None
            
        return cls._adapters[adapter_type].get(name)

    @classmethod
    async def create_adapter(
        cls,
        adapter_type: str,
        name: str,
        config: BaseModel
    ) -> MessagingPort:
        """Create an adapter instance from registry
        
        Args:
            adapter_type: Type of adapter (SMS/Integration)
            name: Name of the adapter implementation
            config: Adapter configuration
            
        Returns:
            Initialized adapter instance
            
        Raises:
            KeyError: If adapter name not found in registry
        """
        # Convert type and name to lowercase for consistent lookup
        adapter_type = adapter_type.lower()
        name = name.lower()
        
        adapter_cls = cls.get_adapter_class(adapter_type, name)
        if not adapter_cls:
            raise KeyError(f"No {adapter_type} adapter registered with name: {name}")

        try:
            adapter = adapter_cls()
            await adapter.initialize(config)
            logger.info(f"Created {adapter_type} adapter: {config.name}")
            return adapter
        except Exception as e:
            logger.error(f"Failed to initialize {adapter_type} adapter {config.name}: {e}")
            raise

    @classmethod
    async def create_adapters(
        cls,
        adapter_type: str,
        configs: Dict[str, List[BaseModel]]
    ) -> List[MessagingPort]:
        """Create multiple adapter instances from configurations
        
        Args:
            adapter_type: Type of adapter (SMS/Integration)
            configs: Dictionary of adapter configs by adapter name
            
        Returns:
            List of initialized adapter instances
        """
        # Convert type to lowercase for consistent lookup
        adapter_type = adapter_type.lower()
        
        # Log available adapters for this type
        registered = list(cls._adapters.get(adapter_type, {}).keys())
        logger.info(f"Found {len(registered)} registered {adapter_type} adapters: {registered}")
        
        adapters = []
        for adapter_name, adapter_configs in configs.items():
            adapter_name = adapter_name.lower()
            for config in adapter_configs:
                if getattr(config, 'enabled', True):  # Default to enabled if not specified
                    try:
                        adapter = await cls.create_adapter(adapter_type, adapter_name, config)
                        adapters.append(adapter)
                    except KeyError as e:
                        logger.error(f"Failed to create adapter: {e}")
                    except Exception as e:
                        logger.error(f"Error initializing adapter {config.name}: {e}")
        
        logger.info(f"Created {len(adapters)} {adapter_type} adapters")
        return adapters