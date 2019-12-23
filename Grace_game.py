import discord
from discord.ext.commands import Bot
import random
import datetime
import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import asyncio

client=Bot(command_prefix=('!',))

content=lambda ctx:ctx.message.content
author=lambda ctx:ctx.message.author
channel=lambda ctx:ctx.message.channel.id
current_time=lambda:datetime.datetime.utcnow()+datetime.timedelta(hours=9)

BETA=True
BETA_TESTLAB=486550288686120961

sheet_name='temp'
record_name='temp_record'

available=30 # 해당 숫자 분 전까지 신청 가능

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

def get_mention_from_player(member):
    mention=member.mention
    if mention[2]!='!':
        mention='<@!{}>'.format(mention[2:-1])
    return mention

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
        for entry in val:
            user=get_member_from_mention(entry)
            if user==-1 and entry.startswith('용병:'):
                users.append(entry)
            else:
                users.append(user)
        return users

    async def add_player(self,new_player):
        ws=await get_worksheet()
        val=ws.findall(get_mention_from_player(new_player))
        if len(val)==0 or (len(val)==1 and val[0].row==1):
            ws.append_row([get_mention_from_player(new_player)])
            return True
        return False

    async def add_external_player(self, new_player):
        ws=await get_worksheet()
        val=ws.findall("용병:"+new_player)
        if len(val)==0:
            ws.append_row(["용병:"+new_player])
            return True
        return False

    async def remove_player(self,new_player):
        ws=await get_worksheet()
        val=ws.findall(get_mention_from_player(new_player))
        if len(val)==2 or (len(val)==1 and val[0].row!=1):
            ws.delete_row(val[-1].row)
            return True
        return False

    async def remove_external_player(self, new_player):
        ws=await get_worksheet()
        val=ws.findall("용병:"+new_player)
        if len(val)!=0:
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
            try:
                ws.append_row([user.mention])
            except:
                pass

current_game=None

@client.command()
async def 업데이트(message):
    global current_game
    if message.channel.id!=channels['내전신청']:
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

    if message.channel.id!=channels['내전신청']:
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

    if message.channel.id!=channels['내전신청']:
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

    if message.channel.id!=channels['내전신청']:
        return

    if current_game is None:
        await message.channel.send("내전이 예정되어 있지 않습니다.")

    else:
        msg="{}\n{} 내전 신청이 열려 있습니다.\n개최자: {}".format(author(message).mention, str(await current_game.get_time())[:-3], (await current_game.get_opener()).nick.split('/')[0])
        await message.channel.send(msg)

@client.command()
async def 개최자변경(message):
    global current_game

    if message.channel.id!=channels['내전신청']:
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

    if message.channel.id!=channels['내전신청']:
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
        try:
            log+='\n{}. {}'.format(cnt, user.nick.split('/')[0])
            cnt+=1
        except:
            continue
    log+='\n\n내전 신청자 총 {}명'.format(cnt-1)

    await current_game.leave_record()
    await current_game.close()
    current_game=None

    await logchannel.send(log)
    await message.channel.send("내전이 종료되었습니다.")

@client.command()
async def 목록(message):
    global current_game

    if message.channel.id!=channels['내전신청']:
        return
    if current_game is None:
        await message.channel.send("신청중인 내전이 없습니다.")
        return

    if current_time()-(await current_game.get_time())>=datetime.timedelta(hours=1):
        if await current_game.open_additional():
            await message.channel.send("@everyone\n내전의 추가신청이 허용되었습니다.")

    condition=message.message.content.split()

    if len(condition)==1:
        condition='전체'
    else:
        condition=condition[1]

    if condition in '홀 홀수'.split():
        condition='홀수'
    elif condition in '짝 짝수'.split():
        condition='짝수'
    elif condition in '홀짝'.split():
        condition='홀짝'
    else:
        condition='전체'

    embed=discord.Embed(title="내전 참가자 목록({})".format(condition))
    embed.add_field(name="일시",value=str(await current_game.get_time())[:-3], inline=True)
    embed.add_field(name="개최자",value=(await current_game.get_opener()).nick.split('/')[0], inline=False)

    log=""
    cnt=0
    for user in await current_game.get_players():
        try:
            user=user.nick
        except:
            pass
        cnt+=1
        if (condition in ['홀수', '전체'] and cnt%2==1) or (condition in ['짝수', '전체'] and cnt%2==0):
            log+='\n{}. {}'.format(cnt, user.split('/')[0])
        if condition in '홀짝'.split():
            if cnt%2==0:
                log+='\n__{}. {}__'.format(cnt, user.split('/')[0])
            else:
                log+='\n{}. {}'.format(cnt, user.split('/')[0])
    log+='\n\n내전 신청자 총 {}명'.format(cnt)

    embed.add_field(name="신청자",value=log)
    await message.channel.send(embed=embed)

