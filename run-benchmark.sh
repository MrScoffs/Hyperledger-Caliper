#!/bin/bash

# Script para executar benchmark do Caliper na rede Besu
#
# Uso: ./run-benchmark.sh

set -e

echo "========================================"
echo "Hyperledger Caliper - Benchmark Runner"
echo "========================================"
echo ""

# Verificar se a rede Besu está rodando
echo "1. Verificando conectividade com a rede Besu..."
if curl -s -X POST --data '{"jsonrpc":"2.0","method":"net_listening","params":[],"id":1}' http://127.0.0.1:8546 | grep -q '"result":true'; then
    echo "   ✓ Rede Besu está respondendo"
else
    echo "   ✗ ERRO: Rede Besu não está respondendo na porta 8546"
    echo "   Verifique se os containers Docker estão rodando: docker ps"
    exit 1
fi

# Verificar se o contrato está deployado
echo ""
echo "2. Verificando se o contrato está deployado..."
CONTRACT_CODE=$(curl -s -X POST --data '{"jsonrpc":"2.0","method":"eth_getCode","params":["0xa50a51c09a5c451C52BB714527E1974b686D8e77","latest"],"id":1}' http://127.0.0.1:8546 | grep -o '"result":"0x[^"]*"' | cut -d'"' -f4)
if [ "$CONTRACT_CODE" != "0x" ]; then
    echo "   ✓ Contrato NodeHealthMonitor encontrado em 0xa50a51c09a5c451C52BB714527E1974b686D8e77"
else
    echo "   ✗ ERRO: Contrato não encontrado no endereço configurado"
    exit 1
fi

echo ""
echo "3. Iniciando benchmark do Caliper..."
echo ""

# Executar Caliper
npx caliper launch manager \
  --caliper-workspace ./ \
  --caliper-benchconfig benchmarks/scenario-monitoring/config.yaml \
  --caliper-networkconfig networks/besu/networkconfig.json \
  --caliper-flow-only-test

echo ""
echo "========================================"
echo "Benchmark concluído!"
echo "========================================"
echo ""
echo "Resultados salvos em:"
echo "  - report.html (relatório visual)"
echo "  - report.json (dados brutos)"
echo ""
