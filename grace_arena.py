import discord
from discord.ext.commands import Bot
import random
import datetime
import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import asyncio

class weekday:
    월요일=0
    화요일=1
    수요일=2
    목요일=3
    금요일=4
    토요일=5
    일요일=6

WEEKDAY=weekday.화요일

client=Bot(command_prefix=('~',))

content=lambda ctx:ctx.message.content
author=lambda ctx:ctx.message.author
channel=lambda ctx:ctx.message.channel.id
current_time=lambda:datetime.datetime.utcnow()+datetime.timedelta(hours=9)

BETA=True
BETA_TESTLAB=486550288686120961

sheet_name='temp_arena'
record_name='temp_record'

channels={
    '내전신청':    469109911016570890,
    '활동로그':    513694118472450048,
    '메시지_로그': 527859699702562828,
    '출입_로그':   516122942896078868,
    '테스트':      486550288686120961,
    '그룹찾기':    420843334614122516,
    '카지노':      594927387158904842,
    'Arena':       469109888077791242,
    }

roles={
    '외부인':      510731224654938112,
    '빠대':        527842187862605834,
}

if BETA:
    for _ in channels:
        channels[_]=BETA_TESTLAB

def is_moderator(member):
    return "운영진" in map(lambda x:x.name, member.roles)

def has_role(member, role):
    return role in map(lambda x:x.name, member.roles)