@client.command()
async def 추가신청허용(message):
    global current_game

    if message.channel.id!=channels['내전신청']:
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

    if message.channel.id!=channels['내전신청']:
        return
    if current_game is None:
        await message.channel.send("신청중인 내전이 없습니다.")
        return

    player=author(message)

    if await current_game.is_additional_opened()==False:
        if (datetime.timedelta(minutes=-(available-1))<current_time()-(await current_game.get_time())<datetime.timedelta(hours=1)):
            await message.channel.send("신청이 마감되었습니다. 추가신청을 기다려주세요.")
            return
        if current_time()-(await current_game.get_time())>=datetime.timedelta(hours=1):
            await current_game.open_additional()
            await message.channel.send("@everyone\n내전의 추가신청이 허용되었습니다.")

    if await current_game.add_player(player):
        await message.channel.send("{}님의 신청이 완료되었습니다.".format(player.mention))
        return

    await message.channel.send("이미 신청하셨습니다.")

@client.command()
async def 취소(message):
    global current_game

    if message.channel.id!=channels['내전신청']:
        return
    if current_game is None:
        await message.channel.send("신청중인 내전이 없습니다.")
        return

    player=author(message)

    if await current_game.get_time()-current_time()<datetime.timedelta(minutes=(available-1)):
        await message.channel.send("신청 취소가 불가합니다.")
        return

    if await current_game.remove_player(player):
        await message.channel.send("{}님의 신청 취소가 완료되었습니다.".format(player.mention))
        return

    await message.channel.send("신청되지 않았습니다.")

@client.command()
async def 임의신청(message):
    global current_game

    if message.channel.id!=channels['내전신청']:
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
            player=get_member_from_mention(plr)
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

    if message.channel.id!=channels['내전신청']:
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

@client.command()
async def 용병신청(message):
    global current_game

    if message.channel.id!=channels['내전신청']:
        return
    if current_game is None:
        await message.channel.send("신청중인 내전이 없습니다.")
        return

    opener=author(message)
    if opener!=await current_game.get_opener() and (not is_moderator(opener)):
        await message.channel.send("내전 개최자 또는 운영진만 용병 신청이 가능합니다.")
        return

    players=message.message.content.split()[1:]

    for player in players:
        if await current_game.add_external_player(player):
            await message.channel.send("{}님의 용병 신청이 완료되었습니다.".format(player))
        else:
            await message.channel.send("{}님은 이미 신청된 용병입니다.".format(player))
        del player

@client.command()
async def 용병취소(message):
    global current_game

    if message.channel.id!=channels['내전신청']:
        return
    if current_game is None:
        await message.channel.send("신청중인 내전이 없습니다.")
        return

    opener=author(message)
    if opener!=await current_game.get_opener() and (not is_moderator(opener)):
        await message.channel.send("내전 개최자 또는 운영진만 용병 취소가 가능합니다.")
        return

    players=message.message.content.split()[1:]

    for player in players:
        if await current_game.remove_external_player(player):
            await message.channel.send("{}님의 용병 취소가 완료되었습니다.".format(player))
        else:
            await message.channel.send("{}님은 신청되지 않은 용병입니다.".format(player))

