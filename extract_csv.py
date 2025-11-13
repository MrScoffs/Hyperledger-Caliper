#!/usr/bin/env python3
"""
Script para extrair metricas de relatorios HTML do Caliper
Processa relatorios na estrutura: reports_htmls/experiments/{experiment_name}/
Gera CSVs na estrutura: reports_csv/experiments/{experiment_name}/
"""

import os
import re
import pandas as pd
from bs4 import BeautifulSoup
from pathlib import Path

# Cores para output
class Colors:
    BLUE = '\033[0;34m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    RED = '\033[0;31m'
    NC = '\033[0m'

def log_info(msg):
    print(f"{Colors.BLUE}[INFO]{Colors.NC} {msg}")

def log_success(msg):
    print(f"{Colors.GREEN}[OK]{Colors.NC} {msg}")

def log_warning(msg):
    print(f"{Colors.YELLOW}[WARN]{Colors.NC} {msg}")

def log_error(msg):
    print(f"{Colors.RED}[ERROR]{Colors.NC} {msg}")

# Caminhos
base_dir = Path(__file__).parent
REPORTS_DIR = base_dir / "reports_htmls" / "experiments"
OUTPUT_DIR = base_dir / "reports_csv" / "experiments"

# Cria a pasta base de saída, se não existir
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Função auxiliar para converter strings numéricas
def try_float(x):
    try:
        return float(x)
    except:
        return x

def extract_table_data(soup, table_type="performance"):
    """Extrai dados de tabelas do HTML do Caliper"""
    data = []

    if table_type == "performance":
        # Procura pela tabela de Performance metrics
        perf_header = soup.find("h3", string=lambda s: s and "Performance metrics" in s)
        if not perf_header:
            return data
        table = perf_header.find_next("table")

    elif table_type == "monitor":
        # Procura pela tabela de Resource monitor
        mon_header = soup.find("h4", string=lambda s: s and "Resource monitor" in s)
        if not mon_header:
            return data
        # A tabela de recursos geralmente é a segunda tabela após o header
        table = mon_header.find_next("table")
        if table:
            next_table = table.find_next("table")
            if next_table:
                table = next_table
    else:
        return data

    if not table:
        return data

    # Extrai headers
    headers = [th.text.strip() for th in table.find_all("th")]
    if not headers:
        return data

    # Extrai linhas
    for row in table.find_all("tr")[1:]:  # Pula header
        values = [td.text.strip() for td in row.find_all("td")]
        if values and len(values) == len(headers):
            record = dict(zip(headers, values))
            data.append(record)

    return data

# Verifica se diretório de relatórios existe
if not REPORTS_DIR.exists():
    log_error(f"Diretorio de relatorios nao encontrado: {REPORTS_DIR}")
    log_error("Execute os experimentos primeiro")
    exit(1)

# Percorre os experimentos
experiments = [d for d in REPORTS_DIR.iterdir() if d.is_dir()]

if not experiments:
    log_error("Nenhum experimento encontrado")
    exit(1)

log_info(f"Encontrados {len(experiments)} experimentos")

total_processed = 0
total_failed = 0

for exp_dir in experiments:
    exp_name = exp_dir.name
    log_info(f"Processando: {exp_name}")

    # Cria diretório de saída para este experimento
    output_exp_dir = OUTPUT_DIR / exp_name
    output_exp_dir.mkdir(parents=True, exist_ok=True)

    performance_data = []
    monitor_data = []

    # Processa todos os arquivos HTML no diretório do experimento
    html_files = list(exp_dir.glob("*.html"))

    if not html_files:
        log_warning(f"  Nenhum arquivo HTML encontrado")
        total_failed += 1
        continue

    for html_file in html_files:
        try:
            with open(html_file, "r", encoding="utf-8") as f:
                soup = BeautifulSoup(f, "lxml")

            # Extrai dados de performance
            perf_rows = extract_table_data(soup, "performance")
            for row in perf_rows:
                row["Test Type"] = html_file.stem  # Nome do arquivo sem extensão
                performance_data.append(row)

            # Extrai dados de monitoramento
            mon_rows = extract_table_data(soup, "monitor")
            for row in mon_rows:
                row["Test Type"] = html_file.stem
                monitor_data.append(row)

        except Exception as e:
            log_warning(f"  Erro ao processar {html_file.name}: {e}")
            continue

    # Salva os CSVs
    saved_files = []

    if performance_data:
        perf_df = pd.DataFrame(performance_data)
        perf_csv = output_exp_dir / "caliper_performance_metrics.csv"
        perf_df.to_csv(perf_csv, index=False)
        saved_files.append("performance")

    if monitor_data:
        monitor_df = pd.DataFrame(monitor_data)
        mon_csv = output_exp_dir / "caliper_monitor_metrics.csv"
        monitor_df.to_csv(mon_csv, index=False)
        saved_files.append("monitor")

    if saved_files:
        log_success(f"  CSVs criados: {', '.join(saved_files)}")
        total_processed += 1
    else:
        log_warning(f"  Nenhum dado extraido")
        total_failed += 1

# Resumo
print(f"\n{'='*60}")
log_info(f"Total processados com sucesso: {total_processed}")
if total_failed > 0:
    log_warning(f"Total com problemas: {total_failed}")
log_success("Extracao concluida!")
