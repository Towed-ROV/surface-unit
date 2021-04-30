import pynmea2
import numpy as np
from nmea_data import data_types, data_values

"""
Created on Wed Jan 27 2021

@author: Fredborg
@version:0.1

Takes a string input and parses them with the NMEA0183 protocol.
"""


class NMEA_parser:
    """
    Parse NMEA data as a dict and values system.

    the NMEA parser can take a string input and return a more meaningful
    version of the data.
    """

    def __init__(self):
        """ Initialize class, sets the amount of errors to 0. """
        self.__parser_error_count = 0

    def parse_nmea_sentence(self, sentence):
        """
        takes a string as an input, checks the length of the string
        and returns the parsed message as another string.

        Parameters
        ----------
        sentence : String.
            An NMEA sentence should start with an  identifier such as: SDDBT
            and the different values are comma-separated, it ends with a
            checksum.

         Raises
         ------
         Exception:
             if the sentence cant be parsed the error message is printed and an
             exception is raised.

        Returns
        -------
        parsed sentence : String.
            A parsed sentence with the talker id, sentence type and
            data.

        """
        # print(sentence)
        try:
            parsed_sentence = pynmea2.parse(sentence)
            msg_type = parsed_sentence.sentence_type
            data = self.__order_data(self.__clean_data(parsed_sentence.data), msg_type)
            data_id = self.__get_data_type(msg_type)
            parsed_json = {data_id.lower(): data}
            return parsed_json

        except pynmea2.ParseError as e:
            print('parser error: ', format(e))
            self.__parser_error_count = self.__parser_error_count + 1
            print('parser error count: ', self.__parser_error_count)
            raise Exception(format(e))

    def parse_raw_message(self, raw_sentence):
        """
        Parse from a sentence with some noise around the NMEA sentence.

        NMEA sentences from serial communication often start with some
        unnecessary or invalid data. this message strips that data, before it
        parses the sentence.

        Parameters
        ----------
        raw_sentence : string
            This message should contain an NMEA message, but it does not need
            to start or end with it.

        Returns
        -------
        string
             A parsed sentence with the talker id, sentence type and
            data.

        """
        sentence = self.nmea_strip(raw_sentence)
        # parses and returns the sentence
        return self.parse_nmea_sentence(sentence)

    def nmea_strip(self, raw_sentence):
        # finds where the NMEA sentence starts or stops. if the message does
        # not have a "$" or "!" sign it's discarded. if a message does not
        # have a "*" sign, the checksum is missing and the index function
        # raises an Exception.
        try:
            start = raw_sentence.find('$')
            if start == -1:
                start = raw_sentence.find('!')
                if start == -1:
                    return
            stop = raw_sentence.index('*') + 3
        except:
            raise Exception("error: message has no checksum: ", raw_sentence)
        # strips the message down to the NMEA sentence
        return raw_sentence[start + 1:stop]

    def __clean_data(self, data):
        return [None if not v else float(v)
        if all((c in set('1234567890.'))
               for c in v) else v for v in data]

    def __get_data_type(self, identifier):
        if identifier in data_types:
            return data_types[identifier]
        else:
            return "%s: %s \n" % ("unknow ID", identifier)

    def __order_data(self, data, data_id):
        ordered_data = {}
        ordered_data, data_id, data = self.get_unit_indecies(ordered_data, data_id, data)
        ordered_data = self.add_names(ordered_data, data_id, data)
        return ordered_data

    def add_names(self, ordered_data, data_id, data):
        for i, v in enumerate(data):
            if v:
                if data_id in data_values.keys() and i < len(data_values[data_id]):

                    ordered_data[data_values[data_id][i]] = v
                else:
                    ordered_data["value_%s" % (i)] = v
        return ordered_data

    def get_unit_indecies(self, ordered_data, data_id, data):
        if "Unit" in data_values[data_id]:
            indexis = np.array([i for i, s in enumerate(data_values[data_id]) if s == "Unit"])
            indexis = indexis[0:len(data) - 1]
            for i in indexis[::-1]:
                s = "%s_in_%s" % (data_values[data_id][i - 1], data.pop(i))
                ordered_data[s] = data[i - 1]
                data.pop(i - 1)
        return ordered_data, data_id, data
