import discord
import asyncio
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import random
import openpyxl


client = discord.Client()

scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name("Grace-defe42f05ec3.json", scope)
auth = gspread.authorize(creds)
spreadsheet = auth.open("Grace2").sheet1

@client.event
async def on_ready():
    print("login")
    print(client.user.name)
    print(client.user.id)
    print("---------------")
    await client.change_presence(activity=discord.Game(name='>>', type=1))

@client.event
async def on_message(message):
    author = message.author
    content = message.content
    channel = message.channel
    print('{} / {}: {}'.format(channel, author, content))

    if message.content.startswith(">>"):
        author = message.content
        author = author.split(">>")
        author = author[1]

        if spreadsheet.find(author) is False:
            return False
        cell = spreadsheet.find(author)
        row = cell.row

        battletag = spreadsheet.cell(row, 2).value
        link = spreadsheet.cell(row, 4).value
        description = spreadsheet.cell(row, 5).value
        role = spreadsheet.cell(row, 6).value
        imagelink = spreadsheet.cell(row, 7).value
        thumbnaillink = spreadsheet.cell(row, 8).value
        arena = spreadsheet.cell(row, 9).value


        if spreadsheet.cell(row, 6).value == "클랜마스터":
            roleimage = ":pen_ballpoint:"
        elif spreadsheet.cell(row, 6).value == "운영진":
            roleimage = ":construction_worker:"
        elif spreadsheet.cell(row, 6).value == "클랜원":
            roleimage = ":boy:"
        elif spreadsheet.cell(row, 6).value == "신입클랜원":
            roleimage = ""

        if link is "X":
            embed = discord.Embed(title="한줄소개", description=description, color=0x5c0bb7)
        elif link is not None:
            embed = discord.Embed(title="바로가기", url=link, description=description, color=0x5c0bb7)

        embed.set_image(url=imagelink)
        embed.set_thumbnail(url=thumbnaillink)
        embed.set_author(name=battletag)
        embed.add_field(name="직책", value=roleimage + role, inline=True)
        embed.add_field(name="Grace Arena", value=":trophy: 제 " + arena + "회 우승", inline=True)

        await channel.send(embed=embed)

    if message.content == '!안녕':
        await channel.send("안녕하세요")

    if message.content == '>>리그':
        await channel.send("https://www.twitch.tv/overwatchleague_kr")

    if message.content.startswith('>>골라'):
        choice = message.content.split(" ")
        choicenumber = random.randint(1, len(choice) - 1)
        choiceresult = choice[choicenumber]
        await channel.send("||" + choiceresult + "||")

    if message.content.startswith('>>쟁탈추첨'):
        food = "리장 타워/일리오스/오아시스/부산/네팔"
        foodchoice = food.split("/")
        foodnumber = random.randint(1, len(foodchoice))
        foodresult = foodchoice[foodnumber - 1]
        await channel.send(foodresult)

    if message.content.startswith('>>배그맵추첨'):
        pubg = "에란겔/미라마/사녹/비켄디"
        pubgchoice = pubg.split("/")
        pubgnumber = random.randint(1, len(pubgchoice))
        pubgresult = pubgchoice[pubgnumber - 1]
        await channel.send(pubgresult)

    if message.content.startswith('!메모장쓰기'):
        file = open("디스코드봇메모장.txt", "w")
        file.write("안녕하세요")
        file.close()

    if message.content.startswith('!메모장읽기'):
        file = open("디스코드봇메모장.txt")
        await channel.send(file.read())
        file.close()

    if message.content.startswith('!학습'):
        file = openpyxl.load_workbook("기억.xlsx")
        sheet = file.active
        learn = message.content.split(" ")
        for i in range(1, 51):
            if sheet["A" + str(i)].value == "-" or sheet["A" + str(i)].value == learn[1]:
                sheet["A" + str(i)].value = learn[1]
                sheet["B" + str(i)].value = learn[2]
                await channel.send("단어가 학습되었습니다.")
                break
        file.save("기억.xlsx")

    if message.content.startswith('!기억') and not message.content.startswith('!기억삭제'):
        file = openpyxl.load_workbook("기억.xlsx")
        sheet = file.active
        memory = message.content.split(" ")
        for i in range(1, 51):
            if sheet["A" + str(i)].value == memory[1]:
                await channel.send(sheet["B" + str(i)].value)
                break

    if message.content.startswith('!기억삭제'):
        file = openpyxl.load_workbook("기억.xlsx")
        sheet = file.active
        memory = message.content.split(" ")
        for i in range(1, 51):
            if sheet["A" + str(i)].value == str(memory[1]):
                sheet["A" + str(i)].value = "-"
                sheet["B" + str(i)].value = "-"
                await channel.send("기억이 삭제되었습니다.")
                file.save("기억.xlsx")
                break

    if message.content.startswith('!팀나누기'):
        team = message.content[6:]
        peopleteam = team.split("/")
        people = peopleteam[0]
        team = peopleteam[1]
        person = people.split(" ")
        teamname = team.split(" ")
        random.shuffle(teamname)
        for i in range(0, len(person)):
            await channel.send(person[i] + "---->" + teamname[i])

@client.event
async def on_message_delete(message):
    author = message.author
    content = message.clean_content
    channel = message.channel
    delchannel = message.guild.get_channel(527859699702562828)
    await delchannel.send('{} / {}: {}'.format(channel, author, content))

@client.event
async def on_member_join(member):
    fmt = '<@332564579148103691>\n{0.mention}님이 {1.name}에 입장하였습니다.'
    channel = member.guild.get_channel(516122942896078868)
    role = member.guild.get_role(510731224654938112)
    await member.add_roles(role)
    await channel.send(fmt.format(member, member.guild))

@client.event
async def on_member_remove(member):
    channel = member.guild.get_channel(516122942896078868)
    fmt = '{0.mention}\n{0.nick}님이 서버에서 나가셨습니다.'
    await channel.send(fmt.format(member, member.guild))


access_token = os.environ["BOT_TOKEN"]
client.run(access_token)
