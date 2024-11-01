import asyncio
import json
import time
import random
from colorama import init, Fore, Style
from web3 import Web3
import aiohttp
import argparse

init(autoreset=True)

print(Fore.CYAN + Style.BRIGHT + """███████╗██╗     ██╗  ██╗     ██████╗██╗   ██╗██████╗ ███████╗██████╗ """ + Style.RESET_ALL)
print(Fore.CYAN + Style.BRIGHT + """╚══███╔╝██║     ██║ ██╔╝    ██╔════╝╚██╗ ██╔╝██╔══██╗██╔════╝██╔══██╗""" + Style.RESET_ALL)
print(Fore.CYAN + Style.BRIGHT + """  ███╔╝ ██║     █████╔╝     ██║      ╚████╔╝ ██████╔╝█████╗  ██████╔╝""" + Style.RESET_ALL)
print(Fore.CYAN + Style.BRIGHT + """ ███╔╝  ██║     ██╔═██╗     ██║       ╚██╔╝  ██╔══██╗██╔══╝  ██╔══██╗""" + Style.RESET_ALL)
print(Fore.CYAN + Style.BRIGHT + """███████╗███████╗██║  ██╗    ╚██████╗   ██║   ██████╔╝███████╗██║  ██║""" + Style.RESET_ALL)
print(Fore.CYAN + Style.BRIGHT + """╚══════╝╚══════╝╚═╝  ╚═╝     ╚═════╝   ╚═╝   ╚═════╝ ╚══════╝╚═╝  ╚═╝""" + Style.RESET_ALL)
print(Fore.CYAN + Style.BRIGHT + """    Auto Deposit ETH for HANA Network / Auto Grow and Open Garden    """ + Style.RESET_ALL)
print(Fore.CYAN + Style.BRIGHT + """                t.me/zlkcyber *** github.com/zlkcyber                """ + Style.RESET_ALL)

RPC_URL = "https://mainnet.base.org"
CONTRACT_ADDRESS = "0xC5bf05cD32a14BFfb705Fb37a9d218895187376c"
api_url = "https://hanafuda-backend-app-520478841386.us-central1.run.app/graphql"
AMOUNT_ETH = 0.0000001  # Amount of ETH to be deposited
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

amount_wei = web3.to_wei(AMOUNT_ETH, 'ether')
contract = web3.eth.contract(address=CONTRACT_ADDRESS, abi=json.loads(contract_abi))

nonces = {key: web3.eth.get_transaction_count(web3.eth.account.from_key(key).address) for key in private_keys}

headers = {
    'Accept': '*/*',
    'Content-Type': 'application/json',
    'User-Agent': "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1"
}

async def colay(session, url, method, payload_data=None):
    async with session.request(method, url, headers=headers, json=payload_data) as response:
        if response.status != 200:
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
    new_access_token = await refresh_access_token(session, refresh_token)
    headers['authorization'] = f'Bearer {new_access_token}'

    info_query = {
        "query": "query CurrentUser { currentUser { id sub name iconPath depositCount totalPoint evmAddress { userId address } inviter { id name } } }",
        "operationName": "CurrentUser"
    }
    info = await colay(session, api_url, 'POST', info_query)
    
    balance = info['data']['currentUser']['totalPoint']
    deposit = info['data']['currentUser']['depositCount']

    bet_query = {
        "query": "query GetGardenForCurrentUser { getGardenForCurrentUser { id inviteCode gardenDepositCount gardenStatus { id activeEpoch growActionCount gardenRewardActionCount } gardenMilestoneRewardInfo { id gardenDepositCountWhenLastCalculated lastAcquiredAt createdAt } gardenMembers { id sub name iconPath depositCount } } }",
        "operationName": "GetGardenForCurrentUser"
    }
    profile = await colay(session, api_url, 'POST', bet_query)
    
    grow = profile['data']['getGardenForCurrentUser']['gardenStatus']['growActionCount']
    garden = profile['data']['getGardenForCurrentUser']['gardenStatus']['gardenRewardActionCount']
    print(f"{Fore.GREEN}POINTS: {balance} | Deposit Counts: {deposit} | Grow left: {grow} | Garden left: {garden}{Style.RESET_ALL}")

    while grow > 0:
        action_query = {
            "query": "mutation issueGrowAction { issueGrowAction }",
            "operationName": "issueGrowAction"
        }
        mine = await colay(session, api_url, 'POST', action_query)
        reward = mine['data']['issueGrowAction']
        balance += reward
        grow -= 1
        print(f"{Fore.GREEN}Rewards: {reward} | Balance: {balance} | Grow left: {grow}{Style.RESET_ALL}")
        await asyncio.sleep(1)
        
        commit_query = {
            "query": "mutation commitGrowAction { commitGrowAction }",
            "operationName": "commitGrowAction"
        }
        await colay(session, api_url, 'POST', commit_query)
        

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
        

async def handle_eth_transactions(session, num_transactions):
    global nonces
    for i in range(num_transactions):
        for private_key in private_keys:
            from_address = web3.eth.account.from_key(private_key).address
            short_from_address = from_address[:4] + "..." + from_address[-4:]

            try:
                transaction = contract.functions.depositETH().build_transaction({
                    'from': from_address,
                    'value': amount_wei,
                    'gas': 100000,
                    'gasPrice': web3.eth.gas_price,
                    'nonce': nonces[private_key],
                })

                signed_txn = web3.eth.account.sign_transaction(transaction, private_key=private_key)
                tx_hash = web3.eth.send_raw_transaction(signed_txn.rawTransaction)
                print(f"{Fore.GREEN}Transaction {i + 1} sent from {short_from_address} with hash: {tx_hash.hex()}{Style.RESET_ALL}")

                nonces[private_key] += 1
                await asyncio.sleep(random.randint(5, 11))  # Random delay between 5 to 11 seconds

            except Exception as e:
                if 'nonce too low' in str(e):
                    print(f"{Fore.RED}Nonce too low for {short_from_address}. Fetching the latest nonce...{Style.RESET_ALL}")
                    nonces[private_key] = web3.eth.get_transaction_count(from_address)
                else:
                    print(f"{Fore.RED}Error sending transaction from {short_from_address}: {str(e)}{Style.RESET_ALL}")

async def main(mode, num_transactions=None):
    async with aiohttp.ClientSession() as session:
        if mode == '1':
            if num_transactions is None:
                num_transactions = int(input(Fore.YELLOW + "Enter the number of transactions to be executed: " + Style.RESET_ALL))
            await handle_eth_transactions(session, num_transactions)
        elif mode == '2':
            for token in access_tokens:
                await handle_grow_and_garden(session, token)
                await asyncio.sleep(5)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['1', '2'], help="Select mode: 1 = ETH deposit, 2 = Auto grow and open garden")
    parser.add_argument('--num_transactions', type=int, help="Number of transactions for mode 1")
    args = parser.parse_args()

    try:
        asyncio.run(main(args.mode, args.num_transactions))
    except KeyboardInterrupt:
        print(Fore.RED + "\nProcess interrupted by user. Exiting..." + Style.RESET_ALL)
