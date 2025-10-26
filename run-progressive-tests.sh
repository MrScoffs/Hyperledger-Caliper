#!/bin/bash

# Script para executar testes progressivos de TPS
# Objetivo: Encontrar o TPS ótimo da rede Besu

set -e

echo "========================================"
echo "Testes Progressivos de TPS - Caliper"
echo "========================================"
echo ""

# Criar diretório para resultados
RESULTS_DIR="progressive_results_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$RESULTS_DIR"

echo "Resultados serão salvos em: $RESULTS_DIR"
echo ""

# Array de TPSs para testar
TPS_VALUES=(3 4 5 6 8 10)

# Arquivo de resumo
SUMMARY_FILE="$RESULTS_DIR/summary.txt"
echo "TPS,Sucesso,Falha,Taxa_Sucesso(%),Send_Rate,Throughput,Eficiencia(%),Lat_Min,Lat_Avg,Lat_Max,Duracao(s)" > "$SUMMARY_FILE"

# Loop pelos valores de TPS
for tps in "${TPS_VALUES[@]}"; do
    echo "========================================"
    echo "Teste com TPS = $tps"
    echo "========================================"

    # Atualizar config.yaml com novo TPS
    sed -i "s/tps: .*/tps: $tps/" benchmarks/scenario-monitoring/config.yaml

    # Limpar relatórios antigos
    rm -f report.html report.json

    # Executar benchmark
    echo "Executando benchmark..."
    npx caliper launch manager \
      --caliper-workspace ./ \
      --caliper-benchconfig benchmarks/scenario-monitoring/config.yaml \
      --caliper-networkconfig networks/besu/networkconfig.json \
      --caliper-flow-only-test \
      2>&1 | tee "$RESULTS_DIR/output_tps_${tps}.log"

    # Salvar relatórios
    if [ -f "report.html" ]; then
        cp report.html "$RESULTS_DIR/report_tps_${tps}.html"
    fi

    # Extrair métricas do log
    METRICS=$(grep -A 5 "### Test result ###" "$RESULTS_DIR/output_tps_${tps}.log" | tail -1 | awk '{print $2","$3","$4","$5","$6","$7","$8}')

    # Extrair duração
    DURACAO=$(grep "Finished round" "$RESULTS_DIR/output_tps_${tps}.log" | tail -1 | awk '{print $(NF-1)}')

    # Salvar no resumo
    if [ ! -z "$METRICS" ]; then
        # Calcular taxa de sucesso
        SUCC=$(echo "$METRICS" | cut -d',' -f1)
        FAIL=$(echo "$METRICS" | cut -d',' -f2)
        TOTAL=$((SUCC + FAIL))
        TAXA_SUCESSO=$(awk "BEGIN {printf \"%.1f\", ($SUCC/$TOTAL)*100}")

        # Calcular eficiência (Throughput / Send Rate * 100)
        SEND_RATE=$(echo "$METRICS" | cut -d',' -f3)
        THROUGHPUT=$(echo "$METRICS" | cut -d',' -f7)
        EFICIENCIA=$(awk "BEGIN {printf \"%.1f\", ($THROUGHPUT/$SEND_RATE)*100}")

        echo "$tps,$METRICS,$TAXA_SUCESSO,$EFICIENCIA,$DURACAO" >> "$SUMMARY_FILE"

        echo ""
        echo "Resultado: $SUCC sucessos, $FAIL falhas ($TAXA_SUCESSO% sucesso)"
        echo "Throughput: $THROUGHPUT TPS (Eficiência: $EFICIENCIA%)"
        echo ""
    else
        echo "$tps,ERROR,ERROR,0,0,0,0,0,0,0,0" >> "$SUMMARY_FILE"
        echo "ERRO: Não foi possível extrair métricas"
        echo ""
    fi

    # Aguardar 10 segundos antes do próximo teste
    if [ "$tps" != "${TPS_VALUES[-1]}" ]; then
        echo "Aguardando 10 segundos antes do próximo teste..."
        sleep 10
    fi
done

echo "========================================"
echo "Todos os testes concluídos!"
echo "========================================"
echo ""
echo "Resumo dos resultados:"
echo ""
column -t -s',' "$SUMMARY_FILE"
echo ""
echo "Resultados detalhados salvos em: $RESULTS_DIR/"
echo ""
