#!/usr/bin/env python3

import urllib.request
import random
import json
import time
import datetime
import requests
import threading
import ssl
import random
import csv
import uuid
import dns.resolver
import dns.message
import base64
import sys, traceback
import http

UPPER_LIMIT_ON_REQUESTS = 1
NUMBER_OF_WORKERS = 1
NUMBER_OF_REQUESTS_TO_EACH_HOST = 200

CUSTOMER = '<customer id>'
ZONE = 'residential'

PASSWORD = ''
if ZONE == 'static':
    PASSWORD = '<password goes here>'
elif ZONE == 'residential':
    PASSWORD = '<password goes here>'

'''
NOTE: You can't use country or ASN with the 'static' zone -- It has to be
'residential or 'mobile'
'''
ASN = None # String
COUNTRY = ['tm', 'sa', 'ws', 'vg', 'qa', 'td', 'ss', 'pw', 'bz', 'gd', 'bb', 'ag', 'ag', 'mh', 'fk', 'ai', 'st', 'bs', 'vc', 'ir', 'tt', 'sb', 'ki', 'vg', 'bl', 'gw', 'sm', 'mf', 'to', 'li', 'bm', 'tc', 'km', 'ky', 'gy', 'fm', 'mp', 'yt', 'bq', 'lc', 'gg', 'xk', 'dm', 'vu', 'mc', 'gu', 'pr', 'jm', 'nc']
NUMBER_OF_COUNTRIES = len(COUNTRY)
CITY = None
STATE = None

EXPECTED_RESPONSE = b'{"message":"Request received."}\n'
TIMES_TO_SUBTRACT = ['init','auth','dns_resolve','p2p_init','dns','connect']

timeline_details = {}
dns_details = ''
ip_details = ''
last_ten_ips = []

good_requests = 0
bad_requests = 0

counter = 0
counterLock = threading.Lock()

old_f = sys.stdout
class CF:
    def write(self, x):
        if 'CONNECT' in x:
            timeline_details[time.time()] = 'connected'
        if 'x-luminati-timeline' in x:
            timeline_details[time.time()] = x.split(" ")[1][:-2].split(",")
        if 'x-luminati-tun-timeline' in x:
            timeline_details[time.time()] = x.split(" ")[1][:-2].split(",")
        if 'x-luminati-ip' in x:
            global ip_details
            ip_details = x.split(" ")[1][:-2]
        if 'GET /dns-query' in x:
            timeline_details[time.time()] = 'get /resolve'
        if 'CF-RAY'.lower() in x.lower():
            timeline_details[time.time()] = 'reply from google'
        if 'dns:' in x or 'dns_resolve:' in x:
            global dns_details
            dns_details = x
        #old_f.write(x)

class GOOGLE:
    def write(self, x):
        if 'CONNECT' in x:
            timeline_details[time.time()] = 'connected'
        if 'x-luminati-timeline' in x:
            timeline_details[time.time()] = x.split(" ")[1][:-2].split(",")
        if 'x-luminati-tun-timeline' in x:
            timeline_details[time.time()] = x.split(" ")[1][:-2].split(",")
        if 'x-luminati-ip' in x:
            global ip_details
            ip_details = x.split(" ")[1][:-2]
        if 'GET /resolve' in x:
            timeline_details[time.time()] = 'get /resolve'
        if 'strict-transport-security'.lower() in x.lower():
            timeline_details[time.time()] = 'reply from google'
        if 'dns:' in x or 'dns_resolve:' in x:
            global dns_details
            dns_details = x

class QUAD9:
    def write(self, x):
        if 'CONNECT' in x:
            timeline_details[time.time()] = 'connected'
        if 'x-luminati-timeline' in x:
            timeline_details[time.time()] = x.split(" ")[1][:-2].split(",")
        if 'x-luminati-tun-timeline' in x:
            timeline_details[time.time()] = x.split(" ")[1][:-2].split(",")
        if 'x-luminati-ip' in x:
            global ip_details
            ip_details = x.split(" ")[1][:-2]
        if 'GET /dns-query' in x:
            timeline_details[time.time()] = 'get /resolve'
        if 'h2o/dnsdist'.lower() in x.lower():
            timeline_details[time.time()] = 'reply from google'
        if 'dns:' in x or 'dns_resolve:' in x:
            global dns_details
            dns_details = x

