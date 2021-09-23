#!/usr/bin/env python3

### DISCLAIMER
# This code is not optimized to make it easy to be understood

from PIL import Image
from cose.messages import CoseMessage
from pylibdmtx import pylibdmtx
from pyzbar import pyzbar
import base45
import cbor2
import datetime
from dateutil import parser
import sys
import zlib

def ORG_to_manufacturer(ORG):
    if ORG == "ORG-100001699":
        return "AstraZeneca AB"
    elif ORG == "ORG-100030215":
        return "Biontech Manufacturing GmbH"
    elif ORG == "ORG-100001417":
        return "Janssen-Cilag International"
    elif ORG == "ORG-100031184":
        return "Moderna Biotech Spain S.L."
    elif ORG == "ORG-100006270":
        return "Curevac AG"
    elif ORG == "ORG-100013793":
        return "CanSino Biologics"
    elif ORG == "ORG-100020693":
        return "China Sinopharm International Corp. - Beijing location"
    elif ORG == "ORG-100010771":
        return "Sinopharm Weiqida Europe Pharmaceutical s.r.o. - Prague location"
    elif ORG == "ORG-100024420":
        return "Sinopharm Zhijun (Shenzhen) Pharmaceutical Co. Ltd. - Shenzhen location"
    elif ORG == "ORG-100032020":
        return "Novavax CZ AS"
    elif ORG == "ORG-100001981":
        return "Serum Institute Of India Private Limited"
    else:
        return ORG.replace('-', ' ')

def vp_to_prophylaxis(vp):
    if vp == "1119349007":
        return "SARS-CoV-2 mRNA vaccine"
    elif vp == "1119305005":
        return "SARS-CoV-2 antigen vaccine"
    elif vp =="J07BX03":
        return "covid-19 vaccines"
    else:
        return "unknown prophylaxis"

def mp_to_vaccine_name(mp):
    if mp == "EU/1/20/1528":
        return "Comirnaty"
    elif mp == "EU/1/20/1507":
        return "Spikevax (previously COVID-19 Vaccine Moderna)"
    elif mp == "EU/1/21/1529":
        return "Vaxzevria"
    elif mp == "EU/1/20/1525":
        return "COVID-19 Vaccine Janssen"
    elif mp == "Inactivated-SARS-CoV-2-Vero-Cell":
        return "Inactivated SARS-CoV-2 (Vero Cell)"
    elif mp == "Covaxin":
        return "Covaxin (also known as BBV152 A, B, C)"
    elif mp == "Covishield":
        return "Covishield (ChAdOx1_nCoV-19)"
    else:
        return mp

def tt_to_type(tt):
    if tt == "LP6464-4":
        return "Nucleic acid amplification with probe detection"
    elif tt == "LP217198-3":
        return "Rapid immunoassay"
    else:
        return "Unknown test type"

def get_2d_doc_element(data, cursor):
    element = ""
    while data[cursor] != 29: #\x1d (Group separator)
        element += chr(data[cursor])
        cursor += 1
    cursor += 1 #Ignoring Group separator
    return element, cursor

img = Image.open(sys.argv[1])
try:
    data = pylibdmtx.decode(img)[0].data

    header_len = 26

    cursor = header_len + 2
    separator = data[header_len:cursor].decode()

    name, cursor = get_2d_doc_element(data, cursor)
    cursor += 2 #Ignoring the separator

    first_name, cursor = get_2d_doc_element(data, cursor)
    cursor += 2 #Ignoring the separator

    birth_date = data[cursor:cursor+8].decode()
    cursor += 8
    cursor += 2 #Ignoring the separator

    target, cursor = get_2d_doc_element(data, cursor)
    cursor += 2 #Ignoring the separator

    molecule, cursor = get_2d_doc_element(data, cursor)
    cursor += 2 #Ignoring the separator

    vaccine_name, cursor = get_2d_doc_element(data, cursor)
    cursor += 2 #Ignoring the separator

    manufacturer, cursor = get_2d_doc_element(data, cursor)
    cursor += 2 #Ignoring the separator

    number_of_doses_received = chr(data[cursor])
    cursor += 1
    cursor += 2 #Ignoring the separator

    number_of_doses_needed = chr(data[cursor])
    cursor += 1
    cursor += 2 #Ignoring the separator

    last_injection_date = data[cursor:cursor+8].decode()
    cursor += 8
    cursor += 2 #Ignoring the separator

    state = data[cursor:cursor+2]
    vaccination_state = "Finished" if state == "TE" else "In progress"

    print("Format: 2D DOC")
    print(f"Name: {name}")
    print(f"First Name: {first_name}")
    print(f"Birth Date: {birth_date[:2]}/{birth_date[2:4]}/{birth_date[4:]}")
    print(f"Covered Disease: {target}")
    print(f"Used Molecule: {molecule}")
    print(f"Vaccine Name: {vaccine_name}")
    print(f"Manufacturer: {manufacturer}")
    print(f"Number of dose(s) received: {number_of_doses_received}")
    print(f"Number of dose(s) needed: {number_of_doses_needed}")
    print(f"Date of the last injection: {last_injection_date[:2]}/{last_injection_date[2:4]}/{last_injection_date[4:]}")
    print(f"State of the vaccination: {vaccination_state}")
