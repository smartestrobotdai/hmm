from hmmlearn import hmm
import numpy as np
import sys
import warnings
from itertools import combinations 

warnings.filterwarnings('ignore')

POLICY_DAYS = 100
COMPONENTS = 8

listX = []
list_price = []



def loadfile(name):
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

def trade(money, stocks, price, op):
    if op == "buy":
        stocks_inc = int(money / (price))
        stocks += stocks_inc
        money = money - stocks_inc * price
    elif op == "sell":
        money = money + stocks * price
        stocks = 0
    return money, stocks
    
def tradeForToday(money, stocks, state, buy_list, sell_list, price, detail = True):
    op = None
    if state in buy_list and money > price:
        # we buy in
        money, stocks = trade(money, stocks, price, "buy")
        if detail == True:
            print("buy in at day {}: state: {} price: {} current stocks:{}, current money:{}".format(i, state, price, stocks, money))
            op = "buy"
    elif state in sell_list and stocks > 0:
        # we sell out
        money, stocks = trade(money, stocks, price, "sell")
        if detail == True:
            print("sell out at day {}: state: {} price: {} current stocks:{}, current money:{}".format(i, state, price, stocks, money))
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

def get_asset_multi_segs(buy_list, sell_list, price_seq, state_seq, today, num_days, num_segs):
    asset_list = []
    start = today - num_days * num_segs
    end = start + num_days
    for i in range(num_segs):
        asset = check_profit(buy_list, sell_list, price_seq[start:end], 
                                   state_list[start:end])
        asset_list.append(asset) 
        start += num_days
        end += num_days
        
    return asset_list

def get_asset_whole_timeline(buy_list, sell_list, price_seq, state_seq, today):
    total_asset = check_profit(buy_list, sell_list, price_seq[:today], 
                                   state_list[:today])
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

def get_diff_wavg(input_list):
    list_diff = get_diff_list(input_list)
    list_diff_wavg = get_weighted_avg(list_diff)
    return list_diff_wavg

# find out the best way 
# TODO: update the model
def check_profit(buy_list, sell_list, price_seq, state_seq):
    #print("start to check: sell_list:{}, buy_list:{}, price change:{}".format(sell_list, buy_list, 
    #                                                                          price_seq[-1] / price_seq[0] - 1 ))
    money = 10000
    stocks = 0

    for i in range(len(state_seq)):
        money, stocks, op = tradeForToday(money, stocks, state_seq[i], buy_list, sell_list, price_seq[i], False)

    total_asset =  stocks * price_seq[-1] + money
    #print("finished: current stocks:{}, current money:{}, total asset: {}".format(stocks, money, total_asset))
    return total_asset

def getProfit(asset, origin_asset):
    return asset / origin_asset - 1

def findPolicy(list_price, state_list, today, policy_days, policy_segs, min_avg_profit):
    buy_list = []
    sell_list = []
    optimized_buy_list = None
    optimized_sell_list = None
    max_asset_wavg = 10000
    max_profit_wavg = 0
    start_day = today - policy_days * policy_segs
    max_profit_list = None
    max_profit_diff_wavg = None
    comb = findAllComb(COMPONENTS)
    for i in comb:

        buy_list = i[0]
        sell_list = i[1]
        # find profits for multiple time segments
        # the last element is the profit for entire time.
        # the date is today
        #check_profit_multi_segs(buy_list, sell_list, price_seq, state_seq, today, num_days, num_segs):
        asset_list = get_asset_multi_segs(buy_list, sell_list, list_price, state_list, today, POLICY_DAYS, policy_segs)
        asset_whole_timeline = get_asset_whole_timeline(buy_list, sell_list, list_price, state_list, today)
        profit_whole_timeline = getProfit(asset_whole_timeline, 10000)
        # the profit must beat the market.
        profit_list = [getProfit(asset, 10000) for asset in asset_list]
        asset_wavg = get_weighted_avg(asset_list)
        profit_wavg = get_weighted_avg(profit_list)
        
        profit_diff_list = get_diff_list(profit_list)
        profit_diff_wavg = get_weighted_avg(profit_diff_list)

        
        if asset_wavg > max_asset_wavg and profit_wavg > min_avg_profit and profit_diff_wavg > 0.1 and is_all_elem_bigger_than(profit_list,0):
            print("comb:{}, asset_wavg{}, profit_wavg{}, profit_diff_wavg={}".format(i, asset_wavg, profit_wavg, profit_diff_wavg))
            optimized_buy_list = buy_list.copy()
            optimized_sell_list = sell_list.copy()
            max_asset_wavg = asset_wavg
            max_profit_wavg = profit_wavg
            max_profit_list = profit_list
            max_profit_diff_wavg = profit_diff_wavg
    print("optimized_buy_list:{}, optimized_sell_list:{}, profit_list:{}, \
             profit_diff_wavg:{}".format(optimized_buy_list,
                                                  optimized_sell_list,
                                                  max_profit_list,
                                                  max_profit_diff_wavg))

    return max_profit_wavg, optimized_buy_list, optimized_sell_list


