# -*- coding: utf-8 -*-
"""
Based on:
Cryptocheck
Copyright (C) 2017 tsts
"""

import csv
import sys
import json
import requests

names = {
    'BCH':'Bitcoin Cash',
    'BTC':'Bitcoin',
    'BCC':'BitConnect',
    'DASH':'Dash',
    'DOGE':'Dogecoin',
    'ETC':'Ethereum Classic',
    'ETH':'Ethereum',
    'ICE':'iDice Ethereum token',
    'LTC':'Litecoin',
    'MIOTA':'IOTA',
    'NEO':'NEO',
    'XEM':'NEM',
    'OMG':'OmiseGo',
    'QTUM':'Qtum',
    'XRP':'Ripple',
    'ZEC':'Zcash',
    'XMR':'Monero'
}

MIN_BITCOIN_PORTFOLIO = 0.75
ACTION_DIFF = 0.02

def __main__():
    if len(sys.argv) < 2:
        print("Usage: %s [addresses.json]" % sys.argv[0])
        sys.exit(1)
    
    with open(sys.argv[1]) as f:
        my_addresses = json.loads(f.read())
    
    coins_exchange_data = get_coin_exchange()

    per_coin_balance = {}
    for my_address in my_addresses:
        retries = 0
        while retries < 4:
            try:
                if 'coins' in my_address:
                    balance_coins = my_address['coins']
                else:
                    balance_coins = check_balance(my_address['coin'], my_address['address'])

                balance = {
                            'coins': balance_coins,
                            'brl': balance_coins * float(coins_exchange_data[my_address['coin']]['price_brl']),
                            'usd': balance_coins * float(coins_exchange_data[my_address['coin']]['price_usd']),
                            'btc': balance_coins * float(coins_exchange_data[my_address['coin']]['price_btc']),
                        }

                #merge dicts summing
                cur_coin_balance = per_coin_balance.get(my_address['coin'], {})
                per_coin_balance[my_address['coin']] = { k: balance.get(k, 0) + cur_coin_balance.get(k, 0) for k in set(balance) | set(cur_coin_balance) }

                print(my_address, balance)
                break
            except KeyboardInterrupt:
                raise
            except:
                print("retrying %s" % my_address)
                retries += 1

    sums = { k: sum([v[k] for v in [per_coin_balance[coin] for coin in per_coin_balance.keys()]]) for k in ('brl', 'usd', 'btc') }

    topCoins = getTopCoins(list(per_coin_balance.keys()))
    sum_normalized_marketcap = sum([coin['marketcap'] for coin in topCoins])

    print()
    print()
    print(per_coin_balance)
    print()
    print(sums)
    print()
    print()
    print("current portfolio:")
    print("rank, coin, marketCap%, 24h-volume%, portfolio%, portfolio$, portfolio_coins, diff%")
    btc_marketcap_percentage = 0
    for coin in topCoins:
        coin['marketcap'] = coin['marketcap'] / sum_normalized_marketcap
        coin['portfolio_usd'] = per_coin_balance.get(coin['coin'], {}).get('usd', 0)
        coin['portfolio_coins'] = per_coin_balance.get(coin['coin'], {}).get('coins', 0)
        coin['portfolio%'] = coin['portfolio_usd'] / sums['usd']

        if coin['coin'] == 'BTC':
            btc_original_marketcap_percentage = coin['marketcap']
            btc_goal_marketcap_percentage = max(coin['marketcap'], MIN_BITCOIN_PORTFOLIO)
            coin['portfolio_goal%'] = btc_goal_marketcap_percentage

    for coin in topCoins:
        if coin['coin'] != 'BTC':
            coin['portfolio_goal%'] = coin['marketcap'] * ((1-btc_goal_marketcap_percentage)/(1-btc_original_marketcap_percentage))

        coin['%_diff'] = coin['portfolio_goal%'] - coin['portfolio%'] 
        coin['action'] = (abs(coin['%_diff']) > ACTION_DIFF)

    #topCoins = [{ k: ('%.2f' % coin[k]) if isinstance(coin[k], float) else coin[k] for k in coin.keys() } for coin in topCoins]

    for coin in topCoins:
        print(coin)

    cw = csv.DictWriter(sys.stdout, topCoins[0].keys())
    cw.writeheader()
    cw.writerows(topCoins)

    print()
    print()
    print("suggested operations")
    print()
    print()
    print("final portfolio")
    print()
    print("link pra monthly volume: https://coinmarketcap.com/currencies/volume/monthly/")
    print()


def get_coin_exchange():
    coins_exchange_data = {}

    response = requests.get('https://api.coinmarketcap.com/v1/ticker/?convert=BRL', timeout = 5)
    data = response.json()

    for coin in data:
        if coin['symbol'] in names:
            coins_exchange_data[coin['symbol']] = coin

    return coins_exchange_data
    


