import discord
from discord.ext.commands import Bot
import random
import datetime
import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import asyncio

client=Bot(command_prefix=('#',))

content=lambda ctx:ctx.message.content
author=lambda ctx:ctx.message.author
channel=lambda ctx:ctx.message.channel.id
current_time=lambda:datetime.datetime.utcnow()+datetime.timedelta(hours=9)

BETA=True
BETA_TESTLAB=486550288686120961

sheet_name='temp_minerals'
record_name='temp_record'

channels={
    '내전신청':    469109911016570890,
    '미네랄즈':    613747228976087040,
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

############################################################
#일반 커맨드
@client.command()
async def 리그(message):
    if BETA and message.channel.id!=BETA_TESTLAB: return
    await message.channel.send("https://www.twitch.tv/overwatchleague_kr")

@client.command()
async def 랜덤(message):
    if BETA and message.channel.id!=BETA_TESTLAB: return
    selection=content(message)
    items=selection.split()[1:]
    await message.channel.send("||{}||".format(random.choice(items)))

@client.command()
async def 쟁탈추첨(message):
    if BETA and message.channel.id!=BETA_TESTLAB: return
    maps=['리장 타워','일리오스','오아시스','부산','네팔',]
    await message.channel.send(random.choice(maps))

############################################################
#그룹찾기 - 빠른대전
@client.command()
async def 빠대(message):
    if message.channel.id!=channels['그룹찾기']: return
    member=author(message)
    role=member.guild.get_role(roles['빠대'])
    if not has_role(member, '빠대'):
        await member.add_roles(role)
        await message.channel.send('{} 빠대 역할이 부여되었습니다.'.format(member.mention))
    else:
        await member.remove_roles(role)
        await message.channel.send('{} 빠대 역할이 제거되었습니다.'.format(member.mention))

@client.command()
async def 빠대목록(message):
    if message.channel.id!=channels['그룹찾기']: return
    member=author(message)
    role=member.guild.get_role(roles['빠대'])
    waiting=role.members

    embed=discord.Embed(title="빠대 대기자 목록")

    log=""
    for user in waiting:
        log+='\n{}'.format(user.nick.split('/')[0])

    embed.add_field(name="대기자",value=log[1:])
    await message.channel.send(embed=embed)

############################################################
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
    return [*map(lambda x:x[0],ws.get_all_values()[3:])]

def get_member_from_mention(mention):
    if not (mention.startswith('<@') and mention.endswith('>')):
        return -1
    if mention[2]!='!':
        m=int(mention[2:-1])
    else:
        m=int(mention[3:-1])
    return grace.get_member(m)

class Internal():
    @classmethod
    async def create(cls, opener, time):
        self=Internal()
        await self.set_opener(opener)
        await self.set_time(time)
        ws=await get_worksheet()
        ws.update_cell(3,1,'0')
        return self

    @classmethod
    async def check_integrity(cls):
        temp=Internal()
        try:
            opener=await temp.get_opener()
            time=await temp.get_time()
            assert isinstance(opener, discord.Member) and isinstance(time, datetime.datetime)
            return True
        except:
            return False

    async def get_opener(self):
        ws=await get_worksheet()
        return get_member_from_mention(ws.cell(1,1).value)

    async def get_players(self):
        ws=await get_worksheet()
        val=await get_all_players(ws)
        users=[]
        for user in map(get_member_from_mention,val):
            if user==-1:
                pass
            else:
                users.append(user)
        return users

    async def add_player(self,new_player):
        ws=await get_worksheet()
        val=ws.findall(new_player.mention)
        if len(val)==0 or (len(val)==1 and val[0].row==1):
            ws.append_row([new_player.mention])
            return True
        return False

    async def remove_player(self,new_player):
        ws=await get_worksheet()
        val=ws.findall(new_player.mention)
        if len(val)==2 or (len(val)==1 and val[0].row!=1):
            ws.delete_row(val[-1].row)
            return True
        return False

    async def open_additional(self):
        ws=await get_worksheet()
        if ws.cell(3,1).value=='0':
            ws.update_cell(3,1,'1')
            return True
        return False

    async def set_time(self, time):
        ws=await get_worksheet()
        ws.update_cell(2,1,repr(time))

    async def set_opener(self, opener):
        ws=await get_worksheet()
        ws.update_cell(1,1,opener.mention)

    async def get_time(self):
        ws=await get_worksheet()
        return eval(ws.cell(2,1).value)

    async def is_additional_opened(self):
        ws=await get_worksheet()
        return ws.cell(3,1).value=='1'

    async def close(self):
        ws=await get_worksheet()
        ws.clear()
        ws.resize(rows=3, cols=1)

    async def leave_record(self):
        ws=await get_worksheet(record_name)
        for user in await current_game.get_players():
            ws.append_row([user.mention])

current_game=None

@client.command()
async def 업데이트(message):
    global current_game
    if message.channel.id!=channels['미네랄즈']:
        return
    if await Internal.check_integrity():
        current_game=Internal()
        msg="내전 설정이 업데이트되었습니다."
    else:
        msg="저장된 내전이 없습니다."
    await message.channel.send(msg)

@client.command()
async def 내전개최(message):
    global current_game

    if message.channel.id!=channels['미네랄즈']:
        return
    if current_game is not None:
        await message.channel.send("이미 {}에 내전이 예정되어 있습니다.".format(str(await current_game.get_time())[:-3]))
        return
    
    opener=author(message)

    current=current_time()
    time=content(message).split()
    if len(time)==1:
        hour=21
        minute=0
        hour24=True
    else:
        time=time[1].split(':')
        hour=int(time[0])
        minute=int(time[1])
        hour24=False
        if hour>12:
            hour24=True
    time=datetime.datetime(year=current.year, month=current.month, day=current.day, hour=0, minute=0)\
         +datetime.timedelta(hours=hour, minutes=minute)

    while time<current_time():
        if hour24:
            time+=datetime.timedelta(hours=24)
        else:
            time+=datetime.timedelta(hours=12)
    current_game=await Internal.create(opener, time)

    msg="@everyone\n{} 내전 신청이 열렸습니다.\n개최자: {}".format(str(await current_game.get_time())[:-3], (await current_game.get_opener()).mention)
    await message.channel.send(msg)

@client.command()
async def 시간변경(message):
    global current_game

    if message.channel.id!=channels['미네랄즈']:
        return
    if current_game is None:
        await message.channel.send("신청중인 내전이 없습니다.")
        return

    opener=author(message)

    current=current_time()
    time=content(message).split()
    if len(time)==1:
        hour=21
        minute=0
        hour24=True
    else:
        time=time[1].split(':')
        hour=int(time[0])
        minute=int(time[1])
        hour24=False
        if hour>12:
            hour24=True
    time=datetime.datetime(year=current.year, month=current.month, day=current.day, hour=0, minute=0)\
         +datetime.timedelta(hours=hour, minutes=minute)

    while time<current_time():
        if hour24:
            time+=datetime.timedelta(hours=24)
        else:
            time+=datetime.timedelta(hours=12)
    current_game=await Internal.create(opener, time)
    
    prev_time=await current_game.get_time()
    await current_game.set_time(time)

    msg="@everyone\n{} 내전이 {}로 변경되었습니다.\n개최자: {}".format(str(prev_time)[:-3], str(await current_game.get_time())[:-3], (await current_game.get_opener()).mention)
    await message.channel.send(msg)

@client.command()
async def 내전확인(message):
    global current_game

    if message.channel.id!=channels['미네랄즈']:
        return

    if current_game is None:
        await message.channel.send("내전이 예정되어 있지 않습니다.")

    else:
        msg="{}\n{} 내전 신청이 열려 있습니다.\n개최자: {}".format(author(message).mention, str(await current_game.get_time())[:-3], (await current_game.get_opener()).nick.split('/')[0])
        await message.channel.send(msg)

@client.command()
async def 개최자변경(message):
    global current_game

    if message.channel.id!=channels['미네랄즈']:
        return
    if current_game is None:
        await message.channel.send("신청중인 내전이 없습니다.")
        return

    prev_opener=author(message)
    if prev_opener!=(await current_game.get_opener()) and (not is_moderator(prev_opener)):
        await message.channel.send("내전 개최자 또는 운영진만 개최자를 변경할 수 있습니다.")
        return

    new_opener=message.message.mentions[0]
    await current_game.set_opener(new_opener)
    msg="@everyone\n{} 내전 개최자가 {}로 변경되었습니다.".format(str(await current_game.get_time())[:-3], (await current_game.get_opener()).mention)
    await message.channel.send(msg)

@client.command()
async def 내전종료(message):
    global current_game

    if message.channel.id!=channels['미네랄즈']:
        return
    if current_game is None:
        await message.channel.send("신청중인 내전이 없습니다.")
        return

    closer=author(message)
    if closer!=(await current_game.get_opener()) and (not is_moderator(closer)):
        await message.channel.send("내전 개최자 또는 운영진만 내전을 종료할 수 있습니다.")
        return
    
    logchannel=message.message.guild.get_channel(channels['활동로그'])

    log="{} 내전 참가자 목록\n\n개최자: {}\n".format(str(await current_game.get_time())[:-3], (await current_game.get_opener()).nick.split('/')[0])
    cnt=1
    for user in (await current_game.get_players()):
        log+='\n{}. {}'.format(cnt, user.nick.split('/')[0])
        cnt+=1
    log+='\n\n내전 신청자 총 {}명'.format(cnt-1)

    await current_game.leave_record()
    await current_game.close()
    current_game=None

    await logchannel.send(log)
    await message.channel.send("내전이 종료되었습니다.")

@client.command()
async def 목록(message):
    global current_game

    if message.channel.id!=channels['미네랄즈']:
        return
    if current_game is None:
        await message.channel.send("신청중인 내전이 없습니다.")
        return

    embed=discord.Embed(title="내전 참가자 목록")
    embed.add_field(name="일시",value=str(await current_game.get_time())[:-3], inline=True)
    embed.add_field(name="개최자",value=(await current_game.get_opener()).nick.split('/')[0], inline=False)

    log=""
    cnt=0
    for user in await current_game.get_players():
        cnt+=1
        log+='\n{}. {}'.format(cnt, user.nick.split('/')[0])
    log+='\n\n내전 신청자 총 {}명'.format(cnt)

    embed.add_field(name="신청자",value=log)
    await message.channel.send(embed=embed)

@client.command()
async def 추가신청허용(message):
    global current_game

    if message.channel.id!=channels['미네랄즈']:
        return
    if current_game is None:
        await message.channel.send("신청중인 내전이 없습니다.")
        return

    opener=author(message)
    if opener!=await current_game.get_opener() and (not is_moderator(opener)):
        await message.channel.send("내전 개최자 또는 운영진만 추가신청을 허용할 수 있습니다.")
        return

    if not await current_game.open_additional():
        await message.channel.send("추가신청이 이미 허용되어 있습니다.")
        return

    await message.channel.send("@everyone\n내전의 추가신청이 허용되었습니다.")

@client.command()
async def 신청(message):
    global current_game

    if message.channel.id!=channels['미네랄즈']:
        return
    if current_game is None:
        await message.channel.send("신청중인 내전이 없습니다.")
        return

    player=author(message)

    if await current_game.is_additional_opened()==False and\
       (datetime.timedelta(minutes=-9)<current_time()-(await current_game.get_time())<datetime.timedelta(hours=1)):
        await message.channel.send("신청이 마감되었습니다. 추가신청을 기다려주세요.")
        return

    if await current_game.add_player(player):
        await message.channel.send("{}님의 신청이 완료되었습니다.".format(player.mention))
        return

    await message.channel.send("이미 신청하셨습니다.")

@client.command()
async def 취소(message):
    global current_game

    if message.channel.id!=channels['미네랄즈']:
        return
    if current_game is None:
        await message.channel.send("신청중인 내전이 없습니다.")
        return

    player=author(message)

    if await current_game.get_time()-current_time()<datetime.timedelta(minutes=9):
        await message.channel.send("신청 취소가 불가합니다.")
        return

    if await current_game.remove_player(player):
        await message.channel.send("{}님의 신청 취소가 완료되었습니다.".format(player.mention))
        return

    await message.channel.send("신청되지 않았습니다.")

@client.command()
async def 임의신청(message):
    global current_game

    if message.channel.id!=channels['미네랄즈']:
        return
    if current_game is None:
        await message.channel.send("신청중인 내전이 없습니다.")
        return

    opener=author(message)
    if opener!=await current_game.get_opener() and (not is_moderator(opener)):
        await message.channel.send("내전 개최자 또는 운영진만 임의신청이 가능합니다.")
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

    if message.channel.id!=channels['미네랄즈']:
        return
    if current_game is None:
        await message.channel.send("신청중인 내전이 없습니다.")
        return

    opener=author(message)
    if opener!=await current_game.get_opener() and (not is_moderator(opener)):
        await message.channel.send("내전 개최자 또는 운영진만 신청반려가 가능합니다.")
        return

    players=message.message.mentions

    for player in players:
        if await current_game.remove_player(player):
            await message.channel.send("{}님의 신청반려가 완료되었습니다.".format(player.mention))
        else:
            await message.channel.send("{}님은 신청되지 않은 플레이어입니다.".format(player.mention))


############################################################
#자동 기록(이벤트)
@client.event
async def on_ready():
    global grace
    await client.wait_until_ready()
    grace=client.get_guild(359714850865414144)
    print("login: Grace Minerals")
    print(client.user.name)
    print(client.user.id)
    print("---------------")

############################################################
#실행
access_token = os.environ["BOT_TOKEN"]
client.run(access_token)
