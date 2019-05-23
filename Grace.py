import discord
from discord.ext.commands import Bot
import random
from datetime import datetime, timedelta
import os

client=Bot(command_prefix=('!',))

content=lambda ctx:ctx.message.content
author=lambda ctx:ctx.message.author
channel=lambda ctx:ctx.message.channel.id
current_time=lambda:datetime.utcnow()+timedelta(hours=9)

ALPHA=False
ALPHA_TESTLAB=463694274190376981

BETA=True
BETA_TESTLAB=486550288686120961

channels={
    '내전신청':    469109911016570890,
    '활동로그':    513694118472450048,
    '메시지_로그': 527859699702562828,
    '출입_로그':   516122942896078868,
    }

if BETA:
    for _ in channels:
        channels[_]=BETA_TESTLAB

if ALPHA:
    for _ in channels:
        channels[_]=ALPHA_TESTLAB

def is_moderator(member):
    print(member.roles)
    return "@운영진" in member.roles

############################################################
#일반 커맨드
@client.command()
async def 리그(message):
    await message.channel.send("https://www.twitch.tv/overwatchleague_kr")

@client.command()
async def 랜덤(message):
    selection=content(message)
    items=selection.split()[1:]
    await message.channel.send("||{}||".format(random.choice(items)))

@client.command()
async def 쟁탈추첨(message):
    maps=['리장 타워','일리오스','오아시스','부산','네팔',]
    await message.channel.send(random.choice(maps))

############################################################
#내전 커맨드
class Internal():
    def __init__(self,opener,time):
        self.opener=opener
        self.time=time
        self.players=[]
        self.additional_opened=False

    def __hash__(self):
        return hash((self.opener,self.time))

    def change_opener(self,new_opener):
        self.opener=new_opener

    def add_player(self,new_player):
        if new_player not in self.players:
            self.players.append(new_player)
            return True
        return False

    def remove_player(self,new_player):
        if new_player in self.players:
            self.players.remove(new_player)
            return True
        return False

    def open_additional(self):
        if not self.additional_opened:
            self.additional_opened=True
            return True
        return False

current_game=None

@client.command()
async def 내전개최(message):
    global current_game

    if message.channel.id!=channels['내전신청']:
        return
    if current_game is not None:
        await message.channel.send("이미 {}에 내전이 예정되어 있습니다.".format(str(current_game.time)[:-3]))
        return
    
    opener=author(message)

    current=current_time()
    time=content(message).split()
    if len(time)==1:
        hour=21
        minute=0
    else:
        time=time[1].split(':')
        hour=int(time[0])
        minute=int(time[1])
    time=datetime(year=current.year, month=current.month, day=current.day, hour=hour, minute=minute)

    current_game=Internal(opener, time)

    msg="@everyone\n{} 내전 신청이 열렸습니다.\n개최자: {}".format(str(current_game.time)[:-3], current_game.opener.mention)
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
    else:
        time=time[1].split(":")
        hour=int(time[0])
        minute=int(time[1])
    time=datetime(year=current.year, month=current.month, day=current.day, hour=hour, minute=minute)

    prev_time, current_game.time=current_game.time, time

    msg="@everyone\n{} 내전이 {}로 변경되었습니다.\n개최자: {}".format(str(prev_time)[:-3], str(current_game.time)[:-3], current_game.opener.mention)
    await message.channel.send(msg)

