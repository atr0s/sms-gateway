import argparse
import asyncio
from typing import List
from pathlib import Path

from sms_gateway.ports.messaging import MessagingPort
from sms_gateway.ports.message_queue import MessageQueuePort
from sms_gateway.domain.config.base import SMSGatewayConfig
from sms_gateway.adapters.queues.factory import create_queue
from sms_gateway.common.logging import get_logger
from sms_gateway.config import load_config, get_default_config_path
from sms_gateway.services.sms import SMSService
from sms_gateway.services.integration import IntegrationService
from sms_gateway.integrations.services.registry import AdapterRegistry, AdapterType

class SMSGatewayDaemon:
    """
    Main daemon class that coordinates message handling services.
    
    This class manages:
    - Service initialization and lifecycle
    - Runtime configuration and control
    - Main processing loop coordination
    """
    
    def __init__(self, config: SMSGatewayConfig):
        """
        Initialize the daemon with configuration
        
        Args:
            config: Configuration object defining services and runtime settings
        """
        self.config = config
        self.logger = get_logger(f"gateway.{config.name}")
        
        # Internal state
        self.sms_ports: List[MessagingPort] = []
        self.integration_ports: List[MessagingPort] = []
        self.should_run = False
        
        # Initialize queues
        self.sms_queue = create_queue(
            config.queues.sms_queue,
            "SMS"
        )
        self.integration_queue = create_queue(
            config.queues.integration_queue,
            "integration"
        )
        
        # Initialize services
        self.sms_service = SMSService(
            self.sms_ports,
            self.integration_queue,
            self.sms_queue
        )
        self.integration_service = IntegrationService(
            self.integration_ports,
            self.sms_queue,
            self.integration_queue
        )
        
    async def initialize(self) -> None:
        """
        Initialize all adapters and prepare for operation
        
        This method:
        1. Initializes all adapters
        2. Validates configuration
        3. Logs initialization status
        
        Raises:
            ConfigurationError: If initialization fails
        """
        self.logger.info(f"Starting SMS Gateway daemon ({self.config.name})...")
        
        # Log registered adapters for debugging
        sms_adapters = AdapterRegistry._adapters.get(AdapterType.SMS, {}).keys()
        integration_adapters = AdapterRegistry._adapters.get(AdapterType.INTEGRATION, {}).keys()
        self.logger.info(f"Registered SMS adapters: {list(sms_adapters)}")
        self.logger.info(f"Registered integration adapters: {list(integration_adapters)}")
        
        # Initialize SMS adapters using registry
        sms_configs = {
            "stub": self.config.sms.stub or [],
            "gammu": self.config.sms.gammu or []
        }
        
        # Log configured adapters
        self.logger.info(f"Configured SMS adapters: {list(sms_configs.keys())}")
        self.sms_ports.extend(
            await AdapterRegistry.create_adapters(AdapterType.SMS, sms_configs)
        )
        
        # Initialize integration adapters using registry
        integration_configs = {
            "telegram": self.config.integration.telegram or []
        }
        
        # Log configured adapters
        self.logger.info(f"Configured integration adapters: {list(integration_configs.keys())}")
        self.integration_ports.extend(
            await AdapterRegistry.create_adapters(AdapterType.INTEGRATION, integration_configs)
        )
        
        if not self.sms_ports and not self.integration_ports:
            self.logger.warning(
                "No adapters were initialized. Check configuration and adapter registration."
            )
            
        # Log initialization status
        self.logger.info("Initialized services:")
        self.logger.info(f"- {len(self.sms_ports)} SMS adapters")
        self.logger.info(f"- {len(self.integration_ports)} integration adapters")
        self.logger.info(f"Poll delay: {self.config.runtime.poll_delay} seconds")
        
    async def shutdown(self) -> None:
        """
        Gracefully shutdown all services and adapters
        
        This method:
        1. Signals shutdown by setting should_run to False
        2. Attempts to shutdown each adapter
        3. Logs shutdown status
        """
        self.should_run = False
        self.logger.info("Initiating shutdown...")
        
        # Shutdown all adapters
        for port in self.sms_ports + self.integration_ports:
            try:
                await port.shutdown()
                self.logger.info(f"Shutdown {port.name} successfully")
            except Exception as e:
                self.logger.error(f"Error shutting down {port.name}: {e}")
                
        self.logger.info("Shutdown complete")
        
    async def check_services(self) -> None:
        """Check all services for new messages"""
        await self.sms_service.check_ports()
        await self.integration_service.check_ports()
        
    async def process_queues(self) -> None:
        """Process all message queues"""
        await self.sms_service.process_queue()
        await self.integration_service.process_queue()

    async def run(self) -> None:
        """
        Run the main message processing loop
        
        This method:
        1. Initializes the system
        2. Processes messages until shutdown
        3. Handles graceful shutdown
        """
        self.should_run = True
        
        try:
            # Initialize everything
            await self.initialize()
            
            # Main processing loop
            while self.should_run:
                # Process messages
                await self.check_services()
                await self.process_queues()
                
                # Sleep between cycles
                await asyncio.sleep(self.config.runtime.poll_delay)
                
        except KeyboardInterrupt:
            self.logger.info("\nReceived shutdown signal")
        finally:
            await self.shutdown()

async def async_main():
    """Async main entry point for the daemon"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="SMS Gateway Daemon")
    parser.add_argument(
        "-c", "--config",
        type=Path,
        default=get_default_config_path(),
        help="Path to configuration file (default: ./config.json)"
    )
    args = parser.parse_args()
    
    # Load and validate configuration
    try:
        config = load_config(args.config)
    except Exception as e:
        print(f"Failed to load configuration: {e}")
        return 1
        
    # Create and run daemon
    daemon = SMSGatewayDaemon(config)
    await daemon.run()
    return 0

def main():
    """Main entry point for the daemon"""
    try:
        return asyncio.run(async_main())
    except KeyboardInterrupt:
        return 0

if __name__ == "__main__":
    exit(main())