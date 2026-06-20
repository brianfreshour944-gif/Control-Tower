# strategy.py
import pandas as pd
import numpy as np
from datetime import date

def fifo_stats_all_bots(df_trades):
    if df_trades.empty: return {}
    df = df_trades.copy()
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values(['bot_name', 'timestamp'])
    result = {}
    for bot, group in df.groupby('bot_name'):
        buy_queue = []
        realized_pnl = 0.0
        wins = losses = total_closed = 0
        for _, row in group.iterrows():
            qty, price, fee, side = float(row['quantity']), float(row['price']), float(row.get('fee', 0) or 0), str(row['side']).upper()
            if side == 'BUY':
                buy_queue.append({'qty': qty, 'price': price, 'fee': fee})
            elif side == 'SELL':
                sell_qty = qty
                while sell_qty > 1e-8 and buy_queue:
                    buy = buy_queue[0]
                    mq = min(sell_qty, buy['qty'])
                    buy_fee = buy['fee'] * (mq / buy['qty']) if buy['qty'] > 0 else 0
                    sell_fee = fee * (mq / qty) if qty > 0 else 0
                    pnl = (price - buy['price']) * mq - buy_fee - sell_fee
                    realized_pnl += pnl
                    total_closed += 1
                    wins += 1 if pnl > 0 else 0
                    losses += 1 if pnl < 0 else 0
                    buy['qty'] -= mq
                    sell_qty -= mq
                    if buy['qty'] <= 1e-8: buy_queue.pop(0)
        result[bot] = {
            'bot_name': bot, 'realized_pnl': round(realized_pnl, 2),
            'wins': wins, 'losses': losses, 'total_closed': total_closed,
            'win_rate': round((wins / total_closed * 100) if total_closed > 0 else 0, 2),
            'orphaned_qty': round(sum(b['qty'] for b in buy_queue), 6),
            'orphaned_cost_basis': round(sum(b['qty'] * b['price'] for b in buy_queue), 2),
        }
    return result

def compute_performance_metrics(df_trades):
    if df_trades.empty: return pd.DataFrame()
    df = df_trades.copy()
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['net_cash'] = df.apply(lambda r: r['value'] - r['fee'] if r['side'] == 'SELL' else -r['value'] - r['fee'], axis=1)
    df['date'] = df['timestamp'].dt.date
    daily_net = df.groupby('date')['net_cash'].sum().sort_index()
    cum_pnl = daily_net.cumsum()
    running_max = cum_pnl.expanding().max()
    drawdown = (cum_pnl - running_max) / running_max.abs().replace(0, 1)
    max_drawdown = drawdown.min()
    buy_val = df[df['side'] == 'BUY']['value'].sum()
    buy_fee = df[df['side'] == 'BUY']['fee'].sum()
    sell_val = df[df['side'] == 'SELL']['value'].sum()
    sell_fee = df[df['side'] == 'SELL']['fee'].sum()
    sharpe = daily_net.mean() / daily_net.std() * np.sqrt(252) if daily_net.std() != 0 else 0
    return pd.DataFrame([{
        "Total Trades": len(df),
        "Gross P&L (USD)": sell_val - buy_val,
        "Net P&L (USD)": (sell_val - sell_fee) - (buy_val + buy_fee),
        "Total Fees (USD)": buy_fee + sell_fee,
        "Sharpe Ratio (daily)": round(sharpe, 2),
        "Max Drawdown (%)": round(max_drawdown * 100, 2)
    }])

def get_daily_realized_pnl(df_trades):
    if df_trades.empty: return 0.0
    df = df_trades.copy()
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    today = df[df['timestamp'].dt.date == date.today()]
    if today.empty: return 0.0
    return today.apply(lambda r: (r['value'] - r['fee']) if r['side'] == 'SELL' else -(r['value'] + r['fee']), axis=1).sum()

def get_live_bot_metrics(df_trades):
    if df_trades.empty: return pd.DataFrame()
    df = df_trades.copy()
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['net_cash'] = df.apply(lambda r: r['value'] - r['fee'] if r['side'] == 'SELL' else -r['value'] - r['fee'], axis=1)
    out = []
    for bot in df['bot_name'].unique():
        b = df[df['bot_name'] == bot].sort_values('timestamp')
        b['date'] = b['timestamp'].dt.date
        d = b.groupby('date')['net_cash'].sum()
        s = d.mean() / d.std() * np.sqrt(252) if d.std() != 0 else 0
        cm = b['net_cash'].cumsum()
        rm = cm.expanding().max()
        dd = ((cm - rm) / rm.abs().replace(0, 1)).min() * 100
        n = len(b)
        out.append({'bot_name': bot, 'live_total_trades': n,
                    'live_net_profit': b['net_cash'].sum(),
                    'live_sharpe': round(s, 2), 'live_max_drawdown': round(dd, 2),
                    'live_win_rate': round((b['net_cash'] > 0).sum() / n * 100, 2) if n else 0})
    return pd.DataFrame(out)

def get_fifo_debug(bot_name, df_trades):
    bot_df = df_trades[df_trades['bot_name'] == bot_name].sort_values('timestamp')
    if bot_df.empty:
        return pd.DataFrame(), 0.0
    buy_queue = []; matched = []
    for _, row in bot_df.iterrows():
        qty = float(row['quantity']); price = float(row['price'])
        fee = float(row.get('fee', 0) or 0); side = str(row['side']).upper(); ts = row['timestamp']
        if side == 'BUY':
            buy_queue.append({'qty': qty, 'price': price, 'fee': fee, 'time': ts})
        elif side == 'SELL':
            sq = qty
            while sq > 1e-8 and buy_queue:
                b = buy_queue[0]; mq = min(sq, b['qty'])
                pnl = (price - b['price']) * mq
                matched.append({'buy_time': b['time'], 'sell_time': ts,
                                'buy_price': b['price'], 'sell_price': price,
                                'quantity': mq, 'pnl': round(pnl, 4)})
                b['qty'] -= mq; sq -= mq
                if b['qty'] <= 1e-8: buy_queue.pop(0)
    return pd.DataFrame(matched), sum(b['qty'] for b in buy_queue)
