import json
import requests
import sys
from pyquery import PyQuery
from random import randint
from selenium import webdriver
from time import sleep

# EVENT_ID = '6474' # Bayern
EVENT_ID = '6477'  # Leicester


root_url = 'https://www.eticketing.co.uk/arsenal/'
login_url = root_url + 'Authentication/Login/Process'
event_url = root_url + 'details/event.aspx?itemref={event_id}'.format(event_id=EVENT_ID)
event_post_url = event_url + '&anthem_callback=true'

debug_proxies = {
    'http': 'http://127.0.0.1:8080',
    'https': 'https://127.0.0.1:8080'
}

login_payload = {
    'returnUrl': '/arsenal/',
    'Type': 'ClientRefPasswordCredentials',
    'PrimaryCredential': '2300127',
    'SecondaryCredential': 'arsenal'
}

post_payload = {
    'Anthem_UpdatePage': 'true',
    '__EVENTTARGET': '',
    '__EVENTARGUMENT': '',
    '__VIEWSTATE': '',
    '__VIEWSTATEGENERATOR': 'B7FC5CAC'
}


# FUNCTIONS

def login(url, ev_url, session, payload, proxies=None):
    """
    Login to the specified URL, using the username/password provided and any debug proxies
    specified if required.
    :param ev_url: The URL of the event to load the details from
    :param url: The URL to post the login payload to
    :param session: The requests session to send the data with
    :param payload: The login payload, containing the username/password
    :param proxies: Any proxies to use for debugging purposes
    :return: The ViewState of the request
    """

    # Login using the data supplied, depending on whether to debug or not
    if proxies:
        session.post(url, data=payload, proxies=proxies, verify=False)
    else:
        session.post(url, data=payload)

    # Get the response from the server
    event_response = s.get(ev_url)
    event_page = PyQuery(event_response.text)

    # Occasionally the servers will be busy. Here we wait until the response for the event page
    # confirms that we are no longer waiting in the queue
    while event_page("title").text() == 'Please Wait - eTickets':
        print("In the queue...")
        sleep(10)
        event_response = s.get(event_url)
        event_page = PyQuery(event_response.text)

    # Once we have got the correct response we send back the ViewState
    return event_page("#__VIEWSTATE").attr("value")


def page_request(url, data_payload, session, proxies=None):
    """
    Sends a post request and returns the view state from the request if applicable.
    :param url: The URL to send the request to
    :param data_payload: the JSON payload to send to the URL
    :param session: The requests session used to send the request
    :param proxies: Any debug proxies that are being used
    :return: The ViewState of the request, or None if not applicable
    """

    # Send the request payload
    if proxies:
        resp = session.post(url, data=data_payload, proxies=proxies, verify=False)
    else:
        resp = session.post(url, data=data_payload)

    # Return the JSON values
    return json.loads(resp.text)


def is_ticket_found(response):
    """
    Checks the requests response to see if a ticket has been added to the cart
    :param response: The response from the requests call
    :return: True if a ticket has been added, false otherwise
    """
    return 'script' in response \
           and response['script'][0] == "try{window.location='/arsenal/basket.aspx';}catch(e){}"


def get_cookies(session):
    """
    Prints the cookie details of the session. These should be pasted into the browser cookie editor
    and the browser refreshed in order for the cart to be updated.
    :param session: The requests session containing the cookies to print
    :return: A dictionary of the cookie values
    """
    return requests.utils.dict_from_cookiejar(session.cookies)


def format_cookies(requests_cookies):
    """
    Formats cookies from the Requests module to be available to use in selenium
    :param requests_cookies: The cookies t
    :return:
    """
    formatted_cookies = []
    for cookie in requests_cookies.keys():
        formatted_cookies.append({'name': cookie, 'value': cookies[cookie]})
    return formatted_cookies


