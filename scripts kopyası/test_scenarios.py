"""
Test Scenarios for Hospital-E
Runs predefined test scenarios from Team 1 requirements
"""
import sys
import time
import requests
from datetime import datetime

sys.path.append('..')

from config.settings import STOCK_MS_CONFIG, ORDER_MS_CONFIG, HOSPITAL_ID
from database.db_manager import db


class TestScenarioRunner:
    """Runs test scenarios for Hospital-E"""
    
    def __init__(self):
        self.stock_ms_url = f"http://localhost:{STOCK_MS_CONFIG['port']}"
        self.order_ms_url = f"http://localhost:{ORDER_MS_CONFIG['port']}"
    
    def print_header(self, title):
        """Print formatted header"""
        print("\n" + "=" * 70)
        print(f"  {title}")
        print("=" * 70)
    
    def print_result(self, scenario_name, data):
        """Print scenario result"""
        print(f"\n[{scenario_name}]")
        print(f"  Current Stock: {data.get('current_stock')} units")
        print(f"  Daily Consumption: {data.get('daily_consumption')} units")
        print(f"  Days of Supply: {data.get('days_of_supply'):.2f} days")
        print(f"  Threshold Breached: {data.get('threshold_breached')}")
        if data.get('threshold_breached'):
            print(f"  Alert Type: {data.get('alert_type')}")
            print(f"  Severity: {data.get('severity')}")
    
    def run_scenario_001(self):
        """SCEN-001: Normal Replenishment (Hospital-E)"""
        self.print_header("SCENARIO 001: Normal Replenishment")
        
        scenario_data = {
            'current_stock': 136,
            'daily_consumption': 68,
            'days_of_supply': 2.0,
            'expected_priority': 'HIGH'
        }
        
        print(f"\nTest Data:")
        print(f"  Current Stock: {scenario_data['current_stock']} units")
        print(f"  Daily Consumption: {scenario_data['daily_consumption']} units")
        print(f"  Days of Supply: {scenario_data['days_of_supply']} days")
        print(f"  Expected Priority: {scenario_data['expected_priority']}")
        
        # Update database
        db.update_stock(
            scenario_data['current_stock'],
            scenario_data['daily_consumption'],
            scenario_data['days_of_supply']
        )
        
        # Trigger stock check
        print("\nTriggering stock check...")
        response = requests.post(f"{self.stock_ms_url}/trigger")
        
        if response.status_code == 200:
            result = response.json()
            self.print_result("Result", result)
            
            # Check if order was created
            time.sleep(3)
            print("\nChecking for orders...")
            orders = requests.get(f"{self.order_ms_url}/orders").json()
            print(f"  Total orders in system: {orders['count']}")
        else:
            print(f"  ERROR: HTTP {response.status_code}")
    
    def run_scenario_002(self):
        """SCEN-002: Critical Shortage (Hospital-E)"""
        self.print_header("SCENARIO 002: Critical Shortage")
        
        scenario_data = {
            'current_stock': 34,
            'daily_consumption': 68,
            'days_of_supply': 0.5,
            'expected_priority': 'URGENT'
        }
        
        print(f"\nTest Data:")
        print(f"  Current Stock: {scenario_data['current_stock']} units")
        print(f"  Daily Consumption: {scenario_data['daily_consumption']} units")
        print(f"  Days of Supply: {scenario_data['days_of_supply']} days")
        print(f"  Expected Priority: {scenario_data['expected_priority']}")
        
        # Update database
        db.update_stock(
            scenario_data['current_stock'],
            scenario_data['daily_consumption'],
            scenario_data['days_of_supply']
        )
        
        # Trigger stock check
        print("\nTriggering stock check...")
        response = requests.post(f"{self.stock_ms_url}/trigger")
        
        if response.status_code == 200:
            result = response.json()
            self.print_result("Result", result)
            
            # Check if order was created
            time.sleep(3)
            print("\nChecking for orders...")
            orders = requests.get(f"{self.order_ms_url}/orders").json()
            print(f"  Total orders in system: {orders['count']}")
        else:
            print(f"  ERROR: HTTP {response.status_code}")
    
    def run_scenario_003(self):
        """SCEN-003: Stock Sufficient (Hospital-E)"""
        self.print_header("SCENARIO 003: Stock Sufficient")
        
        scenario_data = {
            'current_stock': 450,
            'daily_consumption': 68,
            'days_of_supply': 6.6,
            'expected_result': 'No order triggered'
        }
        
        print(f"\nTest Data:")
        print(f"  Current Stock: {scenario_data['current_stock']} units")
        print(f"  Daily Consumption: {scenario_data['daily_consumption']} units")
        print(f"  Days of Supply: {scenario_data['days_of_supply']} days")
        print(f"  Expected Result: {scenario_data['expected_result']}")
        
        # Update database
        db.update_stock(
            scenario_data['current_stock'],
            scenario_data['daily_consumption'],
            scenario_data['days_of_supply']
        )
        
        # Trigger stock check
        print("\nTriggering stock check...")
        response = requests.post(f"{self.stock_ms_url}/trigger")
        
        if response.status_code == 200:
            result = response.json()
            self.print_result("Result", result)
            
            if not result.get('threshold_breached'):
                print("\n  ✅ PASS: No order triggered as expected")
            else:
                print("\n  ❌ FAIL: Order was triggered unexpectedly")
        else:
            print(f"  ERROR: HTTP {response.status_code}")
    
    def run_all_scenarios(self):
        """Run all test scenarios"""
        self.print_header("Hospital-E Test Scenarios")
        print(f"Hospital: {HOSPITAL_ID}")
        print(f"StockMS: {self.stock_ms_url}")
        print(f"OrderMS: {self.order_ms_url}")
        
        # Check service health
        print("\nChecking service health...")
        try:
            stock_health = requests.get(f"{self.stock_ms_url}/health").json()
            order_health = requests.get(f"{self.order_ms_url}/health").json()
            print(f"  StockMS: {stock_health['status']}")
            print(f"  OrderMS: {order_health['status']}")
        except Exception as e:
            print(f"  ERROR: Services not available - {e}")
            return
        
        # Run scenarios
        scenarios = [
            self.run_scenario_001,
            self.run_scenario_002,
            self.run_scenario_003
        ]
        
        for scenario in scenarios:
            try:
                scenario()
                time.sleep(2)
            except Exception as e:
                print(f"\n  ERROR in scenario: {e}")
        
        # Final summary
        self.print_header("Test Summary")
        
        # Get performance stats
        try:
            perf = requests.get(f"{self.stock_ms_url}/performance").json()
            print("\nPerformance Comparison:")
            
            if 'SOA' in perf:
                print(f"\n  SOA Architecture:")
                print(f"    Events: {perf['SOA'].get('total_events', 0)}")
                print(f"    Avg Latency: {perf['SOA'].get('avg_latency', 0):.2f}ms")
                print(f"    P95 Latency: {perf['SOA'].get('p95_latency', 0):.2f}ms")
            
            if 'SERVERLESS' in perf:
                print(f"\n  Serverless Architecture:")
                print(f"    Events: {perf['SERVERLESS'].get('total_events', 0)}")
                print(f"    Avg Latency: {perf['SERVERLESS'].get('avg_latency', 0):.2f}ms")
                print(f"    P95 Latency: {perf['SERVERLESS'].get('p95_latency', 0):.2f}ms")
        except Exception as e:
            print(f"\n  Could not retrieve performance stats: {e}")
        
        # Get order stats
        try:
            stats = requests.get(f"{self.order_ms_url}/orders/stats").json()
            print("\nOrder Statistics:")
            print(f"  Total Orders: {stats['total']['total_orders']}")
            print(f"  Total Units: {stats['total']['total_units']}")
        except Exception as e:
            print(f"\n  Could not retrieve order stats: {e}")
        
        print("\n" + "=" * 70)
        print("  Test scenarios completed!")
        print("=" * 70)


def main():
    """Main entry point"""
    runner = TestScenarioRunner()
    runner.run_all_scenarios()


if __name__ == '__main__':
    main()