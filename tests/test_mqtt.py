import os
import unittest
from unittest.mock import patch, call, Mock

from modbus4mqtt import modbus4mqtt

def assert_no_call(self, *args, **kwargs):
    try:
        self.assert_any_call(*args, **kwargs)
    except AssertionError:
        return
    raise AssertionError('Expected %s to not have been called.' % self._format_mock_call_signature(args, kwargs))

Mock.assert_no_call = assert_no_call

class BasicTests(unittest.TestCase):

    def setUp(self):
        self.modbus_tables = {'input': {}, 'holding': {}}

    def tearDown(self):
        pass

    def modbus_registers(self, table, address):
        if address not in self.modbus_tables[table]:
            return 0
        return self.modbus_tables[table][address]

    def test_pub_on_change(self):
        with patch('paho.mqtt.client.Client') as mock_mqtt:
            with patch('modbus4mqtt.modbus_interface.modbus_interface') as mock_modbus:

                mock_modbus().get_value.side_effect = self.modbus_registers

                m = modbus4mqtt.mqtt_interface('kroopit', 1885, 'brengis', 'pranto', './tests/test.yaml', 'test')
                m.connect()

                mock_mqtt().username_pw_set.assert_called_with('brengis', 'pranto')
                mock_mqtt().connect.assert_called_with('kroopit', 1885, 60)

                self.modbus_tables['holding'][1] = 85
                self.modbus_tables['holding'][2] = 86
                self.modbus_tables['holding'][3] = 87

                m.poll()

                # Check that every topic was published initially
                mock_mqtt().publish.assert_any_call('test/pub_on_change_false', 85, retain=False)
                mock_mqtt().publish.assert_any_call('test/pub_on_change_true', 86, retain=False)
                mock_mqtt().publish.assert_any_call('test/pub_on_change_absent', 87, retain=False)
                mock_mqtt().publish.reset_mock()

                self.modbus_tables['holding'][1] = 15
                self.modbus_tables['holding'][2] = 16
                self.modbus_tables['holding'][3] = 17

                m.poll()

                # Check that every topic was published if everything changed
                mock_mqtt().publish.assert_any_call('test/pub_on_change_false', 15, retain=False)
                mock_mqtt().publish.assert_any_call('test/pub_on_change_true', 16, retain=False)
                mock_mqtt().publish.assert_any_call('test/pub_on_change_absent', 17, retain=False)
                mock_mqtt().publish.reset_mock()

                m.poll()

                # Check that the register with pub_only_on_change: true does not re-publish
                mock_mqtt().publish.assert_any_call('test/pub_on_change_false', 15, retain=False)
                mock_mqtt().publish.assert_no_call('test/pub_on_change_true', 16, retain=False)
                mock_mqtt().publish.assert_any_call('test/pub_on_change_absent', 17, retain=False)


if __name__ == "__main__":
    unittest.main()