if len(sys.argv) < 2:
  print("Usage: ./hmm_stock.py stock_name, n_components, min_price_rate_change_diff, \
    max_price_rate_change_diff min_profit_weighted_avg")
  print("n_components: number of components for HMM, default: 8")
  print("min_price_rate_change_diff: minimum price momentum, default: 0")
  print("max_price_rate_change_diff: maximum price momentum, default: 0.4")
  print("min_profit_weighted_avg: minimum profit weighted average for policy, default: 0.15")
  sys.exit(-1)



stock_name = sys.argv[1]

n_components = 8
min_price_rate_change_diff = 0
max_price_rate_change_diff = 0.4
min_profit_weighted_avg = 0.15

if len(sys.argv) > 2:
  n_components = sys.argv[2]
if len(sys.argv) > 3:
  min_price_rate_change_diff = sys.argv[3]
if len(sys.argv) > 4:
  max_price_rate_change_diff = sys.argv[4]
if len(sys.argv) > 5:
  min_profit_weighted_avg = sys.argv[5]

loadfile(sys.argv[1])
training_length = int(len(listX) * 7/10)
print(training_length)

money = 10000
stocks = 0
exp_profit = 0
verify_profit = 0
update_now = False
delayed_update = False
optimized_buy_list = None
optimized_sell_list = None
remodel = None

for i in range(training_length + 1, len(list_price)):
  price_list = list_price[:i]  
  if (i - training_length - 1) % 100 == 0 or update_now:
    if stocks > 0:
      delayed_update = True
      continue

    update_now = False

    print("updating HMM model: day: {}".format(i))
    remodel = hmm.GaussianHMM(n_components=n_components,  n_iter=1000, random_state = 140)
    #remodel = hmm.GaussianHMM(n_components=COMPONENTS,  n_iter=1000, random_state = 140,  covariance_type="full")
    remodel.fit(listX[:i])
    state_list = remodel.predict(listX[:i])
    optimized_buy_list = None
    optimized_sell_list = None
    price_rate_change_list = get_price_change_rate_multi_segs(price_list, i - 1, POLICY_DAYS, 3)
    #print("WARNING: diff_wavg is too low")    
    price_rate_change_diff_list = get_diff_list(price_rate_change_list)
    price_rate_change_diff_wavg = get_weighted_avg(price_rate_change_diff_list)
    if price_rate_change_diff_wavg < min_price_rate_change_diff or price_rate_change_diff_wavg > max_price_rate_change_diff:
        print("price_rate_change_wavg = {} abnormal".format(price_rate_change_diff_wavg))
        continue
    

    best_avg_profit, optimized_buy_list, optimized_sell_list = findPolicy(price_list, 
                                                                          state_list, 
                                                                          i - 1, 
                                                                          POLICY_DAYS, 
                                                                          3, 
                                                                          min_profit_weighted_avg
                                                                          )

    print("optimized buy: {}, optimized sell: {}, best_avg_profit={}".format(optimized_buy_list, 
                                                        optimized_sell_list, 
                                                        best_avg_profit))
  else:
    state_list = remodel.predict(listX[:i])

  if optimized_buy_list == None:
    if stocks > 0:
      money, stocks = trade(money, stocks, price_list[i - 1], "sell")
      print("no idea about the stock, sell it at price: {}!")
      print("sell out at day {}: state: {} price: {} current stocks:{}, current money:{}".format(i,
                                                                                                 state_seq[i - days_back], 
                                                                                                 price_list[i], 
                                                                                                 stocks, 
                                                                                                 money))
      if delayed_update:
          delayed_update = False
          update_now = True
    continue
  
  # if we lost 10%, sell it
  if stocks > 0 and price_list[i - 1] / trade_price < 0.90:
    print("day: {} lost 10%, trade price:{}, sell it at price: {}.".format(i, trade_price, price_list[i - 1]))
    money, stocks = trade(money, stocks, price_list[i - 1], "sell")
    # seems the model is bad
    update_now = True
    continue
  # trace back if we need sell or buy
  for days_back in range(1, 2):
    money, stocks, op = tradeForToday(money, stocks, state_list[i - days_back], 
                                  optimized_buy_list, optimized_sell_list, price_list[i - 1])
    if op == "sell":
      if delayed_update:
        delayed_update = False
        update_now = True
      break
    elif op == "buy":
      trade_price = price_list[i - 1]
      break
            
        
total_asset =  stocks * list_price[-1] + money
print("finished: name: {} stocks:{}, money:{}, cur_price:{} asset: {}".format(stock_name, stocks, money, price_list[-1], total_asset))



