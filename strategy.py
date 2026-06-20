"""
FILE: strategy.py
Handles all quantitative calculations: FIFO, P&L, Sharpe, Drawdown, and Metrics.
"""
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
    sharpe = daily_net.mean() / daily_net.std() * np.sqrt(252) if daily_net.std() != 0 else 0
    return pd.DataFrame([{
        "Total Trades": len(df),
        "Net P&L (USD)": (df[df['side'] == 'SELL']['value'].sum() - df[df['side'] == 'SELL']['fee'].sum()) - 
                         (df[df['side'] == 'BUY']['value'].sum() + df[df['side'] == 'BUY']['fee'].sum()),
        "Sharpe Ratio (daily)": round(sharpe, 2)
    }])

def get_daily_realized_pnl(df_trades):
    if df_trades.empty: return 0.0
    df = df_trades.copy()
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    today = df[df['timestamp'].dt.date == date.today()]
    if today.empty: return 0.0
    return today.apply(lambda r: (r['value'] - r['fee']) if r['side'] == 'SELL' else -(r['value'] + r['fee']), axis=1).sum()
