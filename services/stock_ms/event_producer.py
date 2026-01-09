"""
Event Hub Producer for Hospital-E
Publishes InventoryLowEvents to Azure Event Hub
"""
import asyncio
import json
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict

from azure.eventhub import EventData, TransportType
from azure.eventhub.aio import EventHubProducerClient

from config.settings import EVENT_HUB_CONFIG, HOSPITAL_ID
from database.db_manager import db

logger = logging.getLogger(__name__)


class EventHubProducer:
    """Publishes events to Azure Event Hub"""
    
    def __init__(self):
        self.connection_string = EVENT_HUB_CONFIG['connection_string']
        self.event_hub_name = EVENT_HUB_CONFIG['inventory_topic']
        self.producer = None
    
    def _create_inventory_low_event(
        self,
        current_stock: int,
        daily_consumption: int,
        days_of_supply: float,
        threshold: float = 2.0
    ) -> Dict:
        """
        Create InventoryLowEvent matching Team 1's schema
        Schema: contracts/schemas/InventoryLowEvent.schema.json
        """
        event = {
            "eventId": f"evt-{uuid.uuid4()}",
            "eventType": "InventoryLow",
            "hospitalId": HOSPITAL_ID,
            "productCode": "PHYSIO-SALINE-500ML",
            "currentStockUnits": current_stock,
            "dailyConsumptionUnits": daily_consumption,
            "daysOfSupply": round(days_of_supply, 2),
            "threshold": threshold,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        return event
    
    async def publish_inventory_low_event(
        self,
        current_stock: int,
        daily_consumption: int,
        days_of_supply: float,
        threshold: float = 2.0
    ) -> bool:
        """
        Publish InventoryLowEvent to Event Hub
        
        Args:
            current_stock: Current stock units
            daily_consumption: Daily consumption units
            days_of_supply: Calculated days of supply
            threshold: Threshold that triggered this event
        
        Returns:
            True if successful, False otherwise
        """
        event_data = self._create_inventory_low_event(
            current_stock, daily_consumption, days_of_supply, threshold
        )
        
        logger.info(
            f"[EVENT HUB] Publishing InventoryLowEvent: "
            f"{current_stock} units, {days_of_supply:.2f} days"
        )
        
        try:
            start_time = time.time()
            
            # Create producer with WebSocket transport for firewall compatibility
            producer = EventHubProducerClient.from_connection_string(
                conn_str=self.connection_string,
                eventhub_name=self.event_hub_name,
                transport_type=TransportType.AmqpOverWebsocket
            )
            
            async with producer:
                # Create batch and add event
                event_batch = await producer.create_batch()
                event_batch.add(EventData(json.dumps(event_data)))
                
                # Send batch
                await producer.send_batch(event_batch)
                
                latency_ms = int((time.time() - start_time) * 1000)
                
                # Log success
                db.log_event(
                    event_type='INVENTORY_EVENT_PUBLISHED',
                    direction='OUTGOING',
                    architecture='SERVERLESS',
                    payload=json.dumps(event_data),
                    status='SUCCESS',
                    latency_ms=latency_ms
                )
                
                logger.info(
                    f"[EVENT HUB] Event published successfully: "
                    f"{event_data['eventId']}, latency={latency_ms}ms"
                )
                return True
        
        except Exception as e:
            logger.error(f"[EVENT HUB] Failed to publish event: {e}")
            
            db.log_event(
                event_type='INVENTORY_EVENT_PUBLISHED',
                direction='OUTGOING',
                architecture='SERVERLESS',
                payload=json.dumps(event_data),
                status='FAILURE',
                error_message=str(e)
            )
            return False
    
    def publish_event_sync(
        self,
        current_stock: int,
        daily_consumption: int,
        days_of_supply: float,
        threshold: float = 2.0
    ) -> bool:
        """Synchronous wrapper for publish_inventory_low_event"""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(
            self.publish_inventory_low_event(
                current_stock, daily_consumption, days_of_supply, threshold
            )
        )
    
    async def test_connection(self) -> bool:
        """Test Event Hub connection"""
        try:
            producer = EventHubProducerClient.from_connection_string(
                conn_str=self.connection_string,
                eventhub_name=self.event_hub_name,
                transport_type=TransportType.AmqpOverWebsocket
            )
            
            async with producer:
                test_event = {
                    "eventType": "ConnectionTest",
                    "hospitalId": HOSPITAL_ID,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                
                event_batch = await producer.create_batch()
                event_batch.add(EventData(json.dumps(test_event)))
                await producer.send_batch(event_batch)
                
                logger.info("[EVENT HUB] Connection test successful")
                return True
        
        except Exception as e:
            logger.error(f"[EVENT HUB] Connection test failed: {e}")
            return False


# Singleton instance
event_producer = EventHubProducer()