def check_balance(coin, add):
    if coin == 'BCC':
        site = 'https://www.blockexperts.com/api?coin=bcc&action=getbalance&address='+add
        hdr = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
           'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
           'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
           'Accept-Encoding': 'none',
           'Accept-Language': 'en-US,en;q=0.8',
           'Connection': 'keep-alive'}                   
        response = requests.get(site, headers=hdr, timeout = 5)            
        html = response.text
        return float(html)
    elif coin == 'BCH':
        response = requests.get('https://api.blocktrail.com/v1/BCC/address/'+add+'?api_key=MY_APIKEY', timeout = 5)
        return response.json()['balance']/1e8
    elif coin == 'BTC': 
        #response = urllib2.urlopen('https://blockchain.info/q/addressbalance/'+add, timeout = 5)
        site = 'https://blockexplorer.com/api/addr/'+add+'/balance'
        hdr = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
           'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
           'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
           'Accept-Encoding': 'none',
           'Accept-Language': 'en-US,en;q=0.8',
           'Connection': 'keep-alive'}                   
        response = requests.get(site, headers=hdr, timeout = 5)
        html = response.text
        return int(html)/1e8
    elif  coin == 'ETC': 
        response = requests.get('https://etcchain.com/api/v1/getAddressBalance?address='+add, timeout = 5)
        return response.json()['balance']
    elif  coin == 'ETH': 
        response = requests.get('https://api.etherscan.io/api?module=account&action=balance&address='+add+'&tag=latest&apikey=NA23E58FGS35PG5UV2IZI3DKGVWFSXW5GV', timeout = 5)
        return int(response.json()['result'])/1e18
    elif coin == 'MIOTA':            
        data = {'command':'getBalances','addresses':[add],'threshold':100}
        headers = {'content-type': 'application/json'} 
        request = requests.get("http://service.iotasupport.com:14265", data=data, headers=headers, timeout = 5)
        return float(requests.json()['balances'][0])
    elif coin == 'NEO':
        #response = urllib2.urlopen('https://api.neonwallet.com/v1/address/balance/'+add, timeout = 5)
        response = requests.get('http://antchain.org/api/v1/address/get_value/'+add, timeout = 5)
        html = response.read()            
        #return int(json.loads(html)['NEO']['balance'])
        return int(response.json()['asset'][0]['value'])
    elif (coin == 'DASH') or (coin == 'LTC') or (coin == 'DOGE'):
        response = requests.get('https://api.blockcypher.com/v1/'+coin.lower()+'/main/addrs/'+add+'/balance', timeout = 5)
        return int(response.json()['balance'])/1e8
    elif coin == 'XRP':
        response = requests.get('https://data.ripple.com/v2/accounts/'+add+'/balances', timeout = 5)
        return float(response.json()['balances'][0]['value'])
    elif coin == 'XEM':
        response = requests.get('http://78.47.64.35:7890/account/get?address='+add, timeout = 5)
        return int(response.json()['account']['balance'])/1e6
    elif coin == 'ZEC':
        site = 'https://api.zcha.in/v2/mainnet/accounts/'+add    
        hdr = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
           'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
           'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
           'Accept-Encoding': 'none',
           'Accept-Language': 'en-US,en;q=0.8',
           'Connection': 'keep-alive'}
        response = requests.get(site, headers=hdr, timeout = 5)
        return response.json()['balance']
    else:
        raise ValueError("invalid coin")

def getTopCoins(my_coins):
    r = requests.get('https://api.coinmarketcap.com/v1/ticker/')
    assert r.status_code == 200
     
    j = r.json()
     
    totalMarketCap = sum([float(v['market_cap_usd']) for v in j])
    totalVolume = sum([float(v['24h_volume_usd']) for v in j])
     
    idToDataMap = {}
    for v in j:
      idToDataMap[v['symbol']] = {'symbol': v['symbol'], 'rank': int(v['rank']), 'price_usd': float(v['price_usd']), 'market_cap_usd': float(v['market_cap_usd']), '24h_volume_usd': float(v['24h_volume_usd'])}
     
    topByMarketCap = sorted(idToDataMap.keys(), key=lambda k: idToDataMap[k]['market_cap_usd'], reverse=True)[:10]
    topByVolume = sorted(idToDataMap.keys(), key=lambda k: idToDataMap[k]['24h_volume_usd'], reverse=True)[:10]
     
    tops = { v for v in set(topByMarketCap + topByVolume + my_coins) }
     
    topsSorted = sorted(tops, key=lambda v: idToDataMap[v]['market_cap_usd'], reverse=True)
     
    coinRank = []
    for top in topsSorted:
      coin = idToDataMap[top]
      coinRank.append({
            'rank': coin['rank'],
            'coin': coin['symbol'],
            'usd': coin['price_usd'],
            'marketcap': coin['market_cap_usd']/totalMarketCap,
            #'24hvol': coin['24h_volume_usd']/totalVolume,
          })

    return coinRank


__main__()

