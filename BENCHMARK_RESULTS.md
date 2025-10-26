# Relatório de Resultados - Hyperledger Caliper Benchmark

## Informações do Teste

**Data**: 2025-10-25
**Rede**: Hyperledger Besu QBFT (6 nós)
**Contrato**: NodeHealthMonitor (0xa50a51c09a5c451C52BB714527E1974b686D8e77)
**Ferramenta**: Hyperledger Caliper 0.5.0
**Executor**: Claude Code

---

## Configuração do Teste

### Rede Besu
- **Número de Nós**: 6 (node1 a node6)
- **Algoritmo de Consenso**: QBFT (Istanbul BFT)
- **Período de Bloco**: 5 segundos
- **Chain ID**: 381660001
- **Conexão**: WebSocket (ws://127.0.0.1:8646)

### Configuração do Contrato
```
Contrato: NodeHealthMonitor
Endereço: 0xa50a51c09a5c451C52BB714527E1974b686D8e77
Função testada: reportStatus(uint8 severity, bytes32 statusHash, string optionalDetails)
```

### Configuração do Caliper
```yaml
Workers: 2
Método de Controle de Taxa: fixed-rate
TPS Configurado: 5
Número de Transações: 50
Duração: Baseada em txNumber
```

---

##  Resultados - Round 1: ReportStatus

### Sumário Executivo

```
+--------------+------+------+-----------------+-----------------+-----------------+-----------------+------------------+
| Name         | Succ | Fail | Send Rate (TPS) | Max Latency (s) | Min Latency (s) | Avg Latency (s) | Throughput (TPS) |
|--------------|------|------|-----------------|-----------------|-----------------|-----------------|------------------|
| ReportStatus | 25   | 25   | 5.2             | 14.96           | 5.70            | 10.37           | 0.2              |
+--------------+------+------+-----------------+-----------------+-----------------+-----------------+------------------+
```

### Métricas Detalhadas

#### Taxa de Sucesso
- **Transações Bem-Sucedidas**: 25
- **Transações Falhadas**: 25
- **Taxa de Sucesso**: **50%** 
- **Taxa de Falha**: **50%** 

#### Performance de Throughput
- **Send Rate (TPS)**: 5.2 TPS
- **Throughput Real**: 0.2 TPS
- **Eficiência**: **3.8%** (0.2 / 5.2)
  - **Interpretação**: Apenas 3.8% da taxa de envio resultou em transações confirmadas

#### Latência
- **Mínima**: 5.70 segundos
- **Máxima**: 14.96 segundos
- **Média**: 10.37 segundos
- **Desvio Observado**: ~9.26 segundos

### Tempo de Execução
- **Duração Total do Round**: 263.073 segundos (~4.4 minutos)
- **Tempo Esperado** (50 tx ÷ 5 TPS): 10 segundos
- **Overhead**: 253 segundos devido a timeouts e falhas

---

## Análise de Falhas

### Tipos de Erros Encontrados

#### 1. Transaction Not Mined (25 ocorrências)
```
Error: Transaction was not mined within 50 blocks
```

**Análise**:
- **Causa Raiz**: Timeout de 50 blocos (50 × 5s = 250 segundos)
- **Nonces Afetados**: 0x3, 0x4, 0x5, 0x6, 0x7, 0x8, 0x9, 0xa, 0xb, 0xc, 0xd, 0xe, 0xf, 0x10, 0x11, 0x12, 0x13, 0x14, 0x15, 0x16, 0x17, 0x18, 0x19, 0x1a, 0x1b
- **Padrão**: Metade das transações (a partir do nonce 0x3) não foram confirmadas a tempo

**Impacto**:
- Reduz throughput efetivo
- Aumenta latência média
- Degrada taxa de sucesso

**Recomendações**:
1. Aumentar timeout no adapter Ethereum do Caliper
2. Reduzir TPS para 2-3 para dar mais tempo de mineração
3. Considerar usar HTTP RPC em vez de WebSocket para melhor handling de timeouts
4. Verificar se a rede QBFT está saudável e sem latência excessiva

---

## 🔍 Round 2: GetLatestStatus (Interrompido)

### Status
** Falha Completa**

### Erros Encontrados
```
Error: Returned error: Known transaction
```

**Ocorrências**: Todas as transações (50/50)

### Análise do Problema

A função `getLatestStatus` no contrato é definida como `view`:
```solidity
function getLatestStatus(address node) external view returns (NodeStatus memory)
```

**Problema**:
- Funções `view` são **read-only** e não modificam o estado
- Não devem ser executadas como transações (não requerem gas)
- Devem ser chamadas via `eth_call`, não `eth_sendTransaction`

**Causa do Erro "Known transaction"**:
- Caliper está tentando enviar transações com o mesmo nonce
- Como a função é view, não consome gas nem incrementa nonce
- Múltiplas tentativas com o mesmo nonce resultam em "Known transaction"

### Recomendações
1. **Remover o round GetLatestStatus** do benchmark de transações
2. Alternativamente, criar um benchmark separado para funções read-only usando Web3 calls diretas
3. Focar benchmarks do Caliper apenas em funções que modificam estado

---

## Conclusões e Recomendações

### Pontos Positivos 
1. Caliper está corretamente configurado e conectado à rede Besu
2. Contrato está deployado e acessível
3. 50% das transações foram bem-sucedidas, provando funcionalidade básica
4. Latência mínima de 5.7s está dentro do esperado para QBFT (período de bloco = 5s)

### Problemas Críticos 
1. **Alta Taxa de Falha (50%)**
   - Timeouts excessivos
   - Throughput muito baixo (0.2 TPS vs 5.2 TPS enviado)

2. **Workload GetLatestStatus Inadequado**
   - Função view não deve ser testada como transação
   - Requer restruturação do benchmark

3. **Latência Alta**
   - Média de 10.37s é mais que 2× o período de bloco
   - Indica possível congestionamento ou overhead do Caliper

### Recomendações de Melhoria

#### Curto Prazo:
1. **Ajustar Configuração do Benchmark**
   ```yaml
   workers:
     number: 1  # Reduzir para evitar conflitos de nonce
   rateControl:
     type: fixed-rate
     opts:
       tps: 2  # Reduzir para 2 TPS
   ```

2. **Remover Round GetLatestStatus**
   - Eliminar do config.yaml até implementação de read-only benchmark

3. **Aumentar Timeout**
   ```json
   "transactionConfirmationBlocks": 3,
   "contractDeployerConfig": {
     "timeout": 300000
   }
   ```

#### Médio Prazo:
1. **Implementar Monitoramento de Recursos**
   ```yaml
   monitors:
     resource:
       - module: docker
         options:
           interval: 5
           containers: ["/node1", "/node2", "/node3", "/node4", "/node5", "/node6"]
   ```

2. **Testes de Carga Progressiva**
   - Começar com 1 TPS
   - Aumentar gradualmente: 2, 5, 10, 20 TPS
   - Identificar ponto de saturação da rede

3. **Benchmark de Read Operations Separado**
   - Usar Web3.js diretamente para chamar `getLatestStatus`
   - Medir latência de leituras vs escritas

#### Longo Prazo:
1. **Otimização da Rede Besu**
   - Considerar reduzir período de bloco para 2-3 segundos
   - Ajustar parâmetros QBFT para melhor throughput

2. **Múltiplas Contas**
   - Distribuir transações entre múltiplas contas
   - Evitar contenção de nonce em alta carga

3. **Análise Comparativa**
   - Benchmarks com diferentes números de workers (1, 2, 4, 8)
   - Comparação HTTP vs WebSocket
   - Impacto de diferentes funções do contrato

---

## Gráficos e Visualizações (Sugeridos)

### Métricas para Visualizar:
1. **Taxa de Sucesso vs TPS**
   - Eixo X: TPS configurado
   - Eixo Y: % de sucesso
   - Esperado: Identificar TPS ótimo

2. **Latência vs Throughput**
   - Eixo X: Throughput (TPS)
   - Eixo Y: Latência média (s)
   - Esperado: Curva crescente

3. **Recursos por Nó**
   - CPU (%)
   - Memória (MB)
   - Identificar nós sob estresse

4. **Distribuição de Latência**
   - Histograma de latências
   - Identificar outliers

---

## Métricas Alvo (Metas Futuras)

Com base em redes QBFT similares:

| Métrica | Atual | Meta    |          |  Status  |
|---------|-------|---------|----------|          |
| Taxa de Sucesso | 50%     | >95%     |  Crítico |
| Throughput      | 0.2 TPS | 5-10 TPS |  Crítico |
| Latência Média  | 10.37s  | <10s     |  Limite  |
| Latência Mínima | 5.70s   | ~5s      |  OK      |
| Latência Máxima | 14.96s  | <15s     |  Limite  |

---

##  Próximos Passos

1.  Configuração inicial do Caliper
2.  Primeiro benchmark executado
3.  Problemas identificados
4.  Implementar correções sugeridas
5.  Re-executar benchmark com configurações otimizadas
6.  Coletar métricas de recursos (Docker monitoring)
7.  Realizar testes de carga progressiva
8.  Documentar resultados finais

---

## Apêndice

### Comando Executado
```bash
npx caliper launch manager \
  --caliper-workspace ./ \
  --caliper-benchconfig benchmarks/scenario-monitoring/config.yaml \
  --caliper-networkconfig networks/besu/networkconfig.json \
  --caliper-flow-only-test
```

### Arquivos de Configuração

#### networkconfig.json (Resumo)
```json
{
  "ethereum": {
    "url": "ws://127.0.0.1:8646",
    "fromAddress": "0xfe3b557e8fb62b89f4916b721be55ceb828dbd73",
    "chainId": 381660001,
    "contracts": {
      "NodeHealthMonitor": {
        "address": "0xa50a51c09a5c451C52BB714527E1974b686D8e77"
      }
    }
  }
}
```

#### config.yaml (Resumo)
```yaml
test:
  workers:
    number: 2
  rounds:
    - label: ReportStatus
      txNumber: 50
      rateControl:
        type: fixed-rate
        opts:
          tps: 5
```

### Ambiente de Execução
```
OS: Linux 6.8.0-85-generic
Node.js: v14+
Caliper: 0.5.0
Web3.js: 1.3.0
Docker: Sim (6 containers)
```

---

**Documento gerado por**: Claude Code
**Última atualização**: 2025-10-25
