import json
import requests
import sys
from pyquery import PyQuery
from random import randint
from selenium import webdriver
from time import sleep

# EVENT_ID = '6474' # Bayern
EVENT_ID = '6477'  # Leicester
TICKET_QUANTITY = '1'
MIN_PRICE = '0.00'
MAX_PRICE = '101.50'


# URLS
root_url = 'https://www.eticketing.co.uk/arsenal/'
basket_url = root_url + "/basket.aspx"
login_url = root_url + 'Authentication/Login/Process'
event_url = root_url + 'details/event.aspx?itemref={event_id}'.format(event_id=EVENT_ID)
event_post_url = event_url + '&anthem_callback=true'

# JSON KEYS

select_ticket_exchange_json = 'ctl00$body$seatselection1$selectionmodes1$repeaterModes$ctl02$ctl02'
ticket_exchange_best_avl_json = 'ctl00$body$seatselection1$bestavailable1$fliptoback'
ticket_exchange_response_json = 'ctl00$body$seatselection1$bestavailable1$panelflip'
ticket_purchase_response_json = 'ctl00$body$seatselection1$bestavailable1$avs1'
ticket_request_json = 'ctl00$body$seatselection1$bestavailable1$repeaterPriceClassesTX$ctl00$'
price_class_html_id = '#ctl00_body_seatselection1_bestavailable1_repeaterPriceClassesTX_ctl00_hiddenPriceClassTX'
price_class_json = ticket_request_json + 'hiddenPriceClassTX'
ticket_quantity_json = ticket_request_json + 'listQtyTX'
min_price_json = ticket_request_json + 'minprice'
max_price_json = ticket_request_json + 'maxprice'

# PAYLOADS

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
    event_response = session.get(ev_url)
    event_page = PyQuery(event_response.text)

    # Occasionally the servers will be busy. Here we wait until the response for the event page
    # confirms that we are no longer waiting in the queue
    while event_page("title").text() == 'Please Wait - eTickets':
        print("In the queue...")
        sleep(10)
        event_response = session.get(event_url)
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


def format_cookies(cookies):
    """
    Formats cookies from the Requests module to be available to use in selenium
    :param cookies: The cookies t
    :return:
    """
    formatted_cookies = []
    for cookie in cookies.keys():
        formatted_cookies.append({'name': cookie, 'value': cookies[cookie]})
    return formatted_cookies


def open_basket(cookies):
    """
    Opens the arsenal shopping basket in firefox with the correct cookies set
    :param cookies: The cookies in the format {name: key, value: value} for each cookie
    """
    driver = webdriver.Chrome()
    driver.get(root_url)
    for cookie in cookies:
        driver.add_cookie(cookie)
    driver.get(basket_url)


def update_payload_event(payload, target, view_state):
    """
    Updates the request payload dictionary with new Event Target values.
    :param payload: The request payload with the original values
    :param target: The new EventTarget to change the payload to
    :param view_state: The updated ViewState of the request
    """
    payload['__EVENTTARGET'] = target
    payload['__VIEWSTATE'] = view_state


def main():
    # Login
    s = requests.Session()
    response = login(login_url, event_url, s, login_payload, debug_proxies)
    view_state = response['viewState']

    # Select the ticket exchange part

    update_payload_event(post_payload, select_ticket_exchange_json, view_state)
    response = page_request(event_post_url, post_payload, s, debug_proxies)
    view_state = response['viewState']

    # Select the Ticket Exchange best available

    update_payload_event(post_payload, ticket_exchange_best_avl_json, view_state)
    response = page_request(event_post_url, post_payload, s, debug_proxies)
    view_state = response['viewState']

    # Get the price class from the response HTML

    response_html = PyQuery(response['controls'][ticket_exchange_response_json])
    price_class = response_html(price_class_html_id).attr('value')

    # Request a ticket
    i = 1
    print("Attempt " + str(i))

    update_payload_event(post_payload, ticket_exchange_best_avl_json, view_state)
    post_payload[price_class_json] = price_class
    post_payload[ticket_request_json] = TICKET_QUANTITY
    post_payload[min_price_json] = MIN_PRICE
    post_payload[max_price_json] = MAX_PRICE

    response = page_request(event_post_url, post_payload, s, debug_proxies)

    # Keep trying till we get a ticket
    while not is_ticket_found(response):
        sleep(randint(6, 10))
        print("Attempt " + str(i))
        i += 1

        # Print the error message
        message = PyQuery(response['controls'][ticket_purchase_response_json])
        resp_msg = message('ul#errorsummary').children('li')[0].text
        print(resp_msg)

        view_state = response['viewState']
        update_payload_event(post_payload, ticket_exchange_best_avl_json, view_state)

    print("TICKET FOUND! LOG ON AND USE THESE COOKIE VALUES:")
    cookies = get_cookies(s)
    print(cookies)
    open_basket(cookies)

if __name__ == '__main__':
    main()
