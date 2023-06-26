from discord_webhook import DiscordEmbed, DiscordWebhook
import requests
import time as t
import json
import sqlite3
import art
import datetime
import socket 
import sys 

def log(content=str):
    time_now = datetime.datetime.now()
    current_time = time_now.strftime("%H:%M:%S")
    print(f"[{str(current_time)}] {content}")

def getLiveLotteries():
    allLotteriesURL = "https://atom.elixirnft.io/all_essence_lotteries?page_size=50&page=0"
    allLotteriesParam = {
        'time_filter': 'Live'
    }

    allLotteriesResponse = requests.get(url=allLotteriesURL, params=allLotteriesParam)
    if allLotteriesResponse.status_code == 200:
        return json.loads(allLotteriesResponse.text)
    else:
        return "Error while scraping raffles info!"

def checkTimeUntilEnd(endTime=int):
    currentTime = t.time()
    currentTime = int(round(currentTime, 0))
    secondsLeft = endTime - currentTime
    return secondsLeft

def checkIDinList(list, ID):
    for element in list:
        if element == ID:
            return True
        else:
            continue
    return False

def getAmountOfTicketsBought(boostCollectionMint=str, name=str):
    ticketDict = {
        0: f"{name} Ticket",
        1: f"{name} 5 Ticket Pack",
        2: f"{name} 25 Ticket Pack",
        3: f"{name} 50 Ticket Pack",
        4: f"{name} 100 Ticket Pack",
        5: f"{name} 500 Ticket Pack",
        6: f"{name} 1K Ticket Pack",
    }

    ticketMultiplier = {
        0: 1,
        1: 5,
        2: 25,
        3: 50,
        4: 100,
        5: 500,
        6: 1000
    }

    ticketPrice = 5000 # 5k essence per ticket

    url = f"https://atom.elixirnft.io/lottery_tickets/{boostCollectionMint}"
    response = json.loads(requests.get(url=url).text)
    ticketAmount = 0

    for i in range(len(ticketDict)):
        if ticketDict[i] in response:
            ticketAmount += int(response[ticketDict[i]]) * ticketMultiplier[i]

    return ticketAmount, (ticketAmount*ticketPrice)

def convert_number(number):
    suffixes = {
        0: '',
        3: 'K',
        6: 'M',
        9: 'B',
        12: 'T'
    }
    power = max(suffixes.keys(), key=lambda x: x if number >= 10 ** x else float('-inf'))
    suffix = suffixes[power]
    converted_number = number / 10 ** power
    return f'{converted_number:.1f}{suffix}'

def typeIn(file=str, name=str, ID=str):
    conn = sqlite3.connect(file)
    cursor = conn.cursor()

    # Create the table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS data (
            id INTEGER PRIMARY KEY,
            name TEXT,
            ID TEXT UNIQUE
        )
    ''')

    # Insert data into the table, ignoring if it violates the unique constraint
    cursor.execute('''
        INSERT OR IGNORE INTO data (name, ID)
        VALUES (?, ?)
    ''', (name, ID))
    conn.commit()
    conn.close()


def retrieveFrom(file=str):
    conn = sqlite3.connect(file)
    cursor = conn.cursor()

    # Create the table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS data (
            id INTEGER PRIMARY KEY,
            name TEXT,
            unique_id TEXT
        )
    ''')

    cursor.execute('SELECT * FROM data')
    rows = cursor.fetchall()

    my_list = []
    for row in rows:
        my_list.append(row[0])

    conn.close()
    return my_list

def createEmbed(ticketsBought=None, essenceSpent=None, chancesPer100tickets=None, name=str, description=str, winnersAmount=str, endTime=int, identifier=str, image=str, option=int):
    if option == 1:
        embed = DiscordEmbed(title=f"**{name} auction ends soon!**", description=description, color="804df6")
    elif option == 2:
        embed = DiscordEmbed(title=f"**New auction: {name}**", description=description, color="804df6")
    
    embed.set_image(image)
    embed.set_footer(text="Powered by Elixir", icon_url="https://i.imgur.com/xnbsZaz.png")
        
    if ticketsBought is not None:
        cTicketsBought = convert_number(ticketsBought)
        embed.add_embed_field("Tickets \nBought", cTicketsBought)
        
    if essenceSpent is not None:
        cEssenceSpent = convert_number(essenceSpent)
        embed.add_embed_field("Essence \nSpent", cEssenceSpent)
        
    if chancesPer100tickets is not None:
        embed.add_embed_field("Chances per \n100 Tickets", f"{str(chancesPer100tickets)}%")
        
    embed.add_embed_field("Winners \nAmount", winnersAmount)
    embed.add_embed_field("Ends", f"<t:{endTime}:R>")
    embed.add_embed_field("Link to the \nraffle", f"[{name}](https://app.elixirnft.io/essence/{identifier})")
        
    return embed

