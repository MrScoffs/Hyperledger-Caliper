import os
import pandas as pd
import matplotlib.pyplot as plt

# Caminho dos CSVs (ajuste se for outro diretório)
#REPORT_DIR = "./reports_csv/open"
#REPORT_DIR = "./reports_csv/query"
REPORT_DIR = "./reports_csv/transfer"
PERF_CSV = os.path.join(REPORT_DIR, "caliper_performance_metrics.csv")
MON_CSV = os.path.join(REPORT_DIR, "caliper_monitor_metrics.csv")

# =====================
# 1. Leitura dos dados
# =====================
perf_df = pd.read_csv(PERF_CSV)
mon_df = pd.read_csv(MON_CSV)

# ---- Normalização das colunas de performance ----
for col in ["Max Latency (s)", "Min Latency (s)", "Avg Latency (s)", "Throughput (TPS)", "TPS"]:
    if col in perf_df.columns:
        perf_df[col] = pd.to_numeric(perf_df[col], errors="coerce")

# ---- Seleciona colunas de CPU e Memória ----
cpu_col = "CPU%(avg)"
mem_col_gb = "Memory(avg) [GB]"
mem_col_mb = "Memory(avg) [MB]"

# Converte para número
for col in [cpu_col, mem_col_gb, mem_col_mb, "TPS"]:
    if col in mon_df.columns:
        mon_df[col] = pd.to_numeric(mon_df[col], errors="coerce")

# ---- Seleciona qual coluna de memória usar ----
if mon_df[mem_col_gb].notna().sum() > 0:
    mon_df["Memory_used_GB"] = mon_df[mem_col_gb]
elif mem_col_mb in mon_df.columns and mon_df[mem_col_mb].notna().sum() > 0:
    mon_df["Memory_used_GB"] = mon_df[mem_col_mb] / 1024  # converte MB → GB
else:
    raise ValueError("❌ Nenhuma coluna de memória válida encontrada no CSV!")

# =====================
# 2. Agrupar e calcular médias
# =====================
perf_grouped = (
    perf_df.groupby("TPS")[["Avg Latency (s)", "Throughput (TPS)"]]
    .mean()
    .reset_index()
)

mon_grouped = (
    mon_df.groupby("TPS")[["Memory_used_GB", cpu_col]]
    .mean()
    .reset_index()
)

# ---- Junta os dois ----
summary = pd.merge(perf_grouped, mon_grouped, on="TPS", how="inner")

print("\n📊 Médias por TPS:")
print(summary)

# =====================
# 3. Geração dos gráficos
# =====================

plt.figure(figsize=(10, 6))
plt.plot(summary["TPS"], summary["Avg Latency (s)"], marker="o")
plt.title("TPS × Latência Média (s)")
plt.xlabel("TPS")
plt.ylabel("Latência Média (s)")
plt.grid(True)
plt.show()

plt.figure(figsize=(10, 6))
plt.plot(summary["TPS"], summary["Throughput (TPS)"], marker="o", color="green")
plt.title("TPS × Throughput (TPS)")
plt.xlabel("TPS")
plt.ylabel("Throughput")
plt.grid(True)
plt.show()

plt.figure(figsize=(10, 6))
plt.plot(summary["TPS"], summary[cpu_col], marker="o", color="red")
plt.title("TPS × CPU Média (%)")
plt.xlabel("TPS")
plt.ylabel("CPU Média (%)")
plt.grid(True)
plt.show()

plt.figure(figsize=(10, 6))
plt.plot(summary["TPS"], summary["Memory_used_GB"], marker="o", color="purple")
plt.title("TPS × Memória Média (GB)")
plt.xlabel("TPS")
plt.ylabel("Memória Média (GB)")
plt.grid(True)
plt.show()
