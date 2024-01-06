import os
import json
import datetime
import aiohttp
import asyncio
import math
from .bilibili_calendar import transform_bilibili_calendar
from .gamewith_calendar import transform_gamewith_calendar

# type 0普通 1 活动 2双倍 3 公会战

event_data = {
    'cn': [],
    'tw': [],
    'jp': [],
}

event_updated = {
    'cn': '',
    'tw': '',
    'jp': '',
}

lock = {
    'cn': asyncio.Lock(),
    'tw': asyncio.Lock(),
    'jp': asyncio.Lock(),
}

async def query_data(url):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                return await resp.json()
    except:
        pass
    return None

async def load_event_cn():
    data = ''
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                    'https://wiki.biligame.com/pcr/活动日历') as resp:
                data = await resp.text('utf-8')
                data = transform_cn_calendar(data)
    except:
        print('解析B站WIKI日程表失败')
        return 1
    if data:
        event_data['cn'] = []
        for item in data:
            start_time = datetime.datetime.strptime(
                    item['start'], r"%Y/%m/%d %H:%M")
            end_time = datetime.datetime.strptime(
                    item['end'], r"%Y/%m/%d %H:%M")
            event = {'title': item['title'], 'start': start_time, 
                     'end': end_time, 'type': 1}
            if '倍' in event['title']:
                event['type'] = 2
            elif '团队战' in event['title']:
                event['type'] = 3
            event_data['cn'].append(event)
        return 0
    return 1

async def load_event_tw():
    data = await query_data('https://pcredivewiki.tw/static/data/event.json')
    if data:
        event_data['tw'] = []
        for item in data:
            start_time = datetime.datetime.strptime(item['start_time'], r"%Y/%m/%d %H:%M")
            end_time = datetime.datetime.strptime(item['end_time'], r"%Y/%m/%d %H:%M")
            event = {'title': item['campaign_name'], 'start': start_time, 'end': end_time, 'type': 1}
            if '倍' in event['title']:
                event['type'] = 2
            elif '戰隊' in event['title']:
                event['type'] = 3
            event_data['tw'].append(event)
        return 0
    return 1

async def load_event_jp():
    data = await query_data('https://cdn.jsdelivr.net/gh/pcrbot/calendar-updater-action@gh-pages/jp.json')
    if data:
        event_data['jp'] = []
        for item in data:
            start_time = datetime.datetime.strptime(item['start_time'], r'%Y/%m/%d %H:%M:%S')
            end_time = datetime.datetime.strptime(item['end_time'], r'%Y/%m/%d %H:%M:%S')
            event = {'title': item['name'], 'start': start_time, 'end': end_time, 'type': 1}
            if '倍' in event['title']:
                event['type'] = 2
            elif '公会战' in event['title']:
                event['type'] = 3
            event_data['jp'].append(event)
        return 0
    return 1

async def load_event_gamewith():
    data = ''
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get('https://gamewith.jp/pricone-re/') as resp:
                data = await resp.text('utf-8')
                data = transform_gamewith_calendar(data)
    except:
        print('解析gamewith日程表失败')
        return 1
    if data:
        event_data['jp'] = []
        for item in data:
            start_time = datetime.datetime.strptime(
                    item['start_time'], r'%Y/%m/%d %H:%M:%S')
            end_time = datetime.datetime.strptime(
                    item['end_time'], r'%Y/%m/%d %H:%M:%S')
            event = {'title': item['name'], 'start': start_time, 
                     'end': end_time, 'type': item['type']}
            event_data['jp'].append(event)
        return 0
    return 1

async def load_event(server):
    if server == 'cn':
        return await load_event_cn()
    elif server == 'tw':
        return await load_event_tw()
    elif server == 'jp':
        return await load_event_gamewith()
    return 1

def get_pcr_now(offset):
    pcr_now = datetime.datetime.now()
    if pcr_now.hour < 5:
        pcr_now -= datetime.timedelta(days=1)
    #用晚6点做基准
    pcr_now = pcr_now.replace(hour=18, minute=0, second=0, microsecond=0) 
    pcr_now = pcr_now + datetime.timedelta(days=offset)
    return pcr_now

async def get_events(server, offset, days):
    events = []
    pcr_now = datetime.datetime.now()
    if pcr_now.hour < 5:
        pcr_now -= datetime.timedelta(days=1)
    #用晚6点做基准
    pcr_now = pcr_now.replace(hour=18, minute=0, second=0, microsecond=0)

    await lock[server].acquire()
    try:
        t = pcr_now.strftime('%y%m%d')
        if event_updated[server] != t:
            if await load_event(server) == 0:
                event_updated[server] = t
    finally:
        lock[server].release()
        

    start = pcr_now + datetime.timedelta(days=offset)
    end = start + datetime.timedelta(days=days)
    end -= datetime.timedelta(hours=18)  #晚上12点结束

    for event in event_data[server]:
        #在指定时间段内 已开始 且 未结束
        if end > event['start'] and start < event['end']:
            #还有几天开始
            event['start_days'] = math.ceil(
                    (event['start'] - start) / datetime.timedelta(days=1))
            #还有几天结束
            event['left_days'] = math.floor(
                    (event['end'] - start) / datetime.timedelta(days=1))
            events.append(event)
    #按type从大到小 按剩余天数从小到大
    events.sort(key=lambda item: item["type"] * 100 - item['left_days'], 
                reverse = True)
    return events


if __name__=='__main__':
    async def main():
        events = await get_events('cn', 0, 1)
        for event in events:
            print(event)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
