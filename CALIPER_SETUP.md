# Hyperledger Caliper - Guia de Configuração
 Índice
- [Pré-requisitos](#pré-requisitos)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Configurações](#configurações)
- [Como Executar os Testes](#como-executar-os-testes)
- [Interpretando Resultados](#interpretando-resultados)
- [Troubleshooting](#troubleshooting)

---

## Pré-requisitos

### Ambiente Requerido:
- **Node.js**: v14+
- **npm**: v6+
- **Docker**: Para monitoramento de recursos dos nós Besu
- **Rede Hyperledger Besu**: Rodando com 6 nós

### Informações da Rede Besu:
- **RPC URLs**: http://127.0.0.1:8545 - http://127.0.0.1:8550
- **WebSocket URLs**: ws://127.0.0.1:8645 - ws://127.0.0.1:8650
- **Chain ID**: 381660001
- **Containers Docker**: node1, node2, node3, node4, node5, node6

### Contrato Deployado:
- **Nome**: NodeHealthMonitor
- **Endereço**: 0xa50a51c09a5c451C52BB714527E1974b686D8e77
- **Localização do projeto**: /home/cpqd/Documentos/contracts-node-health-monitor

---

## Estrutura do Projeto

```
Hyperleadger-Caliper/
├── networks/
│   └── besu/
│       └── networkconfig.json          # Configuração da rede Besu
├── benchmarks/
│   └── scenario-monitoring/
│       ├── config.yaml                 # Configuração do benchmark
│       └── workload/
│           ├── reportStatus.js         # Workload para reportStatus
│           └── getLatestStatus.js      # Workload para getLatestStatus
├── contracts/
│   └── NodeHealthMonitor/
│       ├── NodeHealthMonitor.json      # ABI do contrato
│       └── NodeHealthMonitor.sol       # Código fonte do contrato
├── package.json                         # Dependências do projeto
├── run-benchmark.sh                     # Script de execução
└── README.md
```

---

## Configurações

### 1. Instalação de Dependências

```bash
cd /home/cpqd/Documentos/Hyperleadger-Caliper

# Instalar dependências
npm install

# Verificar instalação do Caliper
npx caliper --version
```

### 2. Arquivo de Configuração de Rede (networkconfig.json)

**Localização**: `networks/besu/networkconfig.json`

**Configurações Principais**:
```json
{
  "caliper": {
    "blockchain": "ethereum"
  },
  "ethereum": {
    "url": "ws://127.0.0.1:8646",
    "fromAddress": "0xfe3b557e8fb62b89f4916b721be55ceb828dbd73",
    "fromAddressPrivateKey": "0x8f2a55949038a9610f50fb23b5883af3b4ecb3c3bb792cbcefbd1542c692be63",
    "chainId": 381660001,
    "transactionConfirmationBlocks": 1,
    "contracts": {
      "NodeHealthMonitor": {
        "address": "0xa50a51c09a5c451C52BB714527E1974b686D8e77",
        "estimateGas": true,
        "gas": {...}
      }
    }
  }
}
```

**Campos Importantes**:
- `url`: WebSocket URL do nó Besu (nó 2 na porta 8646)
- `fromAddress`: Endereço da conta que enviará as transações
- `fromAddressPrivateKey`: Chave privada da conta (com prefixo 0x)
- `chainId`: ID da rede Besu (381660001)
- `transactionConfirmationBlocks`: Número de blocos para confirmar transação
- `contracts.NodeHealthMonitor.address`: Endereço do contrato deployado

### 3. Arquivo de Configuração do Benchmark (config.yaml)

**Localização**: `benchmarks/scenario-monitoring/config.yaml`

**Estrutura Básica**:
```yaml
test:
  name: NodeHealthMonitor Benchmark
  description: Teste de desempenho do contrato NodeHealthMonitor
  workers:
    number: 2                     # Número de workers paralelos
  rounds:
    - label: ReportStatus
      description: Envia relatórios de status
      txNumber: 50                # Número total de transações
      rateControl:
        type: fixed-rate
        opts:
          tps: 5                  # Transações por segundo
      workload:
        module: benchmarks/scenario-monitoring/workload/reportStatus.js
```

**Parâmetros de Controle de Taxa**:
- `fixed-rate`: Taxa fixa de TPS
- `linear-rate`: Taxa que aumenta/diminui linearmente
- `zero-rate`: Envia todas as transações imediatamente

### 4. Workloads

#### reportStatus.js
Envia transações para registrar status dos nós.

**Parâmetros da função `reportStatus`**:
- `severity` (uint8): 0=OK, 1=Warning, 2=Critical
- `statusHash` (bytes32): Hash identificador do status
- `optionalDetails` (string): Detalhes adicionais

**Código do Workload**:
```javascript
const severity = Math.floor(Math.random() * 3); // 0-2
const statusHash = '0x' + crypto.randomBytes(32).toString('hex');
const optionalDetails = `Worker ${this.workerIndex} status report`;

const args = {
    contract: 'NodeHealthMonitor',
    verb: 'reportStatus',
    args: [severity.toString(), statusHash, optionalDetails],
};

await this.sutAdapter.sendRequests(args);
```

---

## Como Executar os Testes

### Opção 1: Usando o Script

```bash
# Tornar o script executável (primeira vez)
chmod +x run-benchmark.sh

# Executar o benchmark
./run-benchmark.sh
```

O script realiza automaticamente:
1. Verifica conectividade com a rede Besu
2. Valida se o contrato está deployado
3. Executa o benchmark
4. Exibe localização dos relatórios gerados

### Opção 2: Comando Manual

```bash
npx caliper launch manager \
  --caliper-workspace ./ \
  --caliper-benchconfig benchmarks/scenario-monitoring/config.yaml \
  --caliper-networkconfig networks/besu/networkconfig.json \
  --caliper-flow-only-test
```

### Opção 3: Testes Incrementais

Para testar diferentes TPSs sequencialmente:

```bash
# Edite config.yaml com diferentes valores de TPS
# Exemplo: tps: 10, depois tps: 20, etc.

for tps in 5 10 20 40 60; do
  echo "Testando com $tps TPS..."
  sed -i "s/tps: .*/tps: $tps/" benchmarks/scenario-monitoring/config.yaml
  ./run-benchmark.sh
  sleep 5
done
```

---

## Interpretando Resultados

### Arquivos Gerados

Após a execução, os seguintes arquivos são criados:
- `report.html`: Relatório visual interativo
- `report.json`: Dados brutos em JSON

### Métricas Principais

#### Tabela de Resultados
```
+--------------+------+------+-----------------+-----------------+-----------------+-----------------+------------------+
| Name         | Succ | Fail | Send Rate (TPS) | Max Latency (s) | Min Latency (s) | Avg Latency (s) | Throughput (TPS) |
|--------------|------|------|-----------------|-----------------|-----------------|-----------------|------------------|
| ReportStatus | 25   | 25   | 5.2             | 14.96           | 5.70            | 10.37           | 0.2              |
+--------------+------+------+-----------------+-----------------+-----------------+-----------------+------------------+
```

**Significado das Colunas**:
- **Succ**: Número de transações bem-sucedidas
- **Fail**: Número de transações que falharam
- **Send Rate (TPS)**: Taxa na qual transações foram enviadas
- **Max/Min/Avg Latency**: Latência máxima, mínima e média (em segundos)
- **Throughput (TPS)**: Taxa efetiva de transações confirmadas

### Taxa de Sucesso

```
Taxa de Sucesso = (Succ / (Succ + Fail)) × 100%
Exemplo: (25 / 50) × 100% = 50%
```

**Meta**: >95% de taxa de sucesso

### Throughput vs Send Rate

- **Send Rate**: Velocidade de envio das transações
- **Throughput**: Velocidade efetiva de confirmação
- **Ideal**: Throughput próximo ao Send Rate

Se Throughput << Send Rate → Rede congestionada ou timeouts

---

## Troubleshooting

### Problema 1: "Transaction was not mined within 50 blocks"

**Causa**: A rede Besu QBFT leva tempo para minar blocos (5 segundos por bloco padrão). 50 blocos = 250 segundos, mas o timeout do web3 pode ser menor.

**Solução**:
```json
// Em networkconfig.json, adicione:
"ethereum": {
  "transactionConfirmationBlocks": 1,  // Reduzir confirmações necessárias
  "contractDeployerConfig": {
    "timeout": 300000  // 5 minutos em ms
  }
}
```

### Problema 2: Erro "Known transaction"

**Causa**: Tentativa de enviar transação duplicada ou função view sendo chamada como transação.

**Solução**:
- Verifique se a função do contrato é `view` ou `pure`
- Funções read-only não devem estar no benchmark de transações
- Remova rounds que testam funções view

### Problema 3: Baixo Throughput

**Causas Possíveis**:
1. Rede congestionada
2. Período de bloco muito alto (5s é alto para testes)
3. Gas limit configurado incorretamente
4. TPS configurado muito alto para a rede

**Soluções**:
```yaml
# Reduzir TPS no config.yaml
rateControl:
  type: fixed-rate
  opts:
    tps: 2  # Começar com valores baixos
```

```json
// Ajustar gas em networkconfig.json
"gas": {
  "reportStatus": 500000  // Reduzir se estiver muito alto
}
```

### Problema 4: "Error: Returned error: Known transaction"

**Causa**: Problemas de gestão de nonce quando múltiplos workers usam a mesma conta.

**Solução**:
```yaml
# Reduzir número de workers para 1
workers:
  number: 1
```

### Problema 5: Rede Besu não responde

**Verificação**:
```bash
# Verificar se containers estão rodando
docker ps | grep node

# Testar conectividade
curl -X POST --data '{"jsonrpc":"2.0","method":"net_listening","params":[],"id":1}' \
  http://127.0.0.1:8546
```

**Solução**:
```bash
# Reiniciar rede Besu
cd ~/Documentos/Hyperleadger-Besu
docker-compose restart
```

### Problema 6: Contrato não encontrado

**Verificação**:
```bash
# Verificar código do contrato
curl -X POST --data \
  '{"jsonrpc":"2.0","method":"eth_getCode","params":["0xa50a51c09a5c451C52BB714527E1974b686D8e77","latest"],"id":1}' \
  http://127.0.0.1:8546
```

Se retornar `"result":"0x"` → Contrato não está deployado

**Solução**:
```bash
# Re-deploy o contrato
cd /home/cpqd/Documentos/contracts-node-health-monitor
npx hardhat ignition deploy ignition/modules/NodeHealthMonitor.js --network besu

# Atualizar endereço em networkconfig.json
```

---

## Comandos Úteis

### Verificar Estado da Rede
```bash
# Listar blocos recentes
curl -X POST --data '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}' \
  http://127.0.0.1:8546

# Ver último bloco
curl -X POST --data '{"jsonrpc":"2.0","method":"eth_getBlockByNumber","params":["latest",false],"id":1}' \
  http://127.0.0.1:8546

# Verificar saldo da conta
curl -X POST --data \
  '{"jsonrpc":"2.0","method":"eth_getBalance","params":["0xfe3b557e8fb62b89f4916b721be55ceb828dbd73","latest"],"id":1}' \
  http://127.0.0.1:8546
```

### Monitorar Logs do Caliper
```bash
# Durante execução, logs são exibidos no console
# Para salvar logs:
./run-benchmark.sh 2>&1 | tee caliper-run-$(date +%Y%m%d-%H%M%S).log
```

### Limpar Ambiente
```bash
# Remover arquivos de relatório antigos
rm -f report.html report.json

# Limpar cache do npm
npm cache clean --force

# Reinstalar dependências
rm -rf node_modules package-lock.json
npm install
```

---

## Próximos Passos

1. **Otimizar Configurações**: Ajuste TPS, workers e timeouts baseado nos resultados iniciais
2. **Adicionar Monitoramento**: Configure Docker monitoring em config.yaml
3. **Testes de Carga Progressiva**: Aumente gradualmente o TPS
4. **Análise de Recursos**: Use os dados de CPU/memória para identificar gargalos
5. **Documentar Resultados**: Mantenha histórico de testes e métricas

---

## Referências

- [Hyperledger Caliper Documentation](https://hyperledger.github.io/caliper/)
- [Caliper Ethereum Adapter](https://github.com/hyperledger/caliper-benchmarks/tree/main/networks/ethereum)
- [Hyperledger Besu Documentation](https://besu.hyperledger.org/)
- [Web3.js Documentation](https://web3js.readthedocs.io/)