############################################################
#도움말
invalid_channels=(channels['테스트'],channels['카지노'])
@client.command()
async def 도움말(ctx):
    if (not BETA and ctx.channel.id in invalid_channels) or (BETA and ctx.channel.id!=BETA_TESTLAB):
        return
    embed = discord.Embed(title="Grace bot", description="그레이스 클랜 봇입니다.", color=0xeee657)
    embed.add_field(name="\u200B",value="\u200B",inline=False)
    embed.add_field(name="전체 서버",value="\u200B",inline=False)
    embed.add_field(name="\u200B",value="\u200B",inline=False)
    embed.add_field(name="!리그\n",value="한국 오버워치 리그 트위치 링크를 줍니다.\n",inline=False)
    embed.add_field(name="!랜덤 (선택1) (선택2) (선택3) ...\n",value="선택지 중 무작위로 하나를 골라줍니다.\n",inline=False)
    embed.add_field(name="!쟁탈추첨\n",value="쟁탈 맵 중 하나를 무작위로 골라줍니다.\n",inline=False)
    if ctx.channel.id==channels['내전신청'] or ctx.channel.id==channels['미네랄즈']:
        embed.add_field(name="\u200B",value="\u200B",inline=False)
        embed.add_field(name="내전신청방",value="\u200B",inline=False)
        embed.add_field(name="\u200B",value="\u200B",inline=False)
        embed.add_field(name="!내전개최 hh:mm",value="내전을 주어진 시각에 개최합니다. 시각을 주지 않으면 {}시로 설정됩니다.\n".format(20+(ctx.channel.id==channels['내전신청'])),inline=False)
        embed.add_field(name="!업데이트",value="내전 중 봇의 오류가 났다면 업데이트를 통해 내전 설정을 업데이트 할 수 있습니다.\n",inline=False)
        embed.add_field(name="\u200B",value="\u200B",inline=False)
        embed.add_field(name="내전 개최자 및 운영진만 사용 가능한 명령어",value="\u200B",inline=False)
        embed.add_field(name="!개최자변경 @사용자\n",value="개최자를 멘션한 사용자로 변경합니다.\n",inline=False)
        embed.add_field(name="!시간변경 hh:mm",value="내전의 개최 시각을 해당 시각으로 변경합니다.",inline=False)
        embed.add_field(name="!내전종료\n",value="내전을 종료하고, 로그를 기록합니다.\n",inline=False)
        embed.add_field(name="!추가신청허용\n",value="추가신청을 허용합니다. 한번 허용하면 이후로 계속 신청이 가능하며, 내전 개최 시점 1시간 이후로는 자동으로 신청이 가능합니다.\n",inline=False)
        embed.add_field(name="!임의신청 @사용자1 @사용자2 ...\n",value="멘션한 사용자들을 신청한 것으로 처리합니다.\n",inline=False)
        embed.add_field(name="!신청반려 @사용자1 @사용자2 ...\n",value="멘션한 사용자들의 신청을 반려합니다.\n",inline=False)
        embed.add_field(name="!용병신청 용병1 용병2 ...\n",value="용병들을 신청한 것으로 처리합니다.\n",inline=False)
        embed.add_field(name="!용병취소 용병1 용병2 ...\n",value="용병들의 신청을 취소합니다.\n",inline=False)
        embed.add_field(name="\u200B",value="\u200B",inline=False)
        embed.add_field(name="모든 사람이 사용 가능한 명령어",value="\u200B",inline=False)
        embed.add_field(name="!내전확인\n",value="현재 내전이 개최중이라면 내전의 정보를 출력합니다.",inline=False)
        embed.add_field(name="!목록\n",value="선착순으로, 신청자 목록을 확인합니다. 목록 뒤에 '홀수' 또는 '짝수'를 입력하면 홀수번째 또는 짝수번째 신청한 목록을 볼 수 있습니다. '홀짝'을 입력하면 짝수번째 신청자에 밑줄이 쳐진 채로 출력됩니다.\n",inline=False)
        embed.add_field(name="!신청\n",value="본인이 개최된 내전에 신청합니다.\n",inline=False)
        embed.add_field(name="!취소\n",value="본인의 내전 신청을 취소합니다.\n",inline=False)
    if ctx.channel.id==channels['그룹찾기']:
        embed.add_field(name="\u200B",value="\u200B",inline=False)
        embed.add_field(name="그룹찾기",value="\u200B",inline=False)
        embed.add_field(name="!빠대\n",value="빠대 역할이 없다면 역할을 부여하고, 있다면 제거합니다. '@빠대'로 멘션이 가능합니다.\n",inline=False)
        embed.add_field(name="!빠대목록\n",value="빠대 역할을 부여받은 모든 사람의 목록을 순서에 상관 없이 출력합니다.\n",inline=False)
    if ctx.channel.id==channels['Arena']:
        embed.add_field(name="\u200B",value="\u200B",inline=False)
        embed.add_field(name="Arena",value="\u200B",inline=False)
        embed.add_field(name="\u200B",value="\u200B",inline=False)
        embed.add_field(name="아레나 개최",value="아레나는 개최일의 정오부터 8시 정각까지 자동으로 신청을 받습니다.",inline=False)
        embed.add_field(name="!업데이트",value="내전 중 봇의 오류가 났다면 업데이트를 통해 내전 설정을 업데이트 할 수 있습니다.\n",inline=False)
        embed.add_field(name="\u200B",value="\u200B",inline=False)
        embed.add_field(name="운영진만 사용 가능한 명령어",value="\u200B",inline=False)
        embed.add_field(name="!아레나 팀 @사용자1 @사용자2 ...\n",value="멘션한 사용자들에게 아레나 팀 권한을 부여합니다.\n팀은 0, 1, 2 중 하나로, 1, 2는 각각 아레나 1, 2팀 역할을 부여하며 0은 아레나 역할을 제거합니다.")
        embed.add_field(name="!임의신청 @사용자1 @사용자2 ...\n",value="멘션한 사용자들을 이 순서대로 신청한 것으로 처리합니다.\n",inline=False)
        embed.add_field(name="!신청반려 @사용자1 @사용자2 ...\n",value="멘션한 사용자들의 신청을 반려합니다.\n",inline=False)
        embed.add_field(name="!안내\n",value="사용자를 개최자로 하여 안내 멘트를 출력합니다.\n",inline=False)
        embed.add_field(name="!종료 우승팀\n",value="아레나를 종료하고, 우승팀에게 카지노 상금을 지급하고, 아레나 팀 역할을 모두 제거하고, 로그를 기록합니다.\n 우승팀은 0, 1, 2 중 하나로, 1, 2는 각각 아레나 1, 2팀, 0은 우승자 없음을 의미합니다.\n",inline=False)
        embed.add_field(name="\u200B",value="\u200B",inline=False)
        embed.add_field(name="모든 사람이 사용 가능한 명령어",value="\u200B",inline=False)
        embed.add_field(name="!확인\n",value="현재 아레나의 상태를 확인합니다.",inline=False)
        embed.add_field(name="!목록\n",value="선착순으로, 신청자 목록을 확인합니다.\n",inline=False)
        embed.add_field(name="!신청\n",value="본인이 해당 아레나에 신청합니다. 지난 7일간 내전에 1회 이상 참여했어야 합니다.\n",inline=False)
        embed.add_field(name="!취소\n",value="본인의 신청을 취소합니다.\n",inline=False)
    await ctx.send(embed=embed)


############################################################
#자동 기록(이벤트)
@client.event
async def on_ready():
    global grace
    await client.wait_until_ready()
    grace=client.get_guild(359714850865414144)
    print("login: Grace Game")
    print(client.user.name)
    print(client.user.id)
    print("---------------")

############################################################
#실행
access_token = os.environ["BOT_TOKEN"]
client.run(access_token)
