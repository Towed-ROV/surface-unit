"""
Created on Wed Jan 27 16:57:03 2021.

@author: Fredborg
class for receiving and handling NMEA messages over serial.
"""
from NMEA_0183_parser import NMEA_parser
import time
import serial
from threading import Thread


class server(Thread):
    """
    Receives and parses NMEA 0183 messages from a serial port.

    Then it stores the message in a storage box.
    """

    def __init__(self, port, baudrate, storage_box, frequency):
        """
        init.

        Defines the serial port and parser and other variables and constants.

        Parameters
        ----------
        port: string
            the port that the server should connect to and read.

        """
        Thread.__init__(self)

        self.__parser = NMEA_parser()
        self.__ser = serial.Serial(port,
                                   baudrate,
                                   timeout=1,
                                   stopbits=1,
                                   bytesize=8)
        self.SERVER_START = ""
        self.com_err = 0
        self.box = storage_box
        self.frequency = frequency

    def run(self):
        """
        Run the Thread, reciving nmea data and parsing it.

        Returns
        -------
        None.

        """
        while True:
            start = time.process_time()
            message = self.get_message()

            self.box.update(message)
            end = time.process_time()
            time.sleep(1/self.frequency-(end-start)+3)

    def __get_current_time_str(self):
        """
        Get the current time as a string.

        Returns
        -------
        string
            returns a string with the current time in the format ss:mm:tt.
        """
        timer = time.localtime()
        return "%i:%i:%i" % (timer.tm_sec,  timer.tm_min, timer.tm_hour)

    def __get_current_date_str(self):
        """
        Get the current time.

        Returns
        -------
        string
            Returns a string with the current time in the format dd:mm:yyyy.

        """
        timer = time.localtime()
        return "%i:%i:%i" % (timer.tm_mday, timer.tm_mon, timer.tm_year)

    def get_message(self):
        """
        Get and parse message from the serial port.

        Raises
        ------
        e
            if the server has a problem and cannot connect to the serial port
            after multiple attempts, it fails and raises an Exception.

        Returns
        -------
        serial
            a parsed NMEA message.

        """
        try:
            if self.ready():
                data = str(self.__ser.readline())

                try:
                    parsed_data = self.__parser.parse_raw_message(data)
                except Exception as e:
                    print(format(e))
                    return

                return parsed_data
        except serial.SerialException as e:
            print('communication error: ', format(e))
            time.sleep(0.5)
            self.com_err += 1

            if self.com_err < 5:
                return self.get_message()
            else:
                raise e
        except UnicodeDecodeError as e:
            print('decode error: ', format(e))
            time.sleep(0.5)
            self.com_err += 1
            if self.com_err < 5:
                return self.get_message()
            raise e

    def __set_start_time(self):
        """
        Set the start time of the server.

        Returns
        -------
        None.

        """
        self.SERVER_START = "%s -:- %s" % (self.get_current_date_str(),
                                           self.get_current_time_str())

    def ready(self):
        """
        Check if there are bytes waiting.

        Returns
        -------
        boolean
            returns true if the server is ready to parse an NMEA message, false
            otherwise.
        """
        return self.__ser.inWaiting() > 10