#내전 커맨드
addr='https://docs.google.com/spreadsheets/d/1iT9lW3ENsx0zFeFVKdvqXDF9OJeGMqVF9zVdgnhMcfg/edit#gid=0'
scope=['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
grace=None

async def get_worksheet(sheet_name=sheet_name):
    creds=ServiceAccountCredentials.from_json_keyfile_name("Grace-defe42f05ec3.json", scope)
    auth=gspread.authorize(creds)
    if creds.access_token_expired:
        auth.login()

    sheet=auth.open_by_url(addr)
    try:
        worksheet=sheet.worksheet(sheet_name)
    except gspread.exceptions.APIError:
        for gamble_channel in gamble_channels:
            await client.get_channel(gamble_channel).send("API 호출 횟수에 제한이 걸렸습니다. 잠시후 다시 시도해주세요.")
        return -1
    return worksheet

async def get_all_players(ws):
    return [*map(lambda x:x[0],ws.get_all_values()[1:])]

def get_member_from_mention(mention):
    if not (mention.startswith('<@') and mention.endswith('>')):
        return -1
    if mention[2]!='!':
        m=int(mention[2:-1])
    else:
        m=int(mention[3:-1])
    return grace.get_member(m)

current_game=None

class Internal():
    @classmethod
    async def create(cls, time):
        global current_game
        self=Internal()
        await self.set_time(time)
        ws=await get_worksheet(sheet_name)
        current_game=self
        return self

    @classmethod
    async def check_integrity(cls):
        temp=Internal()
        try:
            time=await temp.get_time()
            assert isinstance(time, datetime.datetime)
            return True
        except:
            return False

    async def get_players(self):
        ws=await get_worksheet(sheet_name)
        val=await get_all_players(ws)
        return [*map(get_member_from_mention,val)]

    async def check_availability(self,player):
        ws=await get_worksheet(record_name)
        return len(ws.findall(player.mention))!=0

    async def add_player(self,new_player):
        ws=await get_worksheet(sheet_name)
        val=ws.findall(new_player.mention)
        if len(val)==0 or (len(val)==1 and val[0].row==1):
            ws.append_row([new_player.mention])
            return True
        return False

    async def remove_player(self,new_player):
        ws=await get_worksheet(sheet_name)
        val=ws.findall(new_player.mention)
        if len(val)==2 or (len(val)==1 and val[0].row!=1):
            ws.delete_row(val[-1].row)
            return True
        return False

    async def get_time(self):
        ws=await get_worksheet(sheet_name)
        return eval(ws.cell(1,1).value)

    async def close(self):
        ws=await get_worksheet(sheet_name)
        rows=ws.row_count
        for _ in range(2,rows+1):
            ws.delete_row(2)
        ws.update_cell(1,1,'')

        ws=await get_worksheet(record_name)
        rows=ws.row_count
        for _ in range(2,rows+1):
            ws.delete_row(2)
        ws.update_cell(1,1,'')

@client.command()
async def 업데이트(message):
    global current_game
    if message.channel.id!=channels['Arena']:
        return
    if await Internal.check_integrity():
        current_game=Internal()
        msg="아레나 설정이 업데이트되었습니다."
    else:
        msg="저장된 아레나가 없습니다."
    await message.channel.send(msg)

@client.command()
async def 확인(message):
    global current_game

    if message.channel.id!=channels['Arena']:
        return

    if current_game is None:
        await message.channel.send("아레나가 예정되어 있지 않습니다.")

    else:
        msg="{} 아레나가".format(str(await current_game.get_time())[:10])
        if current_time()<(await current_game.get_time()):
            msg+="신청중입니다."
        elif current_time()<(await current_game.get_time())+datetime.timedelta(hours=1):
            msg+="준비중입니다."
        else:
            msg+="진행중입니다."
        await message.channel.send(msg)

@client.command()#TODO
async def 종료(message):
    global current_game

    if message.channel.id!=channels['Arena']:
        return
    if current_game is None:
        await message.channel.send("신청중인 아레나가 없습니다.")
        return

    closer=author(message)
    if not is_moderator(closer):
        await message.channel.send("운영진만 아레나를 종료할 수 있습니다.")
        return
    
    logchannel=message.message.guild.get_channel(channels['활동로그'])

    log="{} 아레나 참가자 목록\n".format(str(await current_game.get_time())[:10])
    cnt=1
    for user in (await current_game.get_players()):
        log+='\n{}. {}'.format(cnt, user.nick.split('/')[0])
        if cnt==12:
            break
        cnt+=1

    await current_game.close()
    current_game=None

    await logchannel.send(log)
    await message.channel.send("아레나가 종료되었습니다.")

@client.command()
async def 목록(message):
    global current_game

    if message.channel.id!=channels['Arena']:
        return
    if current_game is None:
        await message.channel.send("신청중인 아레나가 없습니다.")
        return

    embed=discord.Embed(title="아레나 신청자 목록")
    embed.add_field(name="날짜",value=str(await current_game.get_time())[:10], inline=True)

    log=""
    cnt=0
    for user in await current_game.get_players():
        cnt+=1
        log+='\n{}. {}'.format(cnt, user.nick.split('/')[0])
    log+='\n\n아레나 신청자 총 {}명'.format(cnt)

    embed.add_field(name="신청자",value=log)
    await message.channel.send(embed=embed)

@client.command()#TODO
async def 신청(message):
    global current_game

    if message.channel.id!=channels['Arena']:
        return
    if current_game is None:
        await message.channel.send("신청중인 아레나가 없습니다.")
        return

    player=author(message)

    if current_time()>(await current_game.get_time()):
        await message.channel.send("신청이 마감되었습니다.")
        return

    if not await current_game.check_availability(player):
        await message.channel.send("{}님은 내전 최소 기준을 충족하지 못해 신청이 불가능합니다.".format(player.mention))
        return

    if await current_game.add_player(player):
        await message.channel.send("{}님의 신청이 완료되었습니다.".format(player.mention))
        return

    await message.channel.send("이미 신청하셨습니다.")

@client.command()
async def 취소(message):
    global current_game

    if message.channel.id!=channels['Arena']:
        return
    if current_game is None:
        await message.channel.send("신청중인 아레나가 없습니다.")
        return

    player=author(message)

    if await current_game.get_time()<current_time():
        await message.channel.send("신청 취소가 불가합니다.")
        return

    if await current_game.remove_player(player):
        await message.channel.send("{}님의 신청 취소가 완료되었습니다.".format(player.mention))
        return

    await message.channel.send("신청되지 않았습니다.")

@client.command()
async def 임의신청(message):
    global current_game

    if message.channel.id!=channels['Arena']:
        return
    if current_game is None:
        await message.channel.send("신청중인 아레나가 없습니다.")
        return

    opener=author(message)
    if opener!=await current_game.get_opener() and (not is_moderator(opener)):
        await message.channel.send("운영진만 임의신청이 가능합니다.")
        return

    players=message.message.content.split()[1:]

    for plr in players:
        try:
            player=client.get_user(int(plr[3:-1]))
            print(player)
            if player==None:
                raise Exception
        except:
            continue
        if await current_game.add_player(player):
            await message.channel.send("{}님의 임의신청이 완료되었습니다.".format(player.mention))
        else:
            await message.channel.send("{}님은 이미 신청된 플레이어입니다.".format(player.mention))
        del player

@client.command()
async def 신청반려(message):
    global current_game

    if message.channel.id!=channels['Arena']:
        return
    if current_game is None:
        await message.channel.send("신청중인 내전이 없습니다.")
        return

    opener=author(message)
    if opener!=await current_game.get_opener() and (not is_moderator(opener)):
        await message.channel.send("운영진만 신청반려가 가능합니다.")
        return

    players=message.message.mentions

    for player in players:
        if await current_game.remove_player(player):
            await message.channel.send("{}님의 신청반려가 완료되었습니다.".format(player.mention))
        else:
            await message.channel.send("{}님은 신청되지 않은 플레이어입니다.".format(player.mention))

@client.command()
async def 아레나1(message):
    pass

@client.command()
async def 아레나2(message):
    pass

############################################################
#자동 개최#TODO
@client.event
async def auto_open():
    global current_game
    global grace
    await client.wait_until_ready()
    grace=client.get_guild(359714850865414144)
    
    cur=current_time()

    arenachannel=grace.get_channel(channels['Arena'])

    daydelta=WEEKDAY-cur.weekday()
    if daydelta<0:
        daydelta+=7
    if daydelta==0:
        daydelta=(cur.hour>=24)*7

    next_notify=datetime.datetime(cur.year, cur.month, cur.day, 14, 20, 0)+datetime.timedelta(days=daydelta)

    while True:
        await asyncio.sleep((next_notify-current_time()).seconds)
        deadline=next_notify+datetime.timedelta(hours=8, minutes=1)

        ws=await get_spreadsheet()
        current_game=Internal.create(deadline)

        msg='@everyone\n{} 아레나 신청이 열렸습니다.'.format(str(await current_game.get_time())[:10])
        await arenachannel.send(msg)

        next_notify=next_notify+datetime.timedelta(days=7)

############################################################
#자동 기록(이벤트)
@client.event
async def on_ready():
    print("login: Grace Arena")
    print(client.user.name)
    print(client.user.id)
    print("---------------")

############################################################
#실행
access_token = os.environ["BOT_TOKEN"]
client.loop.create_task(auto_open())
client.run(access_token)
