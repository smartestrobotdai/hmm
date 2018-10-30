import sys
import warnings
warnings.filterwarnings('ignore')
from hmm_lib import loadFile, findPolicy, getStateList

if len(sys.argv) < 2:
  print("Usage: ./hmm_stock.py stock_name, n_components, start_day, trade_days, min_price_rate_change_diff, \
    max_price_rate_change_diff min_profit_weighted_avg")
  print("n_components: number of components for HMM, default: 8")
  print("start_day: the day you want to start")
  print("trade_days: the number of days you want to invest, default: 100")
  print("min_price_rate_change_diff: minimum price momentum, default: 0")
  print("max_price_rate_change_diff: maximum price momentum, default: 0.4")
  print("min_profit_weighted_avg: minimum profit weighted average for policy, default: 0.15")
  sys.exit(-1)

stock_name = sys.argv[1]
n_components = 8
min_price_rate_change_diff = 0
max_price_rate_change_diff = 0.6
min_profit_weighted_avg = 0.05
list_price, listX = loadFile(sys.argv[1])
start_day = int(len(listX) * 7/10) + 1
trade_days = 100

if len(sys.argv) > 2:
  n_components = int(sys.argv[2])
if len(sys.argv) > 3:
  start_day = int(sys.argv[3])
if len(sys.argv) > 4:
  trade_days = int(sys.argv[4])
if len(sys.argv) > 5:
  min_price_rate_change_diff = float(sys.argv[5])
if len(sys.argv) > 6:
  max_price_rate_change_diff = float(sys.argv[6])
if len(sys.argv) > 7:
  min_profit_weighted_avg = float(sys.argv[7])

money = 10000
stocks = 0
exp_profit = 0
verify_profit = 0
delayed_update = False
optimized_buy_list = None
optimized_sell_list = None
trade_price = 0
num_trades = 0
trade_fee_rate = 0.001

remodel = getStateList(n_components=n_components, n_iter=1000, random_state = 140)

# remodel = hmm.GaussianHMM(n_components=COMPONENTS,  n_iter=1000, random_state = 140,  covariance_type="full")
remodel.fit(listX[:start_day - 1])
state_list = remodel.predict(listX[:start_day - 1])

price_list = list_price[:start_day]
optimized_buy_list, optimized_sell_list, max_profit_wavg, max_profit_list, max_profit_diff_wavg= findPolicy(n_components, price_list, 
                                                      state_list, 
                                                      start_day - 1, 
                                                      trade_days, 
                                                      3, 
                                                      min_profit_weighted_avg,
                                                      trade_fee_rate)

if optimized_buy_list == None and optimized_sell_list == None:
  print("finished: name: {} stocks:{}, start_day: {}, trade_days:{}, money:{}, \
    cur_price:{}, asset: {}, num_trades: {}".format(stock_name, stocks, 
      start_day, trade_days, money, price_list[-1], 10000, num_trades))
  sys.exit(0)

price_change_list = get_price_change_rate_multi_segs(price_list, start_day - 1, trade_days, 3)
price_change_wavg = get_weighted_avg(price_change_list)
#print("WARNING: diff_wavg is too low")    
price_change_diff_list = get_diff_list(price_change_list)
price_change_diff_wavg = get_weighted_avg(price_change_diff_list)

print("price_change_list={}, price_change_wavg={}, price_change_diff_list={}, price_change_diff_wavg={}".format(
        price_change_list, price_change_wavg, price_change_diff_list,price_change_diff_wavg ))

if price_change_list[-1] > 0.4 or is_all_elem_bigger_than(price_change_diff_list,0)==False :
  print("uncertain price:{}, aborting........".format(price_change_list))
  sys.exit(0)

for i in range(start_day , start_day + trade_days - 1):
  price_list = list_price[:i]
  state_list = remodel.predict(listX[:i])
  price = list_price[-1]

  price_change_list = get_price_change_rate_multi_segs(price_list, i - 1, trade_days, 3)
  price_change_wavg = get_weighted_avg(price_change_list)
  #print("WARNING: diff_wavg is too low")    
  price_change_diff_list = get_diff_list(price_change_list)
  price_change_diff_wavg = get_weighted_avg(price_change_diff_list)
 
  #if price_rate_change_diff_wavg < min_price_rate_change_diff or price_rate_change_diff_wavg > max_price_rate_change_diff:
  #    continue
   
  # if we lost 10%, sell it
  if stocks > 0 and price_list[i - 1] / trade_price < 0.90:
    print("day: {} lost 10%, trade price:{}, sell it at price: {}.".format(i, trade_price, price_list[i - 1]))
    money, stocks = trade(money, stocks, price_list[i - 1], "sell", trade_fee_rate)
    continue
  # trace back if we need sell or buy

  money, stocks, op = tradeForToday(money, stocks, state_list[i - 1], 
                                optimized_buy_list, optimized_sell_list, price_list[i - 1])
  if op == "buy" or op == "sell":
    num_trades += 1
    if op == "buy":
      trade_price = price_list[i - 1]
  

total_asset =  stocks * price_list[-1] + money
actual_profit = getProfit(total_asset, 10000)

print("n_comp:{}, max_profit_wavg:{},max_profit_list:{},max_profit_diff_wavg:{}, price_change_list:{}, price_change_wavg={}, actual_profit:{}, price_change_diff_wavg:{}".format(
       n_components, max_profit_wavg, max_profit_list,  max_profit_diff_wavg,   price_change_list,    price_change_wavg, actual_profit, price_change_diff_wavg))

print("finished: name: {} stocks:{}, start_day: {}, trade_days:{}, money:{}, \
  cur_price:{}, asset: {}, num_trades: {}".format(stock_name, stocks, 
    start_day, trade_days, money, price_list[-1], total_asset, num_trades))
