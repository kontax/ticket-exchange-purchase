import json
import requests
from pyquery import PyQuery
from random import randint
from time import sleep



event_id = '6474' # Bayern
#event_id = '6477' # Leicester
form_url = 'https://www.eticketing.co.uk/arsenal/Authentication/Login/Process'
event_url = 'https://www.eticketing.co.uk/arsenal/details/event.aspx?itemref=' + event_id

proxies={
    'http': 'http://127.0.0.1:8080',
    'https': 'https://127.0.0.1:8080'
}

payload = {
    'returnUrl': '/arsenal/',
    'Type': 'ClientRefPasswordCredentials',
    'PrimaryCredential': '2300127',
    'SecondaryCredential': 'arsenal'
}




# Login
s = requests.Session()
login = s.post(form_url, data=payload, proxies=proxies, verify=False)
event_response = s.get(event_url)
event_page = PyQuery(event_response.text)

while event_page("title").text() == 'Please Wait - eTickets':
    print("In the queue...")
    sleep(10)
    event_response = s.get(event_url)
    event_page = PyQuery(event_response.text)

view_state = event_page("#__VIEWSTATE").attr("value")
post_url = 'https://www.eticketing.co.uk/arsenal/details/event.aspx?itemref={event_id}&anthem_callback=true'.format(event_id=event_id)




# Select the ticket exchange part

post_data = {
    'Anthem_UpdatePage': 'true',
    '__EVENTTARGET': 'ctl00$body$seatselection1$selectionmodes1$repeaterModes$ctl02$ctl02',
    '__EVENTARGUMENT': '',
    '__VIEWSTATE': view_state,
    '__VIEWSTATEGENERATOR': 'B7FC5CAC'
}

r = s.post(post_url, data=post_data, proxies=proxies, verify=False)
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

r = s.post(post_url, data=post_data, proxies=proxies, verify=False)
ticket_response = json.loads(r.text)
view_state = ticket_response['viewState']
response_html = PyQuery(ticket_response['controls']['ctl00$body$seatselection1$bestavailable1$panelflip'])
price_class = response_html('#ctl00_body_seatselection1_bestavailable1_repeaterPriceClassesTX_ctl00_hiddenPriceClassTX').attr('value')



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

r = s.post(post_url, data=post_data, proxies=proxies, verify=False)
ticket_response = json.loads(r.text)
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
    
    r = s.post(post_url, data=post_data, proxies=proxies, verify=False)
    ticket_response = json.loads(r.text)
    view_state = ticket_response['viewState']
    
    message = PyQuery(ticket_response['controls']['ctl00$body$seatselection1$bestavailable1$avs1'])
    print(message)
    
    resp_msg = message('ul#errorsummary').children('li')[0].text
    sleep(randint(1,3))

