"""Analisi performance del Trading Agent"""
import os
from dotenv import load_dotenv
import psycopg2
from collections import defaultdict

load_dotenv()

conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cur = conn.cursor()

print('='*80)
print('ANALISI PERFORMANCE ULTIMI 3 GIORNI')
print('='*80)

cur.execute('''
    SELECT 
        DATE(closed_at) as day,
        COUNT(*) as num_trades,
        SUM(pnl_usd) as total_pnl,
        SUM(CASE WHEN pnl_usd > 0 THEN 1 ELSE 0 END) as wins,
        SUM(CASE WHEN pnl_usd < 0 THEN 1 ELSE 0 END) as losses
    FROM trades_history 
    WHERE closed_at >= NOW() - INTERVAL '3 days'
    GROUP BY DATE(closed_at)
    ORDER BY day DESC
''')

total_pnl = 0
total_trades = 0
for row in cur.fetchall():
    day, num, pnl, wins, losses = row
    pnl = pnl or 0
    win_rate = (wins/num*100) if num > 0 else 0
    print(f'{day}: {num} trades | PnL: {pnl:.2f} EUR | Win Rate: {win_rate:.1f}% ({wins}W/{losses}L)')
    total_pnl += pnl
    total_trades += num

print(f'\nTOTALE: {total_trades} trades | PnL: {total_pnl:.2f} EUR')

print()
print('='*80)
print('NUMERO OPERAZIONI PER GIORNO (incluso hold)')
print('='*80)

cur.execute('''
    SELECT 
        DATE(created_at) as day,
        operation,
        COUNT(*) as cnt
    FROM bot_operations 
    WHERE created_at >= NOW() - INTERVAL '3 days'
    GROUP BY DATE(created_at), operation
    ORDER BY day DESC, operation
''')

by_day = defaultdict(dict)
for row in cur.fetchall():
    day, op, cnt = row
    by_day[day][op] = cnt

for day, ops in by_day.items():
    total = sum(ops.values())
    opens = ops.get('open', 0)
    closes = ops.get('close', 0)
    holds = ops.get('hold', 0)
    print(f'{day}: {total} totali | open={opens} | close={closes} | hold={holds}')

print()
print('='*80)
print('FREQUENZA OPERAZIONI (ogni quanti minuti?)')
print('='*80)

# Calcolo la frequenza media tra le operazioni
cur.execute('''
    SELECT created_at FROM bot_operations 
    WHERE created_at >= NOW() - INTERVAL '1 day'
    ORDER BY created_at
''')

times = [row[0] for row in cur.fetchall()]
if len(times) > 1:
    diffs = []
    for i in range(1, len(times)):
        diff = (times[i] - times[i-1]).total_seconds() / 60
        diffs.append(diff)
    avg_interval = sum(diffs) / len(diffs)
    print(f'Intervallo medio tra operazioni: {avg_interval:.1f} minuti')
    print(f'Operazioni nelle ultime 24h: {len(times)}')
    print(f'Operazioni per ora: {len(times) / 24:.1f}')

print()
print('='*80)
print('PROBLEMA: OVERTRADING!')
print('='*80)
print('Il bot sta operando ogni ~15 minuti e chiude quasi sempre le posizioni!')
print('Questo causa:')
print('  - Troppe commissioni/spread')
print('  - Non lascia correre i profitti')
print('  - Esce troppo presto dalle posizioni')

conn.close()
