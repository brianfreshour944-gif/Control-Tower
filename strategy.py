# strategy.py
import pandas as pd
import numpy as np
from datetime import date

def fifo_stats_all_bots(df_trades):
    if df_trades.empty: return {}
    df = df_trades.copy()
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values(['bot_name', 'symbol', 'timestamp'])
    result = {}
    # FIX: group by (bot_name, symbol), not just bot_name -- a bot trading
    # multiple symbols (e.g. BTC/USD and ETH/USD) would otherwise have its
    # BUY/SELL queues mixed across symbols, matching e.g. a BTC buy against
    # an ETH sell and producing nonsensical P&L (seen as huge spurious
    # gains/losses in the FIFO Debugger tab).
    for (bot, symbol), group in df.groupby(['bot_name', 'symbol']):
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
        # Merge results across symbols for the same bot, since the
        # dashboard's per-bot views key off bot_name alone.
        if bot not in result:
            result[bot] = {
                'bot_name': bot, 'realized_pnl': 0.0,
                'wins': 0, 'losses': 0, 'total_closed': 0,
                'orphaned_qty': 0.0, 'orphaned_cost_basis': 0.0,
            }
        result[bot]['realized_pnl'] = round(result[bot]['realized_pnl'] + realized_pnl, 2)
        result[bot]['wins'] += wins
        result[bot]['losses'] += losses
        result[bot]['total_closed'] += total_closed
        result[bot]['orphaned_qty'] = round(result[bot]['orphaned_qty'] + sum(b['qty'] for b in buy_queue), 6)
        result[bot]['orphaned_cost_basis'] = round(result[bot]['orphaned_cost_basis'] + sum(b['qty'] * b['price'] for b in buy_queue), 2)

    for bot in result:
        tc = result[bot]['total_closed']
        result[bot]['win_rate'] = round((result[bot]['wins'] / tc * 100) if tc > 0 else 0, 2)
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
    """
    Returns (matched_trades_df, total_orphaned_qty) for the given bot.
    matched_trades_df includes a 'symbol' column. Matching is done
    separately per symbol -- a BUY in one symbol is never matched against
    a SELL in a different symbol, even for bots that trade more than one
    (e.g. a bot trading both BTC/USD and ETH/USD).
    total_orphaned_qty sums orphaned quantity across all symbols; see the
    per-row 'symbol' column if you need it broken out.
    """
    bot_df = df_trades[df_trades['bot_name'] == bot_name].sort_values(['symbol', 'timestamp'])
    if bot_df.empty:
        return pd.DataFrame(), 0.0
    matched = []
    total_orphaned = 0.0
    for symbol, sym_df in bot_df.groupby('symbol'):
        buy_queue = []
        for _, row in sym_df.iterrows():
            qty = float(row['quantity']); price = float(row['price'])
            fee = float(row.get('fee', 0) or 0); side = str(row['side']).upper(); ts = row['timestamp']
            if side == 'BUY':
                buy_queue.append({'qty': qty, 'price': price, 'fee': fee, 'time': ts})
            elif side == 'SELL':
                sq = qty
                while sq > 1e-8 and buy_queue:
                    b = buy_queue[0]; mq = min(sq, b['qty'])
                    pnl = (price - b['price']) * mq
                    matched.append({'symbol': symbol, 'buy_time': b['time'], 'sell_time': ts,
                                    'buy_price': b['price'], 'sell_price': price,
                                    'quantity': mq, 'pnl': round(pnl, 4)})
                    b['qty'] -= mq; sq -= mq
                    if b['qty'] <= 1e-8: buy_queue.pop(0)
        total_orphaned += sum(b['qty'] for b in buy_queue)
    matched_df = pd.DataFrame(matched)
    if not matched_df.empty:
        matched_df = matched_df.sort_values('sell_time').reset_index(drop=True)
    return matched_df, total_orphaned