except IndexError:
    qr_data = pyzbar.decode(img, symbols=[pyzbar.ZBarSymbol.QRCODE])[0].data.decode('utf-8')
    b45_data = qr_data[4:]
    zlib_data = base45.b45decode(b45_data)
    cose = zlib.decompress(zlib_data)
    decoded_cose = CoseMessage.decode(cose)
    data = cbor2.loads(decoded_cose.payload)

    issuer = data[1]
    QR_code_expiration_date = datetime.datetime.fromtimestamp(data[4]).strftime('%d/%m/%Y %H:%M:%S')
    QR_code_generation_date = datetime.datetime.fromtimestamp(data[6]).strftime('%d/%m/%Y %H:%M:%S')

    data_dict = data[-260][1]

    print("Format: Qr code")
    print(f"Name: {data_dict['nam']['fn']}")
    print(f"First Name: {data_dict['nam']['gn']}")
    print(f"Birth Date: {data_dict['dob']}")
    if 'v' in data_dict:
        print("Nature of the pass: vaccine")
        v_dict = data_dict['v'][0]
        print("Covered Disease: ", end='')
        if v_dict['tg'] == "840539006":
            print("COVID-19")
        else:
            print("unknown disease code")
        print(f"Type of the vaccine or prophylaxis: {vp_to_prophylaxis(v_dict['vp'])}")
        print(f"Vaccine name: {mp_to_vaccine_name(v_dict['mp'])}")
        print(f"Manufacturer: {ORG_to_manufacturer(v_dict['ma'])}")
        print(f"Number of dose(s) received: {v_dict['dn']}")
        print(f"Number of dose(s) needed: {v_dict['sd']}")
        print(f"Date of the last injection: {v_dict['dt']}")
        print(f"Contry in which the vaccine was administred: {v_dict['co']}")
        print(f"Pass issuer: {v_dict['is']}")
        print(f"Unique indentifier of the pass: {v_dict['ci']}") #To study deeper to get more info: https://ec.europa.eu/health/sites/default/files/ehealth/docs/vaccination-proof_interoperability-guidelines_en.pdf
    if 't' in data_dict:
        print("Nature of the pass: test")
        t_dict = data_dict['t'][0]
        print("Tested Disease: ", end='')
        if t_dict['tg'] == "840539006":
            print("COVID-19")
        else:
            print("unknown disease code")
        print(f"Test type: {tt_to_type(t_dict['tt'])}")
        if 'nm' in t_dict:
            print(f"Test name: {t_dict['nm']}")
        if 'ma' in t_dict:
            print(f"Test device identifier: {t_dict['ma']} (Please refer to 'https://covid-19-diagnostics.jrc.ec.europa.eu/devices?manufacturer&text_name&marking&rapid_diag&format&target_type&field-1=HSC%20common%20list%20%28RAT%29&value-1=1&search_method=AND#form_content' for more info)")
        print(f"Date of the test: {parser.parse(t_dict['sc']).strftime('%d/%m/%Y %H:%M:%S')}")
        print(f"Testing center: {t_dict['tc']}")
        print(f"Contry in which the test was performed: {t_dict['co']}")
        print(f"Pass issuer: {t_dict['is']}")
        print(f"Unique indentifier of the pass: {t_dict['ci']}") #To study deeper to get more info: https://ec.europa.eu/health/sites/default/files/ehealth/docs/vaccination-proof_interoperability-guidelines_en.pdf
    if 'r' in data_dict:
        print("Nature of the pass: recovery")
        r_dict = data_dict['r'][0]
        print("Disease: ", end='')
        if r_dict['tg'] == "840539006":
            print("COVID-19")
        else:
            print("unknown disease code")
        print(f"First positive test date: {r_dict['fr']}")
        print(f"Contry in which the test was performed: {r_dict['co']}")
        print(f"Pass issuer: {r_dict['is']}")
        print(f"Pass valid from the: {r_dict['df']}")
        print(f"Pass valid until the: {r_dict['du']}")
        print(f"Unique indentifier of the pass: {r_dict['ci']}") #To study deeper to get more info: https://ec.europa.eu/health/sites/default/files/ehealth/docs/vaccination-proof_interoperability-guidelines_en.pdf
    print(f"Qr code issuer: {issuer}")
    print(f"Generation date of the Qr code: {QR_code_generation_date}")
    print(f"Expiration date of the Qr code: {QR_code_expiration_date}")
    print(f"Schema version: {data_dict['ver']}")
