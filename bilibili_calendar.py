from bs4 import BeautifulSoup

def transform_bilibili_calendar(data):
    soup = BeautifulSoup(data, 'html.parser')
    event_cache = soup.find_all('div', {'class': 'calendar-line'})
    event_list = []

    for event in event_cache:
        # data-info: 活动(剧情), 庆典(加倍), 卡池
        #data-info = event.find('span', {'class': 'eventTimer'})['data-info']
        start = event.find('span', {'class': 'eventTimer'})['data-start']
        end = event.find('span', {'class': 'eventTimer'})['data-end']
        # If the event is a 卡池
        if event.span.span:
            event.span.span.extract()
        # Extract the inner div and find title
        event.div.extract()
        title = event.text
        if '国服运营中' in title: continue
        # Add the event to the list
        event_list.append({'title': title, 'start': start, 'end': end})

    return event_list