class NEXTDNS:
    def write(self, x):
        if 'CONNECT' in x:
            timeline_details[time.time()] = 'connected'
        if 'x-luminati-timeline' in x:
            timeline_details[time.time()] = x.split(" ")[1][:-2].split(",")
        if 'x-luminati-tun-timeline' in x:
            timeline_details[time.time()] = x.split(" ")[1][:-2].split(",")
        if 'x-luminati-ip' in x:
            global ip_details
            ip_details = x.split(" ")[1][:-2]
        if 'GET /8ef2aa' in x:
            timeline_details[time.time()] = 'get /resolve'
        if 'includeSubDomains'.lower() in x.lower():
            timeline_details[time.time()] = 'reply from google'
        if 'dns:' in x or 'dns_resolve:' in x:
            global dns_details
            dns_details = x

# Prevent certificate errors
ssl._create_default_https_context = ssl._create_unverified_context

def get_A_record(domain_name):
    result = dns.resolver.query(domain_name, 'A')
    return result[0].to_text()

def get_times():
    try:
        old_f.write(str(timeline_details)+"\n")
        keys = [*timeline_details]
        keys.sort()

        total_time = (keys[1] - keys[0])*1000
        # print("total time")
        # print(total_time)
        time_spent = 0
        tcp_time1 = 0
        for v in timeline_details[keys[1]]:
            type_of, time_taken = v.split(':')
            time_taken = int(time_taken)
            if type_of in TIMES_TO_SUBTRACT:
                time_spent += time_taken


        for v in timeline_details[keys[2]]:
            type_of, time_taken = v.split(':')
            time_taken = int(time_taken)
            if type_of in TIMES_TO_SUBTRACT:
                time_spent += time_taken
                if type_of == 'connect':
                    tcp_time1 = time_taken

        rtt1 = total_time - time_spent

        total_time = (keys[4]-keys[3])*1000
        time_spent = 0
        dns_to_resolver = 0
        for v in timeline_details[keys[4]]:
            type_of, time_taken = v.split(':')
            time_taken = int(time_taken)
            if type_of in TIMES_TO_SUBTRACT:
                time_spent += time_taken
            if type_of == "dns_resolve":
                dns_to_resolver = time_taken

        tcp_time2 = 0
        for v in timeline_details[keys[5]]:
            type_of, time_taken = v.split(':')
            time_taken = int(time_taken)
            if type_of in TIMES_TO_SUBTRACT:
                time_spent += time_taken
                if type_of == 'connect':
                    tcp_time2 = time_taken
                if type_of == "dns":
                    dns_to_resolver = time_taken


        rtt2 = total_time - time_spent

        rtt = min(rtt1,rtt2)

        doh_time1 = (keys[7] - keys[5])*1000 - 2*rtt1 + tcp_time2 + dns_to_resolver
        doh_time2 = (keys[7] - keys[5])*1000 - 2*rtt2 + tcp_time2 + dns_to_resolver

        timeline_details.pop(keys[3], None)
        timeline_details.pop(keys[4], None)
        timeline_details.pop(keys[5], None)
        timeline_details.pop(keys[6], None)
        timeline_details.pop(keys[7], None)
    except Exception as e:
        old_f.write("Failure:"+ str(e))
        traceback.print_exc(file=old_f)
        return -1,-1,-1,-1,-1,-1,-1

    return rtt1,doh_time1,rtt2,doh_time2,tcp_time1,tcp_time2,dns_to_resolver


def get_dns_times():
    global dns_details
    #old_f.write(dns_details)
    if dns_details != '':
        spl = dns_details.split(',')
        for j in spl:
            if 'dns' in j:
                val = int(j.split(':')[1])
                #old_f.write("val: " + str(val))
                return val
    return 0

def check_last_ten_ips(num, ip):
    global last_ten_ips
    if num < 10:
        last_ten_ips.append(ip)
    else:
        if len(set(last_ten_ips)) == 1:
            return True
        last_ten_ips.pop(0)
        last_ten_ips.append(ip)
    return False

