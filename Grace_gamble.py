import discord
from discord.ext.commands import Bot
import asyncio
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import random
import openpyxl
from datetime import datetime, timedelta
from time import sleep

daily=200

gamble_channel=486550288686120961
ws_name='Beta'

content=lambda ctx:ctx.message.content
author=lambda ctx:ctx.message.author
channel=lambda ctx:ctx.message.channel.id
current_time=lambda:datetime.utcnow()+timedelta(hours=9)

client = Bot(command_prefix=('>',))
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']

def get_spreadsheet():
    creds=ServiceAccountCredentials.from_json_keyfile_name("Grace-defe42f05ec3.json", scope)
    auth=gspread.authorize(creds)

    if creds.access_token_expired:
        auth.login()

    sheet=auth.open_by_url("https://docs.google.com/spreadsheets/d/1y1XnmgggAxVVJ3jJrVBocGTjpBR7b8_L9sf47GKBNok/edit#gid=0")
    worksheet=sheet.worksheet(ws_name)
    return worksheet

def get_row(ws,author):
    try: 
        return ws, ws.find(author.mention).row
    except gspread.exceptions.CellNotFound:
        ws.append_row([author.mention,'0'])
        return ws, ws.find(author.mention).row
    except gspread.exceptions.APIError:
        return ws, -1

def get_money(author):
    ws=get_spreadsheet()
    row=get_row(ws,author)
    if row==-1:
        return 0
    return ws.cell(row,2).value

def redeemable(author):
    ws=get_spreadsheet()
    row=get_row(ws,author)
    if row==-1:
        return False
    timestr=ws.cell(row,3).value
    return current_time()-time>=timedelta(days=1)

def update_money(author, money):
    ws=get_spreadsheet()
    row=get_row(ws,author)
    if row==-1:
        return False
    ws.update_cell(row, 2, str(money))
    return 1

@client.event
async def on_ready():
    print("login: Grace Gamble Beta")
    print(client.user.name)
    print(client.user.id)
    print("---------------")
    await client.change_presence(activity=discord.Game(name='>>', type=1))

@client.command()
async def 출석(message):
    author=author(message)
    if redeemable(author):
        money=get_money(author)
        if update_money(author, money+daily):
            await message.channel.send("{}\n출석체크 완료!\n현재 잔고:{}G".format(author.mention, money+daily))
            return
    await message.channel.send("출석체크는 24시간에 한번만 가능합니다.")


@client.command()
async def 확인(message):
    author=author(message)
    money=get_money(author)
    await message.channel.send("{}\n잔고:{}G".format(author.mention, money))

@client.command()
async def 동전(message):
    author=author(message)
    content=content(message)
    com, choice, bet, *rest=content.split()
    
    if choice not in ('앞', '뒤'):
        await message.channel.send("{} 앞 또는 뒤만 선택할 수 있습니다.".format(author.mention))
        return
    
    if not bet.isnumeric():
        await message.channel.send("{} 베팅 금액은 정수여야 합니다.".format(author.mention))
        return
    
    bet=int(bet)
    money=get_money(author)
    if bet>money:
        await message.channel.send("{} 베팅 금액은 소지 금액을 넘어설 수 없습니다. 현재 소지 금액: {}".format(author.mention, money))
        return

    msg="{}\n동전:".format(author.mention)
    
    result=random.choice(['앞','뒤'])
    msg+=result+'\n'

    if result==choice:
        msg+='성공!\n'
        money+=bet
    else:
        msg+='실패...\n'
        money-=bet

    update_money(author, money)
    msg+='현재 잔고: {}'.format(money)

    await message.channel.send(msg)

@client.command()
async def 순위(message):
    author=author(message)
    money=get_money(author)
    ws=get_spreadsheet()
    moneys=[*sorted(map(lambda x:int(x) if x.isnumeric() else -1,ws.col_values(2)), reverse=True)]
    rank=moneys.index(money)
    same=moneys.count(money)
    await message.channel.send("{}\n현재 {}위(공동 {}명)".format(author.mention, rank, same))

@client.command()
async def 랭킹(message):
    author=author(message)
    content=content(message)

    ws=get_spreadsheet()
    data=get_all_values()[1:]
    data.sort(key=lambda x:int(x[1]), reverse=True)

    ct=content.split()
    maxrank=min(10, len(data))
    if len(ct)>1 and ct[1].isnumeric():
        maxrank=min(int(ct[1]), len(data))

    log="현재 랭킹"
    for i in range(maxrank):
        user=client.get_user(int(data[0][3:-1]))
        log+="\n{}. {}: {}G".format(i+1, user.nick.split('/')[0], data[i][1])

    await message.channel.send(log)

async def periodic_ranking():
    await client.wait_until_ready()
    cur=current_time()
    next_notify=datetime(cur.year, cur.month, cur.day+1, 0, 0, 0)
    while True:
        sleep((next_notify-current_time()).seconds)

        ws=get_spreadsheet()
        data=get_all_values()[1:]
        data.sort(key=lambda x:int(x[1]), reverse=True)

        log="현재 랭킹"
        for i in range(min(10, len(data))):
            user=client.get_user(int(data[0][3:-1]))
            log+="\n{}. {}: {}G".format(i+1, user.nick.split('/')[0], data[i][1])

        await client.send_message(gamble_channel, log)
        next_notify+=timedelta(days=1)

access_token = os.environ["BOT_TOKEN"]
client.run(access_token)