"""
Event Hub Consumer for Hospital-E
Consumes OrderCreationCommand events from Azure Event Hub
"""
import asyncio
import json
import logging
from typing import Dict

from azure.eventhub import TransportType
from azure.eventhub.aio import EventHubConsumerClient

from config.settings import EVENT_HUB_CONFIG, HOSPITAL_ID
from database.db_manager import db

logger = logging.getLogger(__name__)


class EventHubConsumer:
    """Consumes order commands from Azure Event Hub"""
    
    def __init__(self):
        self.connection_string = EVENT_HUB_CONFIG['connection_string']
        self.event_hub_name = EVENT_HUB_CONFIG['order_topic']
        self.consumer_group = EVENT_HUB_CONFIG['consumer_group']
        self.running = False
    
    def validate_order_command(self, command: Dict) -> bool:
        """
        Validate OrderCreationCommand against schema
        Schema: contracts/schemas/OrderCreationCommand.schema.json
        """
        required_fields = [
            'commandId', 'commandType', 'orderId', 'hospitalId',
            'productCode', 'orderQuantity', 'priority',
            'estimatedDeliveryDate', 'timestamp'
        ]
        
        # Check all required fields exist
        for field in required_fields:
            if field not in command:
                logger.error(f"Missing required field: {field}")
                return False
        
        # Validate commandType
        if command['commandType'] != 'CreateOrder':
            logger.error(f"Invalid commandType: {command['commandType']}")
            return False
        
        # Validate priority
        if command['priority'] not in ['URGENT', 'HIGH', 'NORMAL']:
            logger.error(f"Invalid priority: {command['priority']}")
            return False
        
        return True
    
    def should_process_order(self, command: Dict) -> bool:
        """
        Check if order is for Hospital-E
        CRITICAL: Only process orders for our hospital!
        """
        hospital_id = command.get('hospitalId', '')
        
        if hospital_id != HOSPITAL_ID:
            logger.debug(f"Skipping order for {hospital_id} (not {HOSPITAL_ID})")
            return False
        
        return True
    
    def process_order_command(self, command: Dict):
        """
        Process an OrderCreationCommand and save to database
        
        Args:
            command: OrderCreationCommand payload
        """
        try:
            # Validate schema
            if not self.validate_order_command(command):
                logger.error("Invalid order command schema")
                db.log_event(
                    event_type='ORDER_RECEIVED',
                    direction='INCOMING',
                    architecture='SERVERLESS',
                    payload=json.dumps(command),
                    status='FAILURE',
                    error_message='Schema validation failed'
                )
                return
            
            # Check if order is for us
            if not self.should_process_order(command):
                return
            
            logger.info(
                f"📦 ORDER RECEIVED: {command['orderId']} - "
                f"{command['orderQuantity']} units, Priority: {command['priority']}"
            )
            
            # Save to database
            success = db.insert_order(command)
            
            if success:
                db.log_event(
                    event_type='ORDER_RECEIVED',
                    direction='INCOMING',
                    architecture='SERVERLESS',
                    payload=json.dumps(command),
                    status='SUCCESS'
                )
                logger.info(f"✅ Order saved: {command['orderId']}")
            else:
                db.log_event(
                    event_type='ORDER_RECEIVED',
                    direction='INCOMING',
                    architecture='SERVERLESS',
                    payload=json.dumps(command),
                    status='FAILURE',
                    error_message='Database insert failed (likely duplicate)'
                )
                logger.warning(f"⚠️  Order already exists: {command['orderId']}")
        
        except Exception as e:
            logger.error(f"Error processing order command: {e}")
            db.log_event(
                event_type='ORDER_RECEIVED',
                direction='INCOMING',
                architecture='SERVERLESS',
                payload=json.dumps(command),
                status='FAILURE',
                error_message=str(e)
            )
    
    async def on_event(self, partition_context, event):
        """
        Event handler callback
        
        Args:
            partition_context: Partition context for checkpointing
            event: Event data from Event Hub
        """
        try:
            # Parse event body
            event_body = event.body_as_str(encoding='UTF-8')
            
            # Handle batch of commands (array)
            try:
                commands = json.loads(event_body)
                if isinstance(commands, list):
                    logger.info(f"📥 Received batch of {len(commands)} commands")
                    for command in commands:
                        self.process_order_command(command)
                else:
                    # Single command
                    self.process_order_command(commands)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse event body as JSON: {e}")
                logger.debug(f"Event body: {event_body}")
            
            # Update checkpoint
            await partition_context.update_checkpoint(event)
        
        except Exception as e:
            logger.error(f"Error in event handler: {e}")
    
    async def on_error(self, partition_context, error):
        """Error handler callback"""
        logger.error(f"Event Hub error on partition {partition_context.partition_id}: {error}")
    
    async def start_consuming(self):
        """Start consuming events from Event Hub"""
        logger.info(f"🎧 Starting Event Hub consumer for {HOSPITAL_ID}")
        logger.info(f"   Event Hub: {self.event_hub_name}")
        logger.info(f"   Consumer Group: {self.consumer_group}")
        
        self.running = True
        
        # Create consumer with WebSocket transport
        client = EventHubConsumerClient.from_connection_string(
            conn_str=self.connection_string,
            consumer_group=self.consumer_group,
            eventhub_name=self.event_hub_name,
            transport_type=TransportType.AmqpOverWebsocket
        )
        
        try:
            async with client:
                logger.info("✅ Connected to Event Hub")
                logger.info("⏳ Waiting for order commands...")
                
                # Start receiving events
                await client.receive(
                    on_event=self.on_event,
                    on_error=self.on_error,
                    starting_position="-1"  # Start from beginning
                )
        
        except KeyboardInterrupt:
            logger.info("🛑 Consumer stopped by user")
            self.running = False
        except Exception as e:
            logger.error(f"Consumer error: {e}")
            self.running = False
    
    def start(self):
        """Synchronous wrapper to start consumer"""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        loop.run_until_complete(self.start_consuming())
    
    async def test_connection(self) -> bool:
        """Test Event Hub connection"""
        try:
            client = EventHubConsumerClient.from_connection_string(
                conn_str=self.connection_string,
                consumer_group=self.consumer_group,
                eventhub_name=self.event_hub_name,
                transport_type=TransportType.AmqpOverWebsocket
            )
            
            async with client:
                logger.info("[EVENT HUB] Consumer connection test successful")
                return True
        
        except Exception as e:
            logger.error(f"[EVENT HUB] Consumer connection test failed: {e}")
            return False


# Singleton instance
event_consumer = EventHubConsumer()