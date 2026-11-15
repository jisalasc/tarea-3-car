#!/usr/bin/env python3
"""Audita cobertura experimental, integridad de CSV y tablas del informe (sin MPI).

Uso: python scripts/audit_results.py [--out informe/verificacion/resultados.json]
No modifica las mediciones. Solo requiere la biblioteca estándar.
"""
import argparse
import csv
import json
import math
import re
import statistics
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_csv(relative):
    with (ROOT / relative).open(newline='') as handle:
        return list(csv.DictReader(handle))


def distributed(relative, expected):
    groups = defaultdict(lambda: defaultdict(list))
    rows = read_csv(relative)
    for row in rows:
        key = tuple(int(row[k]) for k in ('b', 'pr', 'pc', 'threads', 'nodes'))
        require(key in expected, f'{relative}: configuración inesperada {key}')
        b, pr, pc, threads, nodes = key
        rank = int(row['rank'])
        require(int(row['N']) == 8192, f'{relative}: N distinto de 8192')
        require((int(row['myrow']), int(row['mycol'])) == divmod(rank, pc),
                f'{relative}: coordenadas incompatibles con rank {rank}')
        require(int(row['tasks_per_node']) * nodes == pr * pc,
                f'{relative}: procesos/nodo inconsistentes')
        require(int(row['tasks_per_node']) * threads <= 8,
                f'{relative}: más de ocho CPUs por nodo')
        times = [float(row[k]) for k in ('t_comp', 't_comm', 't_wall', 't_max')]
        require(all(math.isfinite(t) and t >= 0 for t in times),
                f'{relative}: tiempo inválido')
        require(times[0] + times[1] <= times[2] + 3e-6,
                f'{relative}: cómputo+comunicación excede wall')
        require(bool(row['job']), f'{relative}: falta job de procedencia')
        groups[key][(row['job'], int(row['rep']))].append(row)
    require(set(groups) == expected, f'{relative}: faltan configuraciones')
    summary = {}
    for key, runs in groups.items():
        require(len(runs) == 3, f'{relative}: se esperan tres corridas para {key}')
        require({rep for job, rep in runs} == {0, 1, 2},
                f'{relative}: repeticiones incorrectas para {key}')
        ordered = []
        for run, processes in runs.items():
            b, pr, pc, threads, nodes = key
            require(sorted(int(r['rank']) for r in processes) == list(range(pr * pc)),
                    f'{relative}: ranks faltantes/duplicados en {run}')
            require(len({r['host'] for r in processes}) == nodes,
                    f'{relative}: número incorrecto de hosts')
            if nodes == 1:
                require({r['host'] for r in processes} == {'ventress'},
                        f'{relative}: referencia de un nodo cambió de hardware')
            for host in {r['host'] for r in processes}:
                require(sum(r['host'] == host for r in processes) == pr * pc // nodes,
                        f'{relative}: distribución por host incorrecta')
            require(len({r['t_max'] for r in processes}) == 1,
                    f'{relative}: t_max difiere entre ranks')
            elapsed = float(processes[0]['t_max'])
            require(abs(elapsed - max(float(r['t_wall']) for r in processes)) <= 1e-6,
                    f'{relative}: t_max no es el máximo wall')
            ordered.append((elapsed, processes))
        ordered.sort(key=lambda run: run[0])
        elapsed, processes = ordered[1]
        summary[key] = dict(time=elapsed, low=ordered[0][0], high=ordered[2][0],
                            comp=statistics.mean(float(r['t_comp']) for r in processes),
                            comm=statistics.mean(float(r['t_comm']) for r in processes),
                            rows=sorted(processes, key=lambda r: int(r['rank'])))
    return summary, len(rows)