def open_basket(cookie_dict):
    """
    Opens the arsenal shopping basket in firefox with the correct cookies set
    :param cookie_dict: The cookies in the format {name: key, value: value} for each cookie
    """
    driver = webdriver.Firefox()
    driver.get("https://www.eticketing.co.uk/arsenal")
    for cookie in cookie_dict:
        driver.add_cookie(cookie)
    driver.get("https://www.eticketing.co.uk/arsenal/basket.aspx")


# Login
s = requests.Session()
response = login(login_url, event_url, s, login_payload, debug_proxies)
view_state = response['viewState']

# Select the ticket exchange part

post_payload['__EVENTTARGET'] = 'ctl00$body$seatselection1$selectionmodes1$repeaterModes$ctl02$ctl02'
post_payload['__VIEWSTATE'] = view_state

view_state = page_request(event_post_url, post_payload, s, debug_proxies)

# Select the Ticket Exchange best available

post_payload['__EVENTTARGET'] = 'ctl00$body$seatselection1$bestavailable1$fliptoback'
post_payload['__VIEWSTATE'] = view_state

view_state = page_request(event_post_url, post_payload, s, debug_proxies)


post_data = {
    'Anthem_UpdatePage': 'true',
    '__EVENTTARGET': 'ctl00$body$seatselection1$bestavailable1$fliptoback',
    '__EVENTARGUMENT': '',
    '__VIEWSTATE': view_state,
    '__VIEWSTATEGENERATOR': 'B7FC5CAC'
}

r = s.post(event_post_url, data=post_data, proxies=debug_proxies, verify=False)
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
    'ctl00$body$seatselection1$bestavailable1$repeaterPriceClassesTX$ctl00$listQtyTX': '1',
    'ctl00$body$seatselection1$bestavailable1$repeaterPriceClassesTX$ctl00$minprice': '0.00',
    'ctl00$body$seatselection1$bestavailable1$repeaterPriceClassesTX$ctl00$maxprice': '101.50'
}

r = s.post(event_post_url, data=post_data, proxies=debug_proxies, verify=False)
ticket_response = json.loads(r.text)

if is_ticket_found(ticket_response):
    print("TICKET FOUND! LOG ON AND USE THESE COOKIE VALUES:")
    cookies = get_cookies(s)
    print(cookies)
    open_basket(cookies)
    sys.exit()
    # return

view_state = ticket_response['viewState']

# Get the response
message = PyQuery(ticket_response['controls']['ctl00$body$seatselection1$bestavailable1$avs1'])
print(message)

resp_msg = message('ul#errorsummary').children('li')[0].text
error_msg = 'None of the prices you selected could be found. Please try back later.'

while error_msg == resp_msg:
    post_data = {
        'Anthem_UpdatePage': 'true',
        '__EVENTTARGET': 'ctl00$body$seatselection1$bestavailable1$cmdAddToBasketTX',
        '__EVENTARGUMENT': '',
        '__VIEWSTATE': view_state,
        '__VIEWSTATEGENERATOR': 'B7FC5CAC',
        'ctl00$body$seatselection1$bestavailable1$repeaterPriceClassesTX$ctl00$hiddenPriceClassTX': price_class,
        'ctl00$body$seatselection1$bestavailable1$repeaterPriceClassesTX$ctl00$listQtyTX': '1',
        'ctl00$body$seatselection1$bestavailable1$repeaterPriceClassesTX$ctl00$minprice': '0.00',
        'ctl00$body$seatselection1$bestavailable1$repeaterPriceClassesTX$ctl00$maxprice': '101.50'
    }

    r = s.post(event_post_url, data=post_data, proxies=debug_proxies, verify=False)
    ticket_response = json.loads(r.text)

    if is_ticket_found(ticket_response):
        print("TICKET FOUND! LOG ON AND USE THESE COOKIE VALUES:")
        cookies = get_cookies(s)
        print(cookies)
        open_basket(cookies)
        sys.exit()

    view_state = ticket_response['viewState']

    message = PyQuery(ticket_response['controls']['ctl00$body$seatselection1$bestavailable1$avs1'])
    print(message)

    resp_msg = message('ul#errorsummary').children('li')[0].text
    sleep(randint(1, 3))

