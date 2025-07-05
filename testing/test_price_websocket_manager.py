#!/usr/bin/env python3
"""
Unit tests for PriceWebSocketManager class.
Tests all functionality including initialization, price management, callbacks, and WebSocket handling.
"""

import unittest
import json
import time
import threading
from unittest.mock import Mock, patch, MagicMock, call
from queue import Queue, Empty
from typing import Dict, Set

# Import the class to test
from classes.price_websocket_manager import PriceWebSocketManager


class TestPriceWebSocketManager(unittest.TestCase):
    """Test cases for PriceWebSocketManager class."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        # Mock the websocket module to avoid actual network connections
        self.websocket_patcher = patch('classes.price_websocket_manager.websocket')
        self.mock_websocket = self.websocket_patcher.start()
        
        # Mock the logging to avoid file operations during tests
        self.logging_patcher = patch('classes.price_websocket_manager.logging')
        self.mock_logging = self.logging_patcher.start()
        
        # Create a mock WebSocketApp
        self.mock_ws_app = Mock()
        self.mock_websocket.WebSocketApp.return_value = self.mock_ws_app
        
        # Create instance for testing
        self.price_manager = PriceWebSocketManager()
        
        # Wait a bit for threads to initialize
        time.sleep(0.1)

    def tearDown(self):
        """Clean up after each test method."""
        # Stop the price manager
        if hasattr(self, 'price_manager'):
            self.price_manager.stop()
        
        # Stop all patches
        self.websocket_patcher.stop()
        self.logging_patcher.stop()

    def test_initialization(self):
        """Test that PriceWebSocketManager initializes correctly."""
        # Check that all attributes are properly initialized
        self.assertIsInstance(self.price_manager.prices, dict)
        self.assertIsInstance(self.price_manager.price_update_event, threading.Event)
        self.assertIsInstance(self.price_manager.callbacks, list)
        self.assertIsInstance(self.price_manager.symbols_queue, Queue)
        self.assertIsInstance(self.price_manager.lock, threading.Lock)
        
        # Check default values
        self.assertEqual(self.price_manager.reconnect_delay, 5)
        self.assertEqual(self.price_manager.max_reconnect_attempts, 5)
        self.assertEqual(self.price_manager.reconnect_attempts, 0)
        self.assertEqual(self.price_manager.subscription_interval, 2.0)
        self.assertEqual(self.price_manager.refresh_interval, 300)
        self.assertTrue(self.price_manager.running)
        self.assertFalse(self.price_manager.is_subscribing)
        
        # Check that WebSocket was started
        self.mock_websocket.WebSocketApp.assert_called_once()
        self.mock_ws_app.run_forever.assert_called_once()

    def test_add_price_callback(self):
        """Test adding price callbacks."""
        # Create a mock callback
        mock_callback = Mock()
        
        # Add the callback
        self.price_manager.add_price_callback(mock_callback)
        
        # Verify callback was added
        self.assertIn(mock_callback, self.price_manager.callbacks)
        self.assertEqual(len(self.price_manager.callbacks), 1)
        
        # Add another callback
        mock_callback2 = Mock()
        self.price_manager.add_price_callback(mock_callback2)
        
        # Verify both callbacks are present
        self.assertIn(mock_callback, self.price_manager.callbacks)
        self.assertIn(mock_callback2, self.price_manager.callbacks)
        self.assertEqual(len(self.price_manager.callbacks), 2)

    def test_update_symbols(self):
        """Test updating symbols to monitor."""
        # Test symbols
        test_symbols = {'BTCUSDT', 'ETHUSDT', 'BNBUSDT'}
        
        # Update symbols
        self.price_manager.update_symbols(test_symbols)
        
        # Verify symbols were added to queue
        try:
            queued_symbols = self.price_manager.symbols_queue.get_nowait()
            self.assertEqual(queued_symbols, test_symbols)
        except Empty:
            self.fail("Symbols were not added to queue")

    def test_get_price(self):
        """Test getting price for a specific symbol."""
        # Test with non-existent symbol
        self.assertIsNone(self.price_manager.get_price('NONEXISTENT'))
        
        # Add a test price
        test_symbol = 'BTCUSDT'
        test_price = 50000.0
        self.price_manager.prices[test_symbol] = test_price
        
        # Get the price
        result = self.price_manager.get_price(test_symbol)
        self.assertEqual(result, test_price)

    def test_get_all_prices(self):
        """Test getting all prices."""
        # Initially should be empty
        all_prices = self.price_manager.get_all_prices()
        self.assertEqual(all_prices, {})
        
        # Add some test prices
        test_prices = {
            'BTCUSDT': 50000.0,
            'ETHUSDT': 3000.0,
            'BNBUSDT': 400.0
        }
        self.price_manager.prices.update(test_prices)
        
        # Get all prices
        result = self.price_manager.get_all_prices()
        self.assertEqual(result, test_prices)
        
        # Verify it's a copy, not the original
        self.assertIsNot(result, self.price_manager.prices)

    def test_on_message_ticker_data(self):
        """Test processing ticker data messages."""
        # Create mock callbacks
        mock_callback1 = Mock()
        mock_callback2 = Mock()
        self.price_manager.add_price_callback(mock_callback1)
        self.price_manager.add_price_callback(mock_callback2)
        
        # Create test ticker message
        test_message = json.dumps({
            'stream': 'btcusdt@ticker',
            'data': {
                's': 'BTCUSDT',
                'c': '50000.00'
            }
        })
        
        # Process the message
        self.price_manager.on_message(None, test_message)
        
        # Verify price was updated
        self.assertEqual(self.price_manager.prices['BTCUSDT'], 50000.0)
        
        # Verify callbacks were called
        mock_callback1.assert_called_once_with('BTCUSDT', 50000.0)
        mock_callback2.assert_called_once_with('BTCUSDT', 50000.0)
        
        # Verify event was set
        self.assertTrue(self.price_manager.price_update_event.is_set())

    def test_on_message_pong(self):
        """Test processing pong messages."""
        # Create test pong message
        test_message = json.dumps({'e': 'pong'})
        
        # Process the message (should not raise any errors)
        try:
            self.price_manager.on_message(None, test_message)
        except Exception as e:
            self.fail(f"Processing pong message raised an exception: {e}")

    def test_on_message_subscription_response(self):
        """Test processing subscription response messages."""
        # Create test subscription response
        test_message = json.dumps({'result': ['btcusdt@ticker']})
        
        # Process the message (should not raise any errors)
        try:
            self.price_manager.on_message(None, test_message)
        except Exception as e:
            self.fail(f"Processing subscription response raised an exception: {e}")

    def test_on_message_invalid_json(self):
        """Test processing invalid JSON messages."""
        # Create invalid JSON message
        invalid_message = "invalid json message"
        
        # Process the message (should handle gracefully)
        try:
            self.price_manager.on_message(None, invalid_message)
        except Exception as e:
            self.fail(f"Processing invalid JSON raised an exception: {e}")

    def test_on_message_unrecognized_format(self):
        """Test processing unrecognized message format."""
        # Create unrecognized message
        unrecognized_message = json.dumps({'unknown': 'format'})
        
        # Process the message (should handle gracefully)
        try:
            self.price_manager.on_message(None, unrecognized_message)
        except Exception as e:
            self.fail(f"Processing unrecognized message raised an exception: {e}")

    def test_callback_exception_handling(self):
        """Test that callback exceptions are handled gracefully."""
        # Create a callback that raises an exception
        def failing_callback(symbol, price):
            raise ValueError("Test exception")
        
        self.price_manager.add_price_callback(failing_callback)
        
        # Create test ticker message
        test_message = json.dumps({
            'stream': 'btcusdt@ticker',
            'data': {
                's': 'BTCUSDT',
                'c': '50000.00'
            }
        })
        
        # Process the message (should not raise exception)
        try:
            self.price_manager.on_message(None, test_message)
        except Exception as e:
            self.fail(f"Callback exception was not handled: {e}")

    def test_on_error(self):
        """Test error handling."""
        # Mock the handle_reconnection method
        with patch.object(self.price_manager, 'handle_reconnection') as mock_handle:
            # Simulate an error
            test_error = Exception("Test error")
            self.price_manager.on_error(None, test_error)
            
            # Verify handle_reconnection was called
            mock_handle.assert_called_once()

    def test_on_close_normal(self):
        """Test normal WebSocket closure."""
        # Mock the handle_reconnection method
        with patch.object(self.price_manager, 'handle_reconnection') as mock_handle:
            # Simulate normal closure (status code 1000)
            self.price_manager.on_close(None, 1000, "Normal closure")
            
            # Verify handle_reconnection was NOT called for normal closure
            mock_handle.assert_not_called()

    def test_on_close_abnormal(self):
        """Test abnormal WebSocket closure."""
        # Mock the handle_reconnection method
        with patch.object(self.price_manager, 'handle_reconnection') as mock_handle:
            # Simulate abnormal closure (status code not 1000)
            self.price_manager.on_close(None, 1001, "Abnormal closure")
            
            # Verify handle_reconnection was called
            mock_handle.assert_called_once()

    def test_handle_reconnection_within_limits(self):
        """Test reconnection handling within attempt limits."""
        # Mock time.sleep to avoid actual delays
        with patch('time.sleep') as mock_sleep:
            # Mock start_websocket to avoid actual WebSocket creation
            with patch.object(self.price_manager, 'start_websocket') as mock_start:
                # Simulate reconnection attempts
                for i in range(3):
                    self.price_manager.handle_reconnection()
                
                # Verify attempts were incremented
                self.assertEqual(self.price_manager.reconnect_attempts, 3)
                
                # Verify start_websocket was called for each attempt
                self.assertEqual(mock_start.call_count, 3)
                
                # Verify sleep was called with increasing delays
                expected_calls = [
                    call(5),   # 5 * 2^0 = 5
                    call(10),  # 5 * 2^1 = 10
                    call(20)   # 5 * 2^2 = 20
                ]
                mock_sleep.assert_has_calls(expected_calls)

    def test_handle_reconnection_max_attempts(self):
        """Test reconnection handling when max attempts reached."""
        # Set reconnect attempts to max
        self.price_manager.reconnect_attempts = self.price_manager.max_reconnect_attempts
        
        # Mock start_websocket
        with patch.object(self.price_manager, 'start_websocket') as mock_start:
            # Try to reconnect
            self.price_manager.handle_reconnection()
            
            # Verify start_websocket was NOT called
            mock_start.assert_not_called()

    def test_update_subscriptions(self):
        """Test updating subscriptions."""
        # Mock the WebSocket connection
        self.price_manager.ws = Mock()
        self.price_manager.ws.sock = Mock()
        self.price_manager.ws.sock.connected = True
        
        # Mock send_subscription_group
        with patch.object(self.price_manager, 'send_subscription_group') as mock_send:
            # Test symbols
            test_symbols = {'BTCUSDT', 'ETHUSDT'}
            
            # Update subscriptions
            self.price_manager._update_subscriptions(test_symbols)
            
            # Verify subscription groups were created
            expected_streams = ['btcusdt@ticker', 'ethusdt@ticker']
            self.assertEqual(len(self.price_manager.subscription_groups), 1)
            self.assertEqual(self.price_manager.subscription_groups[0], expected_streams)
            
            # Verify send_subscription_group was called
            mock_send.assert_called_once_with(self.price_manager.ws)

    def test_update_subscriptions_websocket_disconnected(self):
        """Test updating subscriptions when WebSocket is disconnected."""
        # Mock disconnected WebSocket
        self.price_manager.ws = Mock()
        self.price_manager.ws.sock = Mock()
        self.price_manager.ws.sock.connected = False
        
        # Test symbols
        test_symbols = {'BTCUSDT', 'ETHUSDT'}
        
        # Update subscriptions (should not fail)
        try:
            self.price_manager._update_subscriptions(test_symbols)
        except Exception as e:
            self.fail(f"Updating subscriptions with disconnected WebSocket failed: {e}")

    def test_send_subscription_group_rate_limiting(self):
        """Test subscription group sending with rate limiting."""
        # Mock time.time to control timing
        with patch('time.time') as mock_time:
            mock_time.return_value = 1000.0
            
            # Set up subscription groups
            self.price_manager.subscription_groups = [['btcusdt@ticker'], ['ethusdt@ticker']]
            self.price_manager.current_group_index = 0
            
            # Mock WebSocket
            mock_ws = Mock()
            
            # Mock time.sleep
            with patch('time.sleep') as mock_sleep:
                # Send subscription group
                self.price_manager.send_subscription_group(mock_ws)
                
                # Verify subscription message was sent
                mock_ws.send.assert_called_once()
                
                # Verify the message format
                sent_message = mock_ws.send.call_args[0][0]
                message_data = json.loads(sent_message)
                self.assertEqual(message_data['method'], 'SUBSCRIBE')
                self.assertEqual(message_data['params'], ['btcusdt@ticker'])
                self.assertEqual(message_data['id'], 1)

    def test_stop(self):
        """Test stopping the price manager."""
        # Mock WebSocket close
        self.price_manager.ws = Mock()
        
        # Stop the manager
        self.price_manager.stop()
        
        # Verify running flag was set to False
        self.assertFalse(self.price_manager.running)
        
        # Verify WebSocket was closed
        self.price_manager.ws.close.assert_called_once()

    def test_thread_safety(self):
        """Test thread safety of update_symbols method."""
        # Create multiple threads that update symbols simultaneously
        def update_symbols_thread():
            for i in range(10):
                self.price_manager.update_symbols({f'SYMBOL{i}'})
                time.sleep(0.01)
        
        # Start multiple threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=update_symbols_thread)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify no exceptions were raised (thread safety maintained)
        # The test passes if no exceptions occur during execution


class TestPriceWebSocketManagerIntegration(unittest.TestCase):
    """Integration tests for PriceWebSocketManager (with mocked WebSocket)."""

    def setUp(self):
        """Set up test fixtures for integration tests."""
        # Mock the websocket module
        self.websocket_patcher = patch('classes.price_websocket_manager.websocket')
        self.mock_websocket = self.websocket_patcher.start()
        
        # Mock logging
        self.logging_patcher = patch('classes.price_websocket_manager.logging')
        self.mock_logging = self.logging_patcher.start()
        
        # Create mock WebSocketApp
        self.mock_ws_app = Mock()
        self.mock_websocket.WebSocketApp.return_value = self.mock_ws_app

    def tearDown(self):
        """Clean up after each test method."""
        self.websocket_patcher.stop()
        self.logging_patcher.stop()

    def test_full_price_update_cycle(self):
        """Test a complete price update cycle."""
        # Create price manager
        price_manager = PriceWebSocketManager()
        
        try:
            # Add callback
            received_prices = []
            def price_callback(symbol, price):
                received_prices.append((symbol, price))
            
            price_manager.add_price_callback(price_callback)
            
            # Update symbols
            test_symbols = {'BTCUSDT', 'ETHUSDT'}
            price_manager.update_symbols(test_symbols)
            
            # Wait for processing
            time.sleep(0.1)
            
            # Simulate price updates
            btc_message = json.dumps({
                'stream': 'btcusdt@ticker',
                'data': {'s': 'BTCUSDT', 'c': '50000.00'}
            })
            eth_message = json.dumps({
                'stream': 'ethusdt@ticker',
                'data': {'s': 'ETHUSDT', 'c': '3000.00'}
            })
            
            # Process messages
            price_manager.on_message(None, btc_message)
            price_manager.on_message(None, eth_message)
            
            # Verify prices were updated
            self.assertEqual(price_manager.get_price('BTCUSDT'), 50000.0)
            self.assertEqual(price_manager.get_price('ETHUSDT'), 3000.0)
            
            # Verify callbacks were called
            self.assertEqual(len(received_prices), 2)
            self.assertIn(('BTCUSDT', 50000.0), received_prices)
            self.assertIn(('ETHUSDT', 3000.0), received_prices)
            
            # Verify all prices
            all_prices = price_manager.get_all_prices()
            self.assertEqual(all_prices['BTCUSDT'], 50000.0)
            self.assertEqual(all_prices['ETHUSDT'], 3000.0)
            
        finally:
            price_manager.stop()


def run_tests():
    """Run all tests."""
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_suite.addTest(unittest.makeSuite(TestPriceWebSocketManager))
    test_suite.addTest(unittest.makeSuite(TestPriceWebSocketManagerIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    exit(0 if success else 1) 