def sendWebhook(embed=DiscordEmbed, url=str):
    allowed_mentions = {
        "roles": ["1122144134132678687"] # @Essence Hub
    }
    webhook = DiscordWebhook(url=url, content="<@&1122144134132678687>", allowed_mentions=allowed_mentions)
    webhook.add_embed(embed=embed)
    webhook.execute()



def scrape_lotteries():
    webhookURL = "https://discord.com/api/webhooks/1122900247266463865/cJ2pxNG-oOOmVyIoaE9h1uCdM23MA7UXQdSEk3Fh0PM0w1kpxQxwnND7rDa4vVmFWxtK" # Webhook link
    database = 'elixir.db'
    database2 = 'elixirv2.db'

    usedIDs = retrieveFrom(file=database2)
    existingRafflesNames = retrieveFrom(file=database)
    # print(existingRafflesNames)
    liveLotteries = getLiveLotteries() # Scraping live lotteries
    # print(liveLotteries)
    amountOfLotteries = int(liveLotteries['total']) # From live lotteries scraping amount of them

    # Checking for raffles that end in less than 3h
    for raffleNumber in reversed(range(amountOfLotteries)): # Iteration through all lotteries in reversed order (from the oldest)
        print(raffleNumber)
        try:
            existingRafflesNames = retrieveFrom(file=database)
            usedIDs = retrieveFrom(file=database2)
        except:
            with Exception as e:
                print(f"An error occured while retrieving info from database, error: {e}")

        try:

            info = liveLotteries['lotteries'][raffleNumber]

            ID = int(info['id']) # Getting ID of certain raffle
            endTime = int(info['endTime']) # Getting time at which certain raffle ends
            timeUntilEnd = checkTimeUntilEnd(endTime=endTime)

            name = str(info['name'])
            raffleDescription = str(info['description'])
            winnersAmount = str(info['numWinners'])
            raffleIdentifier = str(info['identifier'])
            raffleImage = str(info['image'])

            boostCollectionMint = str(info['boostCollectionMint'])
            discordRequired = str(info['discordRequired'])

            boughtTickets = getAmountOfTicketsBought(boostCollectionMint=boostCollectionMint, name=name)
            ticketsBought = boughtTickets[0]
            essenceSpent = boughtTickets[1]
            chancesPer100tickets = round((1000 / ticketsBought), 4)

        except:
            with Exception as e:
                print(f"An error occured while creating variables needed for embed, error: {e}")\

        try:
            # Setting up embed
            embed = createEmbed(
                name=name, 
                description=raffleDescription, 
                winnersAmount=winnersAmount, 
                endTime=endTime, 
                identifier=raffleIdentifier, 
                image=raffleImage, 
                ticketsBought=ticketsBought, 
                essenceSpent=essenceSpent, 
                chancesPer100tickets=chancesPer100tickets,
                option=1
                )
        except:
            with Exception as e:
                log(f"An error occured while setting embed up, error: {e}")

        if timeUntilEnd < 1090000 and timeUntilEnd > 0 and checkIDinList(usedIDs, ID) == False: # Checks if raffle ends in less than 3hours and if it was already reminded
            try:
                # Sending webhook
                sendWebhook(url=webhookURL, embed=embed)
                log(f"Reminder for {name} auction sent successfully")
            except:
                with Exception as e:
                    log(f"An error occured while sending webhook, error: {e}")

            try:
                # Typing in ID into database so webhook with same auction won't be sent again
                typeIn(file=database2, name=name, ID=ID)
            except:
                with Exception as e:
                    log(f"An error occured while typing data into database, error: {e}")

    if str(liveLotteries['lotteries'][0]['name']) not in existingRafflesNames:
        try:
            info = liveLotteries['lotteries'][0]

            name = str(info['name'])
            raffleDescription = str(info['description'])
            winnersAmount = str(info['numWinners'])
            endTime = int(info['endTime'])
            raffleIdentifier = str(info['identifier'])
            raffleImage = str(info['image'])

            # Creating embed
            embed = createEmbed(
                name=name, 
                description=raffleDescription, 
                winnersAmount=winnersAmount, 
                endTime=endTime, 
                identifier=raffleIdentifier, 
                image=raffleImage,
                option=2
                )
            
            # Sending webhook
            sendWebhook(
                url=webhookURL,
                embed=embed
            )

            # Store ID in database
            ID = int(info['id']) 
            typeIn(
                file=database, 
                name=name, 
                ID=int(liveLotteries['lotteries'][0]['id'])
                )
            
            log('New auction webhook sent successfully!')

        except:
            with Exception as e:
                log(f"An error occured while sending webhook with new raffle, error: {e}")

if __name__ == '__main__': 
    # your code here 
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
    server_address = ('', 8080) 
    server_socket.bind(server_address) 

    server_socket.listen()

    while True:
        client_socket, addr = server_socket.accept() 
        scrape_lotteries()
        client_socket.close() 