def send_request(worker_id):
    global good_requests
    global bad_requests
    global timeline_details
    global dns_details
    global ip_details
    global last_ten_ips

    #print('Worker %d, good_requests: %d' % (worker_id, good_requests))

    if worker_id >= NUMBER_OF_COUNTRIES:
        return

    as_string = ''
    if ASN is not None:
        as_string = '-asn-' + ASN

    country_string = ''
    if COUNTRY is not None:
        country_string = '-country-' + COUNTRY[worker_id]

    city_string = ''
    if CITY is not None:
        city_string = '-city-' + CITY

    state_string = ''
    if STATE is not None:
        state_string = '-state-' + STATE

    # Ensures a different client every time
    # Also ensures our parameters do not end in a dash ( '-' )

    lum_IP = get_A_record('zproxy.lum-superproxy.io')
    last_ten_ips = []


    for i in range(NUMBER_OF_REQUESTS_TO_EACH_HOST):
        session_string = '-session-glob_' + str(random.randint(1,9999999999))

        proxy_string = 'lum-customer-' + CUSTOMER + '-zone-' + ZONE + '-dns-remote-route_err-block' + as_string + country_string + state_string + city_string + session_string + ':' + PASSWORD + '@'+ lum_IP +':22225'

        print(proxy_string)

        opener_resolver = urllib.request.build_opener(
        urllib.request.ProxyHandler(
        {'http': 'http://' + proxy_string,
        'https': 'https://' + proxy_string}),urllib.request.HTTPSHandler(debuglevel=1),urllib.request.HTTPHandler(debuglevel=1))

        resolver_URL = 'https://lumtest.com/myip.json'

        try:

            req_resolver = urllib.request.Request(resolver_URL)
            resp = opener_resolver.open(req_resolver)
            text_resolver = resp.read()
            opener_resolver.close()

        except Exception as e:
            print("Failure:", e)
            traceback.print_exc(file=sys.stdout)


        sys.stdout = CF()

        resolver_URL = 'https://lumtest.com/myip.json'

        try:

            req_resolver = urllib.request.Request(resolver_URL)
            resp = opener_resolver.open(req_resolver)
            text_resolver = resp.read()
            opener_resolver.close()

        except Exception as e:
            sys.stdout = old_f
            print("Failure:", e)
            traceback.print_exc(file=sys.stdout)
            dns_details = ''
            timeline_details = {}
            continue



        unique_id_resolver_cf = str(uuid.uuid4()) + '-doh-testing.'
        domain = unique_id_resolver_cf+'deepdns.report'
        resolver_URL = 'https://cloudflare-dns.com/dns-query?name='+domain+'&type=A'
        #print(resolver_URL)

        try:

            req_resolver = urllib.request.Request(resolver_URL)
            req_resolver.add_header('accept', 'application/dns-json')
            #req_resolver.add_header('Host','dns.google')


            resp = opener_resolver.open(req_resolver)
            text_resolver = resp.read()

            opener_resolver.close()


        except Exception as e:
            sys.stdout = old_f
            print("Failure:", e)
            traceback.print_exc(file=sys.stdout)
            dns_details = ''
            timeline_details = {}
            continue

        # time.sleep(1000)

        rtt1,cf_doh_time1,cf_rtt2,cf_doh_time2,tcp_time1,cf_tcp_time2,dns_to_cf = get_times()

        sys.stdout = GOOGLE()

        unique_id_resolver_g = str(uuid.uuid4()) + '-doh-testing.'
        domain = unique_id_resolver_g+'deepdns.report'
        resolver_URL = 'https://dns.google/resolve?name='+domain+'&type=A'
        #print(resolver_URL)

        try:

            req_resolver = urllib.request.Request(resolver_URL)
            req_resolver.add_header('accept', 'application/dns-json')
            #req_resolver.add_header('Host','dns.google')


            resp = opener_resolver.open(req_resolver)
            text_resolver = resp.read()

            opener_resolver.close()


        except Exception as e:
            sys.stdout = old_f
            print("Failure:", e)
            traceback.print_exc(file=sys.stdout)
            dns_details = ''
            timeline_details = {}
            continue

        # time.sleep(1000)

        rtt1,g_doh_time1,g_rtt2,g_doh_time2,tcp_time1,g_tcp_time2,dns_to_g = get_times()

        sys.stdout = NEXTDNS()

        unique_id_resolver_n = str(uuid.uuid4()) + '-doh-testing.'
        domain = unique_id_resolver_n+'deepdns.report'
        resolver_URL = 'https://dns.nextdns.io/8ef2aa?name='+domain+'&type=A'
        #print(resolver_URL)

        try:

            req_resolver = urllib.request.Request(resolver_URL)
            req_resolver.add_header('accept', 'application/dns-json')
            #req_resolver.add_header('Host','dns.google')


            resp = opener_resolver.open(req_resolver)
            text_resolver = resp.read()

            opener_resolver.close()


        except Exception as e:
            sys.stdout = old_f
            print("Failure:", e)
            traceback.print_exc(file=sys.stdout)
            dns_details = ''
            timeline_details = {}
            continue

        # time.sleep(1000)

        rtt1,n_doh_time1,n_rtt2,n_doh_time2,tcp_time1,n_tcp_time2,dns_to_n = get_times()

        sys.stdout = QUAD9()

        unique_id_resolver_q = str(uuid.uuid4()) + '-doh-testing.'
        domain = unique_id_resolver_q+'deepdns.report'
        request = dns.message.make_query(domain, dns.rdatatype.A)
        wireformat = base64.b64encode(request.to_wire())
        b64decoded = wireformat.decode('ascii')
        resolver_URL = 'https://dns.quad9.net/dns-query?dns='+b64decoded
        #print(resolver_URL)

        try:

            req_resolver = urllib.request.Request(resolver_URL)
            req_resolver.add_header('accept', 'application/dns-message')
            #req_resolver.add_header('Host','dns.google')


            resp = opener_resolver.open(req_resolver)
            text_resolver = resp.read()

            opener_resolver.close()


        except Exception as e:
            sys.stdout = old_f
            print("Failure:", e)
            traceback.print_exc(file=sys.stdout)
            dns_details = ''
            timeline_details = {}
            continue


        rtt1,q_doh_time1,q_rtt2,q_doh_time2,tcp_time1,q_tcp_time2,dns_to_q = get_times()


        dns_details = ''

        if rtt1 >= 0:

            unique_id_server = str(uuid.uuid4()) + '-doh-testing.'
            server_URL = '<your webserver where you log requests>'


            try:
                req = urllib.request.Request(server_URL)


                resp = opener_resolver.open(req)
                text_server = resp.read()

                opener_resolver.close()


            except Exception as e:
                print("Failure:", e)
                traceback.print_exc(file=sys.stdout)

            dns_time = get_dns_times()
            sys.stdout = old_f
            print(COUNTRY[worker_id], ip_details, rtt1, tcp_time1, unique_id_resolver_cf,cf_doh_time1,cf_rtt2,cf_doh_time2,cf_tcp_time2,dns_to_cf, unique_id_resolver_g,g_doh_time1,g_rtt2,g_doh_time2,g_tcp_time2,dns_to_g, unique_id_resolver_n,n_doh_time1,n_rtt2,n_doh_time2,n_tcp_time2,dns_to_n, unique_id_resolver_q,q_doh_time1,q_rtt2,q_doh_time2,q_tcp_time2,dns_to_q, unique_id_server,dns_time)


        sys.stdout = old_f
        if check_last_ten_ips(i, ip_details):
            return
        timeline_details = {}
        ip_details = ''



def worker(from_country, to_country):
    global counter
    global counterLock

    for i in range(int(from_country), int(to_country)):
        result = send_request(i)


def main():
    global good_requests
    global bad_requests



    threads = []
    for i in range(NUMBER_OF_WORKERS):
        t = threading.Thread(target=worker, args=(sys.argv[1],sys.argv[2],))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()


    print(timeline_details)


if __name__ == '__main__':
    main()