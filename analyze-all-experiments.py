#!/usr/bin/env python3
"""
Script para analisar todos os experimentos executados
Consolida resultados e identifica melhor configuracao
"""

import os
import pandas as pd
from pathlib import Path
import sys

# Cores para output
class Colors:
    BLUE = '\033[0;34m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    RED = '\033[0;31m'
    CYAN = '\033[0;36m'
    NC = '\033[0m'

def log_info(msg):
    print(f"{Colors.BLUE}[INFO]{Colors.NC} {msg}")

def log_success(msg):
    print(f"{Colors.GREEN}[OK]{Colors.NC} {msg}")

def log_warning(msg):
    print(f"{Colors.YELLOW}[WARN]{Colors.NC} {msg}")

def log_error(msg):
    print(f"{Colors.RED}[ERROR]{Colors.NC} {msg}")

def log_section(msg):
    print(f"\n{Colors.CYAN}{'='*60}{Colors.NC}")
    print(f"{Colors.CYAN}{msg}{Colors.NC}")
    print(f"{Colors.CYAN}{'='*60}{Colors.NC}")

def parse_experiment_name(exp_name):
    """Parse experiment name: 6n-5s-qbft-v25.10.0_20251112_133845 -> dict"""
    try:
        # Separar timestamp se existir
        timestamp = None
        if '_' in exp_name:
            parts_ts = exp_name.rsplit('_', 2)
            if len(parts_ts) == 3 and parts_ts[1].isdigit() and parts_ts[2].isdigit():
                exp_name_base = parts_ts[0]
                timestamp = f"{parts_ts[1]}_{parts_ts[2]}"
            else:
                exp_name_base = exp_name
        else:
            exp_name_base = exp_name

        # Parse parametros
        parts = exp_name_base.split('-')
        nodes = int(parts[0].replace('n', ''))
        blocktime = int(parts[1].replace('s', ''))
        consensus = parts[2]
        version = parts[3].replace('v', '')

        result = {
            'experiment': exp_name,
            'experiment_base': exp_name_base,
            'nodes': nodes,
            'blocktime': blocktime,
            'consensus': consensus,
            'version': version
        }

        if timestamp:
            result['timestamp'] = timestamp

        return result
    except:
        return None

def load_experiment_csvs(exp_dir):
    """Carrega CSVs de performance e monitor de um experimento"""
    perf_csv = exp_dir / 'caliper_performance_metrics.csv'
    mon_csv = exp_dir / 'caliper_monitor_metrics.csv'

    data = {}

    if perf_csv.exists():
        try:
            df = pd.read_csv(perf_csv)

            # Converter colunas para numerico
            for col in ['Max Latency (s)', 'Min Latency (s)', 'Avg Latency (s)', 'Throughput (TPS)', 'Success Rate']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')

            # Calcular medias
            data['avg_latency'] = df['Avg Latency (s)'].mean() if 'Avg Latency (s)' in df.columns else None
            data['max_latency'] = df['Max Latency (s)'].mean() if 'Max Latency (s)' in df.columns else None
            data['min_latency'] = df['Min Latency (s)'].mean() if 'Min Latency (s)' in df.columns else None
            data['throughput'] = df['Throughput (TPS)'].mean() if 'Throughput (TPS)' in df.columns else None
            data['success_rate'] = df['Success Rate'].mean() if 'Success Rate' in df.columns else None
        except Exception as e:
            log_warning(f"Erro ao ler {perf_csv}: {e}")

    if mon_csv.exists():
        try:
            df = pd.read_csv(mon_csv)

            # Converter colunas para numerico
            cpu_col = 'CPU%(avg)'
            mem_col_gb = 'Memory(avg) [GB]'
            mem_col_mb = 'Memory(avg) [MB]'

            for col in [cpu_col, mem_col_gb, mem_col_mb]:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')

            # CPU
            if cpu_col in df.columns:
                data['avg_cpu'] = df[cpu_col].mean()

            # Memoria
            if mem_col_gb in df.columns and df[mem_col_gb].notna().sum() > 0:
                data['avg_memory_gb'] = df[mem_col_gb].mean()
            elif mem_col_mb in df.columns and df[mem_col_mb].notna().sum() > 0:
                data['avg_memory_gb'] = df[mem_col_mb].mean() / 1024
            else:
                data['avg_memory_gb'] = None
        except Exception as e:
            log_warning(f"Erro ao ler {mon_csv}: {e}")

    return data

def main():
    log_section("ANALISE CONSOLIDADA DE EXPERIMENTOS")

    # Diretorio base
    base_dir = Path(__file__).parent
    experiments_dir = base_dir / 'reports_csv' / 'experiments'

    if not experiments_dir.exists():
        log_error(f"Diretorio de experimentos nao encontrado: {experiments_dir}")
        log_error("Execute os experimentos primeiro usando: run-all-experiments.sh")
        sys.exit(1)

    # Listar experimentos
    experiments = [d for d in experiments_dir.iterdir() if d.is_dir()]

    if not experiments:
        log_error("Nenhum experimento encontrado")
        sys.exit(1)

    log_info(f"Encontrados {len(experiments)} experimentos")

    # Coletar dados de todos experimentos
    results = []

    for exp_dir in experiments:
        exp_name = exp_dir.name
        log_info(f"Processando: {exp_name}")

        # Parse nome
        exp_info = parse_experiment_name(exp_name)
        if not exp_info:
            log_warning(f"  Nao foi possivel parsear nome do experimento: {exp_name}")
            continue

        # Carregar CSVs
        metrics = load_experiment_csvs(exp_dir)

        if not metrics:
            log_warning(f"  Nenhuma metrica encontrada para {exp_name}")
            continue

        # Combinar informacoes
        result = {**exp_info, **metrics}
        results.append(result)

        log_success(f"  Metricas carregadas: throughput={metrics.get('throughput', 'N/A'):.2f} TPS")

    if not results:
        log_error("Nenhum resultado valido encontrado")
        sys.exit(1)

    # Criar DataFrame
    df = pd.DataFrame(results)

    # Ordenar por throughput (decrescente) e latencia (crescente)
    df_sorted = df.sort_values(by=['throughput', 'avg_latency'], ascending=[False, True])

    # ==========================================
    # EXIBIR RESULTADOS
    # ==========================================

    log_section("TABELA COMPARATIVA DE RESULTADOS")

    # Selecionar colunas para display
    display_cols = ['experiment', 'nodes', 'blocktime', 'consensus', 'version',
                   'throughput', 'avg_latency', 'success_rate', 'avg_cpu', 'avg_memory_gb']

    # Filtrar colunas que existem
    display_cols = [col for col in display_cols if col in df_sorted.columns]

    # Formatar valores
    df_display = df_sorted[display_cols].copy()

    if 'throughput' in df_display.columns:
        df_display['throughput'] = df_display['throughput'].apply(lambda x: f"{x:.2f}" if pd.notna(x) else "N/A")
    if 'avg_latency' in df_display.columns:
        df_display['avg_latency'] = df_display['avg_latency'].apply(lambda x: f"{x:.4f}" if pd.notna(x) else "N/A")
    if 'success_rate' in df_display.columns:
        df_display['success_rate'] = df_display['success_rate'].apply(lambda x: f"{x:.2f}" if pd.notna(x) else "N/A")
    if 'avg_cpu' in df_display.columns:
        df_display['avg_cpu'] = df_display['avg_cpu'].apply(lambda x: f"{x:.2f}" if pd.notna(x) else "N/A")
    if 'avg_memory_gb' in df_display.columns:
        df_display['avg_memory_gb'] = df_display['avg_memory_gb'].apply(lambda x: f"{x:.2f}" if pd.notna(x) else "N/A")

    print("\n" + df_display.to_string(index=False))

    # ==========================================
    # IDENTIFICAR MELHOR CONFIGURACAO
    # ==========================================

    log_section("MELHOR CONFIGURACAO")

    # Criterio: maior throughput
    best = df_sorted.iloc[0]

    print(f"\nExperimento: {best['experiment']}")
    print(f"Configuracao:")
    print(f"  Nos: {best['nodes']}")
    print(f"  Tempo de bloco: {best['blocktime']}s")
    print(f"  Consenso: {best['consensus'].upper()}")
    print(f"  Versao Besu: {best['version']}")
    print(f"\nMetricas:")
    print(f"  Throughput: {best['throughput']:.2f} TPS")
    print(f"  Latencia media: {best['avg_latency']:.4f}s")

    if 'success_rate' in best and pd.notna(best['success_rate']):
        print(f"  Taxa de sucesso: {best['success_rate']:.2f}%")
    if 'avg_cpu' in best and pd.notna(best['avg_cpu']):
        print(f"  CPU medio: {best['avg_cpu']:.2f}%")
    if 'avg_memory_gb' in best and pd.notna(best['avg_memory_gb']):
        print(f"  Memoria media: {best['avg_memory_gb']:.2f} GB")

    # ==========================================
    # SALVAR RESULTADOS
    # ==========================================

    log_section("SALVANDO RESULTADOS")

    # Criar timestamp para os arquivos consolidados
    analysis_timestamp = pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')

    # Salvar CSV completo com timestamp
    output_csv = base_dir / 'reports_csv' / 'experiments' / f'CONSOLIDATED_RESULTS_{analysis_timestamp}.csv'
    df_sorted.to_csv(output_csv, index=False)
    log_success(f"CSV consolidado salvo: {output_csv}")

    # Manter tambem uma copia como latest (para compatibilidade)
    output_csv_latest = base_dir / 'reports_csv' / 'experiments' / 'CONSOLIDATED_RESULTS.csv'
    df_sorted.to_csv(output_csv_latest, index=False)
    log_success(f"CSV latest salvo: {output_csv_latest}")

    # Salvar relatorio texto com timestamp
    output_txt = base_dir / 'reports_csv' / 'experiments' / f'ANALYSIS_REPORT_{analysis_timestamp}.txt'

    with open(output_txt, 'w') as f:
        f.write("="*60 + "\n")
        f.write("RELATORIO DE ANALISE DE EXPERIMENTOS\n")
        f.write("="*60 + "\n\n")

        f.write(f"Total de experimentos: {len(results)}\n")
        f.write(f"Data da analise: {pd.Timestamp.now()}\n\n")

        f.write("="*60 + "\n")
        f.write("MELHOR CONFIGURACAO (por throughput)\n")
        f.write("="*60 + "\n\n")

        f.write(f"Experimento: {best['experiment']}\n\n")
        f.write("Configuracao:\n")
        f.write(f"  Nos: {best['nodes']}\n")
        f.write(f"  Tempo de bloco: {best['blocktime']}s\n")
        f.write(f"  Consenso: {best['consensus'].upper()}\n")
        f.write(f"  Versao Besu: {best['version']}\n\n")

        f.write("Metricas:\n")
        f.write(f"  Throughput: {best['throughput']:.2f} TPS\n")
        f.write(f"  Latencia media: {best['avg_latency']:.4f}s\n")

        if 'success_rate' in best and pd.notna(best['success_rate']):
            f.write(f"  Taxa de sucesso: {best['success_rate']:.2f}%\n")
        if 'avg_cpu' in best and pd.notna(best['avg_cpu']):
            f.write(f"  CPU medio: {best['avg_cpu']:.2f}%\n")
        if 'avg_memory_gb' in best and pd.notna(best['avg_memory_gb']):
            f.write(f"  Memoria media: {best['avg_memory_gb']:.2f} GB\n")

        f.write("\n" + "="*60 + "\n")
        f.write("RANKING COMPLETO (ordenado por throughput)\n")
        f.write("="*60 + "\n\n")

        for idx, row in df_sorted.iterrows():
            f.write(f"{row['experiment']}: {row['throughput']:.2f} TPS\n")

        f.write("\n" + "="*60 + "\n")
        f.write("OBSERVACOES\n")
        f.write("="*60 + "\n\n")

        # Analise por parametro
        f.write("Impacto do numero de nos:\n")
        for nodes in sorted(df['nodes'].unique()):
            subset = df[df['nodes'] == nodes]
            avg_tps = subset['throughput'].mean()
            f.write(f"  {nodes} nos: {avg_tps:.2f} TPS medio\n")

        f.write("\nImpacto do tempo de bloco:\n")
        for bt in sorted(df['blocktime'].unique()):
            subset = df[df['blocktime'] == bt]
            avg_tps = subset['throughput'].mean()
            f.write(f"  {bt}s: {avg_tps:.2f} TPS medio\n")

        f.write("\nImpacto do consenso:\n")
        for cons in df['consensus'].unique():
            subset = df[df['consensus'] == cons]
            avg_tps = subset['throughput'].mean()
            f.write(f"  {cons.upper()}: {avg_tps:.2f} TPS medio\n")

        f.write("\nImpacto da versao:\n")
        for ver in sorted(df['version'].unique()):
            subset = df[df['version'] == ver]
            avg_tps = subset['throughput'].mean()
            f.write(f"  {ver}: {avg_tps:.2f} TPS medio\n")

    log_success(f"Relatorio texto salvo: {output_txt}")

    # Manter tambem uma copia como latest (para compatibilidade)
    output_txt_latest = base_dir / 'reports_csv' / 'experiments' / 'ANALYSIS_REPORT.txt'
    with open(output_txt, 'r') as f_in:
        with open(output_txt_latest, 'w') as f_out:
            f_out.write(f_in.read())
    log_success(f"Relatorio latest salvo: {output_txt_latest}")

    log_section("ANALISE CONCLUIDA")

    log_info("Arquivos gerados:")
    log_info(f"  1. {output_csv}")
    log_info(f"  2. {output_txt}")
    log_info(f"  3. {output_csv_latest} (latest)")
    log_info(f"  4. {output_txt_latest} (latest)")
    log_info("")
    log_success("Analise finalizada com sucesso!")

if __name__ == '__main__':
    main()
