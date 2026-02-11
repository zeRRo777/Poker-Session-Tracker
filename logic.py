import pandas as pd

def calculate_kpi(df):
    if df.empty:
        return 0, 0, 0, 0

    total_profit = df['profit'].sum()
    total_sessions = len(df)

    # Hourly Rate
    hourly_rate = calc_hourly_rate(df, total_profit)

    # Win Rate
    wins = len(df[df['profit'] > 0])
    win_rate = (wins / total_sessions) * 100

    return total_profit, hourly_rate, total_sessions, win_rate


def get_records(df):
    if df.empty:
        return {}

    best_win_row = df.loc[df['profit'].idxmax()]
    worst_loss_row = df.loc[df['profit'].idxmin()]

    return {
        'best_win': (best_win_row['profit'], best_win_row['date'].strftime('%Y-%m-%d')),
        'worst_loss': (worst_loss_row['profit'], worst_loss_row['date'].strftime('%Y-%m-%d')),
    }

def calculate_streaks(df):
    if df.empty:
        return 0, 0

    df_sorted = df.sort_values(by='date')
    profits = df_sorted['profit'].tolist()

    max_win_streak = 0
    max_loss_streak = 0
    current_win = 0
    current_loss = 0

    for p in profits:
        if p > 0:
            current_win += 1
            current_loss = 0
            max_win_streak = max(max_win_streak, current_win)
        elif p < 0:
            current_loss += 1
            current_win = 0
            max_loss_streak = max(max_loss_streak, current_loss)
        else:
            current_win = 0
            current_loss = 0

    return max_win_streak, max_loss_streak


def get_roi(df):
    mtt_df = df[df['game_type'] == 'MTT']

    if mtt_df.empty:
        return 0.0

    total_buyin = mtt_df['buy_in'].sum()
    total_profit = mtt_df['profit'].sum()

    if total_buyin == 0:
        return 0.0

    return (total_profit / total_buyin) * 100


def calc_hourly_rate(df, total_profit):
    if df.empty:
        return 0
    df_calc = df.copy()
    if not df_calc['date'].empty and hasattr(df_calc['date'].dt, 'date'):
        df_calc['date_group'] = df_calc['date'].dt.date
    else:
        df_calc['date_group'] = df_calc['date']

    daily_durations = df_calc.groupby('date_group')['duration_minutes'].max()
    total_real_minutes = daily_durations.sum()
    total_real_hours = total_real_minutes / 60

    hourly_rate = total_profit / total_real_hours if total_real_hours > 0 else 0

    return hourly_rate

