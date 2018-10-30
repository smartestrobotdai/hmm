import sys
import warnings
#warnings.filterwarnings('ignore')
from hmm_lib import * 



if len(sys.argv) < 2:
  print("Usage: ./hmm_stock.py stock_name, n_components, start_day, trade_days")
  print("n_components: number of components for HMM, default: 8")
  print("start_day: the day you want to start, start from 1.")
  print("trade_days: the number of days you want to invest, default: 100")
  sys.exit(-1)

stock_name = sys.argv[1]
n_components = 8
min_price_rate_change_diff = 0
max_price_rate_change_diff = 0.6
min_profit_weighted_avg = 0.05
all_price_list, all_list_X = loadFile(sys.argv[1])
start_day = int(len(all_list_X) * 7/10) + 1
trade_days = 20

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

remodel = getHmmModel(n_components=n_components, n_iter=1000, random_state = 140)

# remodel = hmm.GaussianHMM(n_components=COMPONENTS,  n_iter=1000, random_state = 140,  covariance_type="full")
hmm_start_day = start_day - trade_days * 2 - 1

list_X = all_list_X[hmm_start_day:]
price_list = all_price_list[hmm_start_day:]

remodel.fit(list_X[:start_day - 1])
state_list = remodel.predict(list_X[:start_day - 1])
price_list = price_list[:start_day]
comb_list = getCombineList(n_components, price_list, state_list, trade_days, [20, 10, 5, 0], [20, 10, 5], 0.001)
print("hmm_start_day:{}, price_list:{}".format(hmm_start_day, len(price_list)))
# test combs one by one:
print("comb_list{}".format(comb_list))
for comb in comb_list:
  print("comb:{}".format(comb))
  buy_list = comb[0]
  sell_list = comb[1]
  if len(buy_list) == 0 and len(sell_list) == 0:
    continue

  profit_list = comb[2]
  ema_list = comb[3]
  money = 10000
  stocks = 0
  for i in range(start_day , start_day + trade_days - 1):
      
    price_list = all_price_list[hmm_start_day:i]
    list_X = all_list_X[hmm_start_day:i]
    state_list = remodel.predict(list_X)
    price = price_list[-1]
    state = state_list[-1]

    money, stocks, op = tradeForToday(money, stocks, state, 
                                buy_list, sell_list, price)
    if op == "buy" or op == "sell":
      asset = stocks * price_list[-1] + money
      print("day: {} op:{}, current price: {}, current asset:{}".format(i - start_day, op, price, asset))
      num_trades += 1

  final_asset =  stocks * price_list[-1] + money  
  print("finish: current price: {}, current asset:{}".format(price_list[-1], final_asset))
  
  actual_profit = getProfit(final_asset, 10000)
  print("DATA: {},{},{},{},{},{},{}".format(stock_name,n_components, len(buy_list), len(sell_list), ",".join(map(str, profit_list)), ",".join(map(str, ema_list)), actual_profit))