@client.command()
async def 내전확인(message):
    global current_game

    if message.channel.id!=channels['내전신청']:
        return

    if current_game is None:
        await message.channel.send("내전이 예정되어 있지 않습니다.")

    else:
        msg="{}\n{} 내전 신청이 열려 있습니다.\n개최자: {}".format(author(message).mention, str(current_game.time)[:-3], current_game.opener.mention)
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
    if prev_opener!=current_game.opener and (not is_moderator(prev_opener)):
        await message.channel.send("내전 개최자 또는 운영진만 개최자를 변경할 수 있습니다.")
        return

    new_opener=message.message.mentions[0]
    current_game.opener=new_opener
    msg="{} 내전 개최자가 {}로 변경되었습니다.".format(str(current_game.time)[:-3], current_game.opener.mention)
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
    if closer!=current_game.opener and (not is_moderator(closer)):
        await message.channel.send("내전 개최자 또는 운영진만 내전을 종료할 수 있습니다.")
        return
    
    logchannel=message.message.guild.get_channel(channels['활동로그'])

    log="{} 내전 참가자 목록\n\n개최자: {}\n".format(str(current_game.time)[:-3], current_game.opener.nick.split('/')[0])
    cnt=1
    for user in current_game.players:
        log+='\n{}. {}'.format(cnt, user.nick.split('/')[0])
        cnt+=1
    log+='\n\n내전 신청자 총 {}명'.format(cnt-1)

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

    log="{} 내전 참가자 목록\n\n개최자: {}\n".format(str(current_game.time)[:-3], current_game.opener.nick.split('/')[0])
    cnt=1
    for user in current_game.players:
        log+='\n{}. {}'.format(cnt, user.nick.split('/')[0])
        cnt+=1
    log+='\n\n내전 신청자 총 {}명'.format(cnt-1)
    await message.channel.send(log)

@client.command()
async def 추가신청허용(message):
    global current_game

    if message.channel.id!=channels['내전신청']:
        return
    if current_game is None:
        await message.channel.send("신청중인 내전이 없습니다.")
        return

    opener=author(message)
    if opener!=current_game.opener and (not is_moderator(opener)):
        await message.channel.send("내전 개최자 또는 운영진만 추가신청을 허용할 수 있습니다.")
        return

    if not current_game.open_additional():
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

    if current_game.additional_opened==False and\
       (timedelta(minutes=-10)<current_time()-current_game.time<timedelta(hours=1)):
        await message.channel.send("신청이 마감되었습니다. 추가신청을 기다려주세요.")
        return

    if current_game.add_player(player):
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

    if current_game.time-current_time()<timedelta(minutes=10):
        await message.channel.send("신청 취소가 불가합니다.")
        return

    if current_game.remove_player(player):
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
    if opener!=current_game.opener and (not is_moderator(opener)):
        await message.channel.send("내전 개최자 또는 운영진만 임의신청이 가능합니다.")
        return

    players=message.message.mentions

    for player in players:
        if current_game.add_player(player):
            await message.channel.send("{}님의 임의신청이 완료되었습니다.".format(player.mention))
        else:
            await message.channel.send("{}님은 이미 신청된 플레이어입니다.".format(player.mention))

@client.command()
async def 신청반려(message):
    global current_game

    if message.channel.id!=channels['내전신청']:
        return
    if current_game is None:
        await message.channel.send("신청중인 내전이 없습니다.")
        return

    opener=author(message)
    if opener!=current_game.opener and (not is_moderator(opener)):
        await message.channel.send("내전 개최자 또는 운영진만 신청반려가 가능합니다.")
        return

    players=message.message.mentions

    for player in players:
        if current_game.remove_player(player):
            await message.channel.send("{}님의 신청반려가 완료되었습니다.".format(player.mention))
        else:
            await message.channel.send("{}님은 신청되지 않은 플레이어입니다.".format(player.mention))

