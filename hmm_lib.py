from hmmlearn import hmm
import numpy as np
import sys
import warnings
from itertools import combinations 
warnings.filterwarnings('ignore')

def loadFile(name):
    listX = []
    list_price = []
    f=open("./txt-files/{}.txt".format(name), 'r')
    f1 = f.readlines()

    last_price = None
    last_volume = None
    for line in f1:
        info = line.split()
        price_str = info[1]
        price_str = price_str.replace(',', '.')
        price = int(price_str) / 100
        volume = int(info[2])
        if last_price == None:
            rate = 0
        else:
            rate = price / last_price - 1
            
        if last_volume == None:
            volume_rate = 0
        else:
            volume_rate = volume / last_volume - 1
        listX.append([rate * 100, volume_rate * 100])
        list_price.append(price)
        last_price = price
        last_volume = volume

    print("file loaded, length:{}".format(len(listX)))    
    return (list_price, listX)
    
    
def nomalization():
  price_rate_list = [item[0] for item in listX]
  volume_rate_list = [item[1] for item in listX]

  mean = stats.mean(price_rate_list)
  stddev = stats.stdev(price_rate_list)
  norm_price_rate_list = [(i - mean) / stddev for i in price_rate_list]

  mean = stats.mean(volume_rate_list)
  stddev = stats.stdev(volume_rate_list)
  norm_volume_rate_list = [(i - mean) / stddev for i in volume_rate_list]

  listX = []
  listX = [[norm_price_rate_list[i], norm_volume_rate_list[i]] for i in range(len(norm_price_rate_list))]
  #listX = [[norm_price_rate_list[i]] for i in range(len(norm_price_rate_list))]

def findCombinations(state_list, num_buy_states, num_sell_states):
    length = len(state_list)
    comb_buy = combinations(state_list, num_buy_states)
    comb_list = []
    for buy_list in list(comb_buy):
        tmp_list = state_list.copy()
        for state in buy_list:
            tmp_list.remove(state)
        comb_sell = combinations(tmp_list, num_sell_states)
        for sell_list in comb_sell:
            #print("buy_list: {}, sell_list: {}".format(buy_list, sell_list))
            comb_list.append([list(buy_list), list(sell_list)])
    return comb_list

def findAllComb(num_components):
    state_list = list(range(num_components))
    length = len(state_list)
    output = []
    for num_buy in range(length):
        for num_sell in range(length):
            comb_list = findCombinations(state_list, num_buy, num_sell)
            output.extend(comb_list)
    return output

def trade(money, stocks, price, op, trade_fee_rate):
    if op == "buy":
      stocks_inc = int(money / (price))
      money_spent = stocks_inc * price
      trade_fee = trade_fee_rate * money_spent
      stocks += stocks_inc
      money = money - stocks_inc * price - trade_fee
    elif op == "sell":
      trafe_fee = stocks * price * trade_fee_rate
      money = money + stocks * price - trafe_fee
      stocks = 0
    return money, stocks

def getAsset(money, stocks, price):
  return money + stocks * price

def tradeForToday(money, stocks, state, buy_list, sell_list, price, trade_fee_rate=0.001, detail = True):
    op = None
    if state in buy_list and money > price:
        # we buy in
        money, stocks = trade(money, stocks, price, "buy", trade_fee_rate)
        if detail == True:
            print("buy in:  state: {}, price: {}, current stocks:{}, current money:{}, asset:{}".format(state, price, stocks, money, getAsset(money, stocks, price)))
            op = "buy"
    elif state in sell_list and stocks > 0:
        # we sell out
        money, stocks = trade(money, stocks, price, "sell", trade_fee_rate)
        if detail == True:
            print("sell out: state: {}, price: {}, current stocks:{}, current money:{}, asset:{}".format(state, price, stocks, money, getAsset(money, stocks, price)))
            op = "sell"
    return (money, stocks, op)

def get_verify_price_change_list(price_seq, today, num_days, num_segs):
    price_change_list = []
    start = today - num_days * num_segs
    end = start + num_days
    for i in range(num_segs):
        price_change_list.append(price_seq[end] / price_seq[start] - 1)
        start += num_days
        end += num_days
    return price_change_list

def get_asset_multi_segs(buy_list, sell_list, price_seq, state_seq, today, num_days, num_segs, trade_fee_rate):
    asset_list = []
    start = today - num_days * num_segs
    end = start + num_days
    for i in range(num_segs):
        asset = check_profit(buy_list, sell_list, price_seq[start:end], 
                                   state_seq[start:end], trade_fee_rate)
        asset_list.append(asset) 
        start += num_days
        end += num_days
        
    return asset_list

def get_asset_whole_timeline(buy_list, sell_list, price_seq, state_seq, today):
    total_asset = check_profit(buy_list, sell_list, price_seq[:today], 
                                   state_seq[:today])
    return total_asset

def get_price_change_rate_multi_segs(price_seq, today, num_days, num_segs):
    price_change_rate_list = []
    start = today - num_days * num_segs
    end = start + num_days

    for i in range(num_segs):
        price_change_rate = price_seq[end] / price_seq[start] - 1
        price_change_rate_list.append(price_change_rate) 
        start += num_days
        end += num_days
    return price_change_rate_list

def get_price_change_rate_whole_timeline(price_seq, today):
    return price_seq[today] / price_seq[0] - 1