def get_daily_pnl_per_bot(df_trades):
    """
    Returns a DataFrame with columns: date, bot_name, daily_pnl
    daily_pnl = sum of net cash flow (SELL +value, BUY -value, minus fees) per bot per day.

    NOTE: this is cash flow, not realized profit -- a BUY and its matching
    SELL can land on different days, so a single day can show a large
    "loss" here just from the bot buying inventory it hasn't sold yet.
    See get_daily_realized_pnl_per_bot() for FIFO-matched realized P&L
    bucketed by the day each trade actually closed.
    """
    if df_trades.empty:
        return pd.DataFrame(columns=['date', 'bot_name', 'daily_pnl'])

    df = df_trades.copy()
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['date'] = df['timestamp'].dt.date

    # Net cash per trade: SELL => +value - fee ; BUY => -value - fee
    df['net_cash'] = df.apply(
        lambda r: r['value'] - float(r.get('fee', 0) or 0) if str(r['side']).upper() == 'SELL'
                  else -r['value'] - float(r.get('fee', 0) or 0),
        axis=1
    )

    daily = df.groupby(['date', 'bot_name'], as_index=False)['net_cash'].sum()
    daily.columns = ['date', 'bot_name', 'daily_pnl']
    return daily.sort_values(['date', 'bot_name'])


def get_daily_realized_pnl_per_bot(df_trades):
    """
    Returns a DataFrame with columns: date, bot_name, realized_pnl, closed_trades
    Uses the same FIFO BUY-matching logic as fifo_stats_all_bots(), but
    records each match's P&L under the date of the SELL that closed it,
    instead of only accumulating a lifetime total. This is "did the bot
    actually make money that day" -- unaffected by inventory still held.
    """
    if df_trades.empty:
        return pd.DataFrame(columns=['date', 'bot_name', 'realized_pnl', 'closed_trades'])

    df = df_trades.copy()
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values(['bot_name', 'symbol', 'timestamp'])

    records = []
    # FIX: match per (bot_name, symbol), not just bot_name -- see the same
    # fix and rationale in fifo_stats_all_bots().
    for (bot, symbol), group in df.groupby(['bot_name', 'symbol']):
        buy_queue = []
        for _, row in group.iterrows():
            qty, price, fee = float(row['quantity']), float(row['price']), float(row.get('fee', 0) or 0)
            side = str(row['side']).upper()
            sell_date = row['timestamp'].date()
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
                    records.append({'date': sell_date, 'bot_name': bot, 'pnl': pnl})
                    buy['qty'] -= mq
                    sell_qty -= mq
                    if buy['qty'] <= 1e-8: buy_queue.pop(0)

    if not records:
        return pd.DataFrame(columns=['date', 'bot_name', 'realized_pnl', 'closed_trades'])

    rec_df = pd.DataFrame(records)
    daily = rec_df.groupby(['date', 'bot_name'], as_index=False).agg(
        realized_pnl=('pnl', 'sum'),
        closed_trades=('pnl', 'count'),
    )
    return daily.sort_values(['date', 'bot_name'])


def aggregate_to_weekly(daily_df, value_cols):
    """
    Groups a daily (date, bot_name, ...) DataFrame into ISO weeks.
    value_cols: list of column names to sum (e.g. ['daily_pnl'] or
    ['realized_pnl', 'closed_trades']). Adds 'week_start' (Monday of
    that ISO week) as the grouping key, replacing 'date'.
    """
    if daily_df.empty:
        cols = ['week_start', 'bot_name'] + value_cols
        return pd.DataFrame(columns=cols)

    df = daily_df.copy()
    df['date'] = pd.to_datetime(df['date'])
    df['week_start'] = (df['date'] - pd.to_timedelta(df['date'].dt.weekday, unit='D')).dt.date

    weekly = df.groupby(['week_start', 'bot_name'], as_index=False)[value_cols].sum()
    return weekly.sort_values(['week_start', 'bot_name'])
