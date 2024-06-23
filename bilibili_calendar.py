from bs4 import BeautifulSoup

def transform_bilibili_calendar(data):
    soup = BeautifulSoup(data, 'html.parser')
    event_cache = soup.find_all('div', {'class': 'calendar-line'})
    event_list = []

    for event in event_cache:
        # data-info: 活动(剧情), 庆典(加倍), 卡池, 团队战
        start_time = event.find('span', {'class': 'eventTimer'})['data-start']
        end_time = event.find('span', {'class': 'eventTimer'})['data-end']
        # JAG: type id of the events
        data_info = event.find('span', {'class': 'eventTimer'})['data-info']
        if data_info == '庆典':
            type_id = 2
        elif data_info == '团队战':
            type_id = 3
        else:
            type_id = 1
        # If the event is a 卡池
        for span in event.find_all('span'):
            if span.span:
                span.span.extract()
        # Extract the inner div and find title
        event.div.extract()
        campaign_name = event.text
        if '国服运营中' in title: continue
        # Add the event to the list
        event_list.append({
            'campaign_name': campaign_name, 'start_time': start_time,
            'end_time': end, 'type': type_id})

    return event_list