def get_weighted_avg(input_list):
    n = len(input_list)
    s = 0
    m = 0
    for i in range(n):
        s += input_list[i] * (i + 1)
        m += (i + 1)
    return s/m

def is_all_elem_bigger_than(list_input, num):
    for item in list_input:
        if item <= num:
            return False
    return True

def get_diff_list(input_list):
    length = len(input_list)
    output = []
    for i in range(length):
        if i == 0:
            continue
        output.append(input_list[i] - input_list[i - 1])
    return output


def compute_ema(input_list, days):

    length = len(input_list)
    output_list = [] 
    multiplier = (2 / (days + 1))
    for i in range(length):
        if i == 0:
            output_list.append(input_list[0])
        else:
            output_list.append((input_list[i] - output_list[i - 1]) * multiplier + output_list[i - 1])
    return output_list

def get_diff_wavg(input_list):
    list_diff = get_diff_list(input_list)
    list_diff_wavg = get_weighted_avg(list_diff)
    return list_diff_wavg

# find out the best way 
# TODO: update the model
def check_profit(buy_list, sell_list, price_seq, state_seq, trade_fee_rate):
    #print("start to check: sell_list:{}, buy_list:{}, price change:{}".format(sell_list, buy_list, 
    #                                                                          price_seq[-1] / price_seq[0] - 1 ))
    money = 10000
    stocks = 0

    for i in range(len(state_seq)):
        money, stocks, op = tradeForToday(money, stocks, state_seq[i], buy_list, sell_list, price_seq[i], trade_fee_rate, False)

    total_asset =  stocks * price_seq[-1] + money
    #print("finished: current stocks:{}, current money:{}, total asset: {}".format(stocks, money, total_asset))
    return total_asset / 10000 - 1

def getProfit(asset, origin_asset):
    return asset / origin_asset - 1

def getHmmModel(n_components, n_iter, random_state):
    return hmm.GaussianHMM(n_components=n_components, n_iter=1000, random_state = 140)

# profit_test_day_list - till example: [10,5,0], means we need to calculate the profit for 0, 5, 10 days ago.
# price_moving_average_day_list - for example [5, 10, 20] means we need to calculate the MA5, MA10 and MA20


def getCombineList(n_components, price_list, state_list, trade_days, profit_test_day_list, price_ema_day_list, trade_fee_rate):
  comb = findAllComb(n_components)
  price_ema_day_list = [ compute_ema(price_list, i)[-1] for i in price_ema_day_list]
  return_list = []
  for item in comb:
      #print(item)
      buy_list = item[0]
      sell_list = item[1]
      profit_list = [ check_profit(buy_list, sell_list, price_list[-i-trade_days-1:-i-1], state_list[-i-trade_days-1:-i-1], trade_fee_rate) for i in profit_test_day_list]

      return_list.append([buy_list, sell_list, price_ema_day_list, profit_list])

  return return_list

def findPolicy(n_components,list_price, state_list, today, policy_days, policy_segs, min_avg_profit, trade_fee_rate, tryit=False):
    buy_list = []
    sell_list = []
    optimized_buy_list = None
    optimized_sell_list = None
    max_asset_wavg = 10000
    max_profit_wavg = 0
    start_day = today - policy_days * policy_segs
    max_profit_list = None
    max_profit_diff_wavg = None
    comb = findAllComb(n_components)
    for i in comb:
        buy_list = i[0]
        sell_list = i[1]
        # find profits for multiple time segments
        # the last element is the profit for entire time.
        # the date is today
        #check_profit_multi_segs(buy_list, sell_list, price_seq, state_seq, today, num_days, num_segs):
        # get the profit for current, 5 days ago, 10 days ago.
        asset_list = get_asset_multi_segs(buy_list, sell_list, list_price, state_list, today, policy_days, policy_segs, trade_fee_rate)
        #asset_whole_timeline = get_asset_whole_timeline(buy_list, sell_list, list_price, state_list, today)
        #profit_whole_timeline = getProfit(asset_whole_timeline, 10000)
        # the profit must beat the market.
        profit_list = [getProfit(asset, 10000) for asset in asset_list]
        asset_wavg = get_weighted_avg(asset_list)
        profit_wavg = get_weighted_avg(profit_list)
        
        profit_diff_list = get_diff_list(profit_list)
        profit_diff_wavg = get_weighted_avg(profit_diff_list)

        if profit_wavg > max_profit_wavg and profit_wavg > min_avg_profit and profit_diff_wavg > 0.1 and is_all_elem_bigger_than(profit_list,0):
            print("comb:{}, asset_wavg{}, profit_wavg{}, profit_diff_wavg={}".format(i, asset_wavg, profit_wavg, profit_diff_wavg))
            optimized_buy_list = buy_list.copy()
            optimized_sell_list = sell_list.copy()
            max_asset_wavg = asset_wavg
            max_profit_wavg = profit_wavg
            max_profit_list = profit_list
            max_profit_diff_wavg = profit_diff_wavg


    print("n_components:{}, optimized_buy_list:{}, optimized_sell_list:{}, profit_list:{}, \
             profit_diff_wavg:{}".format(n_components, optimized_buy_list,
                                                  optimized_sell_list,
                                                  max_profit_list,
                                                  max_profit_diff_wavg))

    return optimized_buy_list, optimized_sell_list, max_profit_wavg, max_profit_list, max_profit_diff_wavg