def markdown_tables():
    blocks = re.findall(r'(?:^\|.*\|\s*\n)+', (ROOT / 'informe/informe.md').read_text(), re.M)
    tables = []
    for block in blocks:
        rows = [[cell.strip() for cell in line.strip().strip('|').split('|')]
                for line in block.splitlines() if line.strip()]
        if len(rows) >= 2 and all(re.fullmatch(r':?-+:?', x) for x in rows[1]):
            tables.append((rows[0], rows[2:]))
    return tables


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    grids = [(1, 1, t) for t in (1, 2, 4, 8)]
    grids += [(pr, pc, t) for pr, pc in ((1, 2), (2, 1)) for t in (1, 2, 4)]
    grids += [(2, 2, t) for t in (1, 2)] + [(2, 4, 1), (4, 2, 1)]
    configs = {0: grids[:4], 1: grids[4:10], 2: grids[10:12], 3: grids[12:],
               4: [(2, 4, 1)], 5: [(4, 4, 1)]}
    all_configs = {}
    count = 0
    for config, variants in configs.items():
        expected = {(b, pr, pc, t, 1 if config < 4 else 2)
                    for b in (512, 1024) for pr, pc, t in variants}
        result, n = distributed(f'results/cluster/config{config}.csv', expected)
        all_configs.update(result)
        count += n
    sweep, n = distributed('results/cluster/parte_c.csv',
                           {(b, 2, 2, 2, 1) for b in (64, 128, 256, 512, 1024, 2048, 4096, 8192)})
    count += n
    serial = defaultdict(list)
    for row in read_csv('results/parte_a_mac_jose.csv'):
        require(int(row['N']) == 4096 and int(row['threads']) == 1,
                'Parte (a): N o threads incorrectos')
        require(math.isfinite(float(row['time_s'])) and float(row['time_s']) > 0,
                'Parte (a): tiempo inválido')
        serial[int(row['b'])].append(row)
    require(set(serial) == {64, 128, 256, 512, 1024, 2048, 4096}, 'Parte (a): bloques faltantes')
    for b, rows in serial.items():
        require(len(rows) == 3 and {int(r['rep']) for r in rows} == {0, 1, 2},
                f'Parte (a): repeticiones incorrectas para b={b}')
        residuals = [float(r['residual']) for r in rows if math.isfinite(float(r['residual']))]
        require(residuals and max(residuals) < 1e-8, f'Parte (a): residuo inválido para b={b}')
    f = lambda x: f'{x:.3f}'
    expected_a = [[str(b), str(4096 // b), f(statistics.median(float(r['time_s']) for r in serial[b])),
                   f(min(float(r['time_s']) for r in serial[b])), f(max(float(r['time_s']) for r in serial[b])),
                   f'{2 * 4096**3 / 3 / statistics.median(float(r["time_s"]) for r in serial[b]) / 1e9:.1f}']
                  for b in sorted(serial, reverse=True)]
    checked = 0
    for header, rows in markdown_tables():
        if header[:2] == ['$b$', '$N/b$']:
            expected_rows = expected_a
        elif header[:2] == ['$b$', r'$t_{\max}$ [s]']:
            expected_rows = [[str(b), f(v['time']), f(v['low']), f(v['high']), f(v['comp']), f(v['comm']),
                              f'{2 * 8192**3 / 3 / v["time"] / 1e9:.1f}']
                             for (b, pr, pc, t, n), v in sorted(sweep.items(), reverse=True)]
        elif header[0] == 'Config.':
            require(len(rows) == 14, 'Parte (d): tabla incompleta')
            # Identify its block from the one-thread reference, without relying on section order.
            block = next((b for b in (512, 1024)
                          if rows[0][4] == f(all_configs[(b, 1, 1, 1, 1)]['time'])), None)
            require(block is not None, 'Parte (d): T(1) no coincide con CSV')
            expected_rows = []
            for pr, pc, t in grids:
                v = all_configs[(block, pr, pc, t, 1)]
                config = next(c for c in range(4) if (pr, pc, t) in configs[c])
                s = all_configs[(block, 1, 1, 1, 1)]['time'] / v['time']
                expected_rows.append([str(config), f'{pr}×{pc}', str(t), str(pr * pc * t),
                                      f(v['time']), f'{s:.2f}', f'{100 * s / (pr * pc * t):.1f}%'])
        elif header[:3] == ['$b$', 'Config.', 'Grid']:
            expected_rows = []
            for b in (512, 1024):
                for config, pr, pc, nodes in ((3, 2, 4, 1), (4, 2, 4, 2), (5, 4, 4, 2)):
                    v = all_configs[(b, pr, pc, 1, nodes)]
                    expected_rows.append([str(b), str(config), f'{pr}×{pc}', str(nodes), str(pr * pc),
                                          f(v['time']), f(v['comp']), f(v['comm'])])
        elif header[:3] == ['$b$', 'Config.', 'Nodo']:
            expected_rows = []
            for b in (512, 1024):
                for config, pr, pc in ((4, 2, 4), (5, 4, 4)):
                    v = all_configs[(b, pr, pc, 1, 2)]
                    for host in ('ventress', 'yodaxico'):
                        processes = [r for r in v['rows'] if r['host'] == host]
                        ranks = [int(r['rank']) for r in processes]
                        expected_rows.append([str(b), str(config), host, f'{min(ranks)}–{max(ranks)}',
                                              f(statistics.mean(float(r['t_comp']) for r in processes)),
                                              f(statistics.mean(float(r['t_comm']) for r in processes))])
        elif header[:2] == ['$b$', 'Rank']:
            expected_rows = []
            for b in (4096, 512):
                v = sweep[(b, 2, 2, 2, 1)]
                for r in v['rows']:
                    expected_rows.append([str(b), r['rank'], f"({r['myrow']},{r['mycol']})",
                                          f(float(r['t_comp'])), f(float(r['t_comm'])),
                                          f(float(r['t_wall'])), f(v['time'])])
        elif header[:2] == ['$b$', 'Grid']:
            expected_rows = []
            for (b, pr, pc, t, nodes), v in sorted(all_configs.items()):
                label = f'{pr}×{pc}' + (f' ({nodes} nodos)' if nodes > 1 else '')
                expected_rows.append([str(b), label, str(t), f(v['low']), f(v['high'])])
        else:
            continue
        require(sorted(rows) == sorted(expected_rows), f'Tabla no coincide con CSV: {header}')
        checked += 1
    require(checked == 8, f'Se esperaban ocho tablas numéricas; se comprobaron {checked}')
    result = dict(status='PASS', distributed_measurement_groups=len(all_configs) + len(sweep),
                  distributed_rows=count, serial_rows=sum(map(len, serial.values())),
                  numeric_report_tables=checked,
                  scope='CSV, cobertura y tablas; no valida procedencia física ni ejecuta MPI')
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')


if __name__ == '__main__':
    main()
