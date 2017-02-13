import json
import requests
from pyquery import PyQuery
from time import sleep

#event_id = '6474' # Bayern
event_id = '6462' # Hull
form_url = 'https://www.eticketing.co.uk/arsenal/Authentication/Login/Process'
event_url = 'https://www.eticketing.co.uk/arsenal/details/event.aspx?itemref=' + event_id

payload = {
    'returnUrl': '/arsenal/',
    'Type': 'ClientRefPasswordCredentials',
    'PrimaryCredential': '2300127',
    'SecondaryCredential': 'arsenal'
}

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
post_url = 'https://www.eticketing.co.uk/arsenal/details/event.aspx?itemref={event_id}&anthem_callback=true'.format(event_id=event_id)



# Select the best available tab

headers = {
    'Host': 'www.eticketing.co.uk',
    'Connection': 'keep-alive',
    'Origin': 'https://www.eticketing.co.uk',
    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'Accept': '*/*',
    'Referer': event_url
}

post_data = {
    'Anthem_UpdatePage': 'true',
    '__EVENTTARGET': 'ctl00$body$seatselection1$selectionmodes1$repeaterModes$ctl02$ctl02',
    '__EVENTARGUMENT': '',
    '__VIEWSTATE': view_state,
    '__VIEWSTATEGENERATOR': 'B7FC5CAC'
}

r = s.post(post_url, data=post_data, headers=headers)
ticket_response = json.loads(r.text)
post_data['view_state'] = ticket_response['viewState']
#s.cookies.set('_gali','ctl00_body_seatselection1_selectionmodes1_repeaterModes_ctl02_ctl02')


# Select the Ticket Exchange best available
post_data['__EVENTTARGET'] = 'ctl00$body$seatselection1$bestavailable1$fliptoback'

#post_data = {
#    'Anthem_UpdatePage': 'true',
#    '__EVENTTARGET': 'ctl00$body$seatselection1$bestavailable1$fliptoback',
#    '__EVENTARGUMENT': '',
#    #'__VIEWSTATE': view_state,
#    '__VIEWSTATEGENERATOR': 'B7FC5CAC'
#}

r = s.post(post_url, data=post_data, headers=headers)
ticket_response = json.loads(r.text)
print(ticket_response['controls'].keys())
print(ticket_response)
post_data['view_state'] = ticket_response['viewState']
response_html = PyQuery(ticket_response['controls']['ctl00$body$seatselection1$bestavailable1$panelflip'])
price_class = response_html('#ctl00_body_seatselection1_bestavailable1_repeaterPriceClassesTX_ctl00_hiddenPriceClassTX').attr('value')

post_data = {
    'Anthem_UpdatePage': 'true',
    '__EVENTTARGET': 'ctl00%24body%24seatselection1%24bestavailable1%24cmdAddToBasketTX',
    '__EVENTARGUMENT': '',
    '__VIEWSTATE': view_state,
    '__VIEWSTATEGENERATOR': 'B7FC5CAC',
    'ctl00$body$seatselection1$bestavailable1$repeaterPriceClassesTX$ctl00$hiddenPriceClassTX': price_class,
    'ctl00$body$seatselection1$bestavailable1$repeaterPriceClassesTX$ctl00$listQtyTX': '1',
    'ctl00$body$seatselection1$bestavailable1$repeaterPriceClassesTX$ctl00$minprice': '26.00',
    'ctl00$body$seatselection1$bestavailable1$repeaterPriceClassesTX$ctl00$maxprice': '162.50'
}

r = s.post(post_url, data=post_data)
ticket_response = json.loads(r.text)

# Reset the view state
post_data['view_state'] = ticket_response['viewState']

# Get the response
message = PyQuery(ticket_response['controls']['ctl00$body$seatselection1$isc1$panelSeatSelection'])
print(r.text)