############################################################
#도움말
@client.command()
async def 도움말(ctx):
    embed = discord.Embed(title="Grace bot", description="그레이스 클랜 봇입니다.", color=0xeee657)
    embed.add_field(name="\u200B",value="\u200B",inline=False)
    embed.add_field(name="전체 서버",value="\u200B",inline=False)
    embed.add_field(name="\u200B",value="\u200B",inline=False)
    embed.add_field(name="리그\n",value="한국 오버워치 리그 트위치 링크를 줍니다.\n",inline=False)
    embed.add_field(name="랜덤 (선택1) (선택2) (선택3) ...\n",value="선택지 중 무작위로 하나를 골라줍니다.\n",inline=False)
    embed.add_field(name="쟁탈추첨\n",value="쟁탈 맵 중 하나를 무작위로 골라줍니다.\n",inline=False)
    if ctx.channel.id==channels['내전신청']:
        embed.add_field(name="\u200B",value="\u200B",inline=False)
        embed.add_field(name="내전신청방",value="\u200B",inline=False)
        embed.add_field(name="\u200B",value="\u200B",inline=False)
        embed.add_field(name="내전개최 hh:mm",value="내전을 주어진 시각에 개최합니다. 시각을 주지 않으면 21시로 설정됩니다.\n",inline=False)
        embed.add_field(name="\u200B",value="\u200B",inline=False)
        embed.add_field(name="내전 개최자 및 운영진만 사용 가능한 명령어",value="\u200B",inline=False)
        embed.add_field(name="개최자변경 @사용자\n",value="개최자를 멘션한 사용자로 변경합니다.\n",inline=False)
        embed.add_field(name="시간변경 hh:mm",value="내전의 개최 시각을 해당 시각으로 변경합니다.",inline=False)
        embed.add_field(name="내전종료\n",value="내전을 종료하고, 로그를 기록합니다.\n",inline=False)
        embed.add_field(name="추가신청허용\n",value="추가신청을 허용합니다. 한번 허용하면 이후로 계속 신청이 가능하며, 내전 개최 시점 1시간 이후로는 자동으로 신청이 가능합니다.\n",inline=False)
        embed.add_field(name="임의신청 @사용자1 @사용자2 ...\n",value="멘션한 사용자들을 신청한 것으로 처리합니다.\n",inline=False)
        embed.add_field(name="신청반려 @사용자1 @사용자2 ...\n",value="멘션한 사용자들의 신청을 반려합니다.\n",inline=False)
        embed.add_field(name="\u200B",value="\u200B",inline=False)
        embed.add_field(name="모든 사람이 사용 가능한 명령어",value="\u200B",inline=False)
        embed.add_field(name="내전확인\n",value="현재 내전이 개최중이라면 내전의 정보를 출력합니다.",inline=False)
        embed.add_field(name="목록\n",value="선착순으로, 신청자 목록을 확인합니다.\n",inline=False)
        embed.add_field(name="신청\n",value="본인이 개최된 내전에 신청합니다.\n",inline=False)
        embed.add_field(name="취소\n",value="본인의 내전 신청을 취소합니다.\n",inline=False)
    await ctx.send(embed=embed)

############################################################
#자동 기록(이벤트)
@client.event
async def on_ready():
    print("login")
    print(client.user.name)
    print(client.user.id)
    print("---------------")
    await client.change_presence(activity=discord.Game(name='!', type=1))

@client.event
async def on_message_delete(message):
    if TESTING: return
    author = message.author
    content = message.content
    channel = message.channel
    delchannel = message.server.get_channel('메시지_로그')
    await client.send_message(delchannel, '{} / {}: {}'.format(channel, author, content))

@client.event
async def on_member_join(member):
    if TESTING: return
    fmt = '<@332564579148103691>\n{0.mention}님이 {1.name}에 입장하였습니다.'
    channel = member.server.get_channel('출입_로그')
    await client.send_message(channel, fmt.format(member, member.server))
    #await client.send_message(member, "디스코드 권한 부여 해 드렸고요")
    role = discord.utils.get(member.server.roles, name='외부인')
    await client.add_roles(member, role)

@client.event
async def on_member_remove(member):
    if TESTING: return
    channel = member.server.get_channel('출입_로그')
    fmt = '{0.mention}\n{0.nick}님이 서버에서 나가셨습니다.'
    await client.send_message(channel, fmt.format(member, member.server))


############################################################
#실행
access_token = os.environ["BOT_TOKEN"]
client.run(access_token)