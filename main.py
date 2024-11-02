import asyncio
import json
import time
from colorama import init, Fore, Style
from web3 import Web3
import aiohttp
import argparse
from utils.banner import banner 
init(autoreset=True)

print(Fore.CYAN + Style.BRIGHT + banner + Style.RESET_ALL)

RPC_URL = "https://mainnet.base.org"
CONTRACT_ADDRESS = "0xC5bf05cD32a14BFfb705Fb37a9d218895187376c"
api_url = "https://hanafuda-backend-app-520478841386.us-central1.run.app/graphql"
AMOUNT_ETH = 0.0000000001
web3 = Web3(Web3.HTTPProvider(RPC_URL))

with open("pvkey.txt", "r") as file:
    private_keys = [line.strip() for line in file if line.strip()]

with open("token.txt", "r") as file:
    access_tokens = [line.strip() for line in file if line.strip()]

contract_abi = '''
[
    {
        "constant": false,
        "inputs": [],
        "name": "depositETH",
        "outputs": [],
        "stateMutability": "payable",
        "type": "function"
    }
]
'''

headers = {
    'Accept': '*/*',
    'Content-Type': 'application/json',
    'User-Agent': "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1"
}

async def colay(session, url, method, payload_data=None):
    async with session.request(method, url, headers=headers, json=payload_data) as response:
        if response.status == 429:
            raise Exception('HTTP error 429: Rate Limit Exceeded')
        elif response.status != 200:
            raise Exception(f'HTTP error! Status: {response.status}')
        return await response.json()

async def refresh_access_token(session, refresh_token):
    api_key = "AIzaSyDipzN0VRfTPnMGhQ5PSzO27Cxm3DohJGY"  
    async with session.post(
        f'https://securetoken.googleapis.com/v1/token?key={api_key}',
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data=f'grant_type=refresh_token&refresh_token={refresh_token}'
    ) as response:
        if response.status != 200:
            raise Exception("Failed to refresh access token")
        data = await response.json()
        return data.get('access_token')

async def handle_grow_and_garden(session, refresh_token):  
    while True:
        try:
            new_access_token = await refresh_access_token(session, refresh_token)
            headers['authorization'] = f'Bearer {new_access_token}'

            info_query = {
                "query": "query getCurrentUser { "
                            "currentUser { id totalPoint depositCount } "
                            "getGardenForCurrentUser { "
                            "gardenStatus { growActionCount gardenRewardActionCount } "
                            "} "
                            "}",
                "operationName": "getCurrentUser"
            }
            info = await colay(session, api_url, 'POST', info_query)
            
            balance = info['data']['currentUser']['totalPoint']
            deposit = info['data']['currentUser']['depositCount']
            grow = info['data']['getGardenForCurrentUser']['gardenStatus']['growActionCount']
            garden = info['data']['getGardenForCurrentUser']['gardenStatus']['gardenRewardActionCount']

            print(f"{Fore.GREEN}POINTS: {balance} | Deposit Counts: {deposit} | Grow left: {grow} | Garden left: {garden}{Style.RESET_ALL}")

            async def grow_action():
                action_query = {
                    "query": "mutation issueGrowAction { issueGrowAction commitGrowAction }",
                    "operationName": "issueGrowAction"
                }
                                
                try:
                    mine = await colay(session, api_url, 'POST', action_query)            
                    
                    if mine and 'data' in mine and 'issueGrowAction' in mine['data']:
                        reward = mine['data']['issueGrowAction']
                        return reward
                    else:
                        print(f"{Fore.RED}Error: Unexpected response format: {mine}{Style.RESET_ALL}")
                        return 0  
                except Exception as e:
                    return 0

            while grow > 0:

                grow_count = min(grow, 10)
                tasks = [grow_action() for _ in range(grow_count)]
                results = await asyncio.gather(*tasks)

                for reward in results:
                    if reward != 0:
                        balance += reward
                        grow -= 1
                        print(f"{Fore.GREEN}Rewards: {reward} | Balance: {balance} | Grow left: {grow}{Style.RESET_ALL}")
            
            while garden >= 10:
                garden_action_query = {
                    "query": "mutation executeGardenRewardAction($limit: Int!) { executeGardenRewardAction(limit: $limit) { data { cardId group } isNew } }",
                    "variables": {"limit": 10},
                    "operationName": "executeGardenRewardAction"
                }
                mine_garden = await colay(session, api_url, 'POST', garden_action_query)
                card_ids = [item['data']['cardId'] for item in mine_garden['data']['executeGardenRewardAction']]
                print(f"{Fore.GREEN}Opened Garden: {card_ids}{Style.RESET_ALL}")
                garden -= 10
            break

        except Exception as e:
            if 'HTTP error 429' in str(e):
                print(f"{Fore.RED}Rate limit exceeded. Retrying in 11 minutes...{Style.RESET_ALL}")
                await asyncio.sleep(660)  # 660 ثانیه معادل 11 دقیقه
            else:
                print(f"{Fore.RED}An unexpected error occurred: {str(e)}{Style.RESET_ALL}")
                break

async def main(mode, num_transactions=None):
    async with aiohttp.ClientSession() as session:
        if mode == '1':
            if num_transactions is None:
                num_transactions = int(input(Fore.YELLOW + "Enter the number of transactions to be executed: " + Style.RESET_ALL))
            await handle_eth_transactions(session, num_transactions)
        elif mode == '2':
            while True:  
                for refresh_token in access_tokens:
                    await handle_grow_and_garden(session, refresh_token)  
                print(f"{Fore.RED}All accounts have been processed. Cooling down for 11 minutes...{Style.RESET_ALL}")
                time.sleep(660)  
        else:
            print(Fore.RED + "Invalid option. Please choose either 1 or 2." + Style.RESET_ALL)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Choose the mode of operation.')
    parser.add_argument('-a', '--action', choices=['1', '2'], help='1: Execute Transactions, 2: Grow and Garden')
    parser.add_argument('-tx', '--transactions', type=int, help='Number of transactions to execute (optional for action 1)')

    args = parser.parse_args()

    if args.action is None:
        args.action = input(Fore.YELLOW + "Choose action (1: Execute Transactions, 2: Grow and Garden): " + Style.RESET_ALL)
        while args.action not in ['1', '2']:
            print(Fore.RED + "Invalid choice. Please select either 1 or 2." + Style.RESET_ALL)
            args.action = input(Fore.YELLOW + "Choose action (1: Execute Transactions, 2: Grow and Garden): " + Style.RESET_ALL)
   
    asyncio.run(main(args.action, args.transactions))
