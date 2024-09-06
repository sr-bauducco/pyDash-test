# -*- coding: utf-8 -*-
from player.parser import *
from player.player import *
from base.configuration_parser import *
from r2a.ir2a import IR2A
import timeit
import http.client

class R2ANewMethod(IR2A):

    def __init__(self, id):
        IR2A.__init__(self, id)
        self.parsed_mpd : mpd_node = ''
        self.qi : list = []
        self.initial_buffer : int = int(ConfigurationParser.get_instance().get_parameter('buffering_until'))
        self.segment_size : dict = dict()
        self.start_time : float = 0
        self.weighted_mean_rate : float = 0
        self.sample_count : int = 5
        self.segment_info : list = list()
        self.current_segment_size : int = 0
        self.current_bitrate : int = 46980
        self.alpha : int = 10
        self.beta : int = 15

    def handle_xml_request(self, msg):
        self.send_down(msg)

    def handle_xml_response(self, msg):
        self.parsed_mpd = parse_mpd(msg.get_payload())
        self.qi = self.parsed_mpd.get_qi()
        
        for number in range(1, 597):
            self.segment_size[number] = dict()
        for quality in self.qi:
            port = '80'
            host_name = "45.171.101.167"
            path_name = f"http://45.171.101.167/DASHDataset/BigBuckBunny/1sec/bunny_{quality}bps/"
            connection = http.client.HTTPConnection(host_name, port)
            connection.request('GET', path_name)
            ss_file = connection.getresponse().read()
            file = ss_file.decode()
            for line in file.splitlines():
                if line.count("m4s"):
                    data = line.split('td')
                    number = int(data[3].split('.')[0].split('s')[-1])
                    size = data[7].split('<')[0].split('>')[-1]
                    size = float(size.replace('K',''))*1000 if size.count('K') else float(size.replace('M',''))*1000000 if size.count('M') else float(size)
                    self.segment_size[number][quality] = size*8

            connection.close()

        self.send_up(msg)

    def handle_segment_size_request(self, msg : SSMessage):             
      pass
    def handle_segment_size_response(self, msg):
       pass

    def update_weighted_mean(self, segment_size, segment_download_time):
        segment_download_rate = segment_size / segment_download_time

        while(len(self.segment_info) > self.sample_count):
            self.segment_info.pop(0)
        self.segment_info.append((segment_size, segment_download_rate))
        self.weighted_mean_rate = sum([size for size, _ in self.segment_info]) / sum([s/r for s, r in self.segment_info])
        return self.weighted_mean_rate

    def initialize(self):
        pass

    def finalization(self):
        pass