import json
import requests
import sys
from pyquery import PyQuery
from random import randint
from selenium import webdriver
from time import sleep

event_id = '6474'  # Bayern
# event_id = '6477' # Leicester
ticket_quantity = '2'
min_price = '0.00'
max_price = '101.50'

form_url = 'https://www.eticketing.co.uk/arsenal/Authentication/Login/Process'
event_url = 'https://www.eticketing.co.uk/arsenal/details/event.aspx?itemref=' + event_id

proxies = {
    'http': 'http://127.0.0.1:8080',
    'https': 'https://127.0.0.1:8080'
}

payload = {
    'returnUrl': '/arsenal/',
    'Type': 'ClientRefPasswordCredentials',
    'PrimaryCredential': '2304955',
    'SecondaryCredential': '590kTv&LY#Lz'
}


# Functions

def is_ticket_found(ticket_response):
    return 'script' in ticket_response \
           and ticket_response['script'][0] == "try{window.location='/arsenal/basket.aspx';}catch(e){}"


def get_cookies(session):
    return requests.utils.dict_from_cookiejar(session.cookies)


def convert_cookies(cookies):
    fixed_cookies = []
    for cookie in cookies.keys():
        tmp = {}
        tmp['name'] = cookie
        tmp['value'] = cookies[cookie]
        fixed_cookies.append(tmp)
    return fixed_cookies


def open_browser(fixed_cookies):
    driver = webdriver.Firefox()
    driver.get("https://www.eticketing.co.uk")
    for cookie in fixed_cookies:
        driver.add_cookie(cookie)
    driver.get("https://www.eticketing.co.uk/arsenal/basket.aspx")


# Login
s = requests.Session()
login = s.post(form_url, data=payload)
event_response = s.get(event_url)
event_page = PyQuery(event_response.text)

while event_page("title").text() == 'Please Wait - eTickets':
    print("In the queue...")
    sleep(10)
    event_response = s.get(event_url)
    event_page = PyQuery(event_response.text)

view_state = event_page("#__VIEWSTATE").attr("value")
post_url = 'https://www.eticketing.co.uk/arsenal/details/event.aspx?itemref={event_id}&anthem_callback=true'.format(
    event_id=event_id)

# Select the ticket exchange part

post_data = {
    'Anthem_UpdatePage': 'true',
    '__EVENTTARGET': 'ctl00$body$seatselection1$selectionmodes1$repeaterModes$ctl02$ctl02',
    '__EVENTARGUMENT': '',
    '__VIEWSTATE': view_state,
    '__VIEWSTATEGENERATOR': 'B7FC5CAC'
}

r = s.post(post_url, data=post_data)
ticket_response = json.loads(r.text)
view_state = ticket_response['viewState']

# Select the Ticket Exchange best available


post_data = {
    'Anthem_UpdatePage': 'true',
    '__EVENTTARGET': 'ctl00$body$seatselection1$bestavailable1$fliptoback',
    '__EVENTARGUMENT': '',
    '__VIEWSTATE': view_state,
    '__VIEWSTATEGENERATOR': 'B7FC5CAC'
}

r = s.post(post_url, data=post_data)
ticket_response = json.loads(r.text)
view_state = ticket_response['viewState']
response_html = PyQuery(ticket_response['controls']['ctl00$body$seatselection1$bestavailable1$panelflip'])
price_class = response_html(
    '#ctl00_body_seatselection1_bestavailable1_repeaterPriceClassesTX_ctl00_hiddenPriceClassTX').attr('value')

# Request a ticket


post_data = {
    'Anthem_UpdatePage': 'true',
    '__EVENTTARGET': 'ctl00$body$seatselection1$bestavailable1$cmdAddToBasketTX',
    '__EVENTARGUMENT': '',
    '__VIEWSTATE': view_state,
    '__VIEWSTATEGENERATOR': 'B7FC5CAC',
    'ctl00$body$seatselection1$bestavailable1$repeaterPriceClassesTX$ctl00$hiddenPriceClassTX': price_class,
    'ctl00$body$seatselection1$bestavailable1$repeaterPriceClassesTX$ctl00$listQtyTX': ticket_quantity,
    'ctl00$body$seatselection1$bestavailable1$repeaterPriceClassesTX$ctl00$minprice': min_price,
    'ctl00$body$seatselection1$bestavailable1$repeaterPriceClassesTX$ctl00$maxprice': max_price
}

r = s.post(post_url, data=post_data)
ticket_response = json.loads(r.text)

if is_ticket_found(ticket_response):
    print("TICKET FOUND! LOG ON AND USE THESE COOKIE VALUES:")
    cookies = get_cookies(s)
    print(cookies)
    open_browser(convert_cookies(cookies))
    sys.exit()

view_state = ticket_response['viewState']

# Get the response
message = PyQuery(ticket_response['controls']['ctl00$body$seatselection1$bestavailable1$avs1'])
print(message)

resp_msg = message('ul#errorsummary').children('li')[0].text
error_msg = 'None of the prices you selected could be found. Please try back later.'

i = 0

while error_msg == resp_msg:
    post_data = {
        'Anthem_UpdatePage': 'true',
        '__EVENTTARGET': 'ctl00$body$seatselection1$bestavailable1$cmdAddToBasketTX',
        '__EVENTARGUMENT': '',
        '__VIEWSTATE': view_state,
        '__VIEWSTATEGENERATOR': 'B7FC5CAC',
        'ctl00$body$seatselection1$bestavailable1$repeaterPriceClassesTX$ctl00$hiddenPriceClassTX': price_class,
        'ctl00$body$seatselection1$bestavailable1$repeaterPriceClassesTX$ctl00$listQtyTX': ticket_quantity,
        'ctl00$body$seatselection1$bestavailable1$repeaterPriceClassesTX$ctl00$minprice': min_price,
        'ctl00$body$seatselection1$bestavailable1$repeaterPriceClassesTX$ctl00$maxprice': max_price
    }

    # Try 2 tickets first

    r = s.post(post_url, data=post_data)
    ticket_response = json.loads(r.text)

    if is_ticket_found(ticket_response):
        print("2 TICKETS FOUND! LOG ON AND USE THESE COOKIE VALUES:")
        cookies = get_cookies(s)
        print(cookies)
        open_browser(convert_cookies(cookies))
        sys.exit()

    try:
        view_state = ticket_response['viewState']
    except:
        print(ticket_response)
        # sys.exit()

    message = PyQuery(ticket_response['controls']['ctl00$body$seatselection1$bestavailable1$avs1'])
    print(message)

    resp_msg = message('ul#errorsummary').children('li')[0].text
    sleep(randint(6, 10))

    # If that doesn't work then try looking for 1

    post_data['ctl00$body$seatselection1$bestavailable1$repeaterPriceClassesTX$ctl00$listQtyTX'] = '1'

    r = s.post(post_url, data=post_data)
    ticket_response = json.loads(r.text)

    if is_ticket_found(ticket_response):
        print("TICKET FOUND! LOG ON AND USE THESE COOKIE VALUES:")
        cookies = get_cookies(s)
        print(cookies)
        open_browser(convert_cookies(cookies))
        sys.exit()

    i += 1
    print('Attempt ' + str(i))

    try:
        view_state = ticket_response['viewState']
    except:
        print(ticket_response)
        # sys.exit()

    message = PyQuery(ticket_response['controls']['ctl00$body$seatselection1$bestavailable1$avs1'])
    print(message)

    resp_msg = message('ul#errorsummary').children('li')[0].text
    sleep(randint(6, 10))


