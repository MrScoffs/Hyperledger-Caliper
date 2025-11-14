# 📘 NodeHealthMonitor Performance Evaluation using Hyperledger Caliper

Este repositório apresenta uma estrutura de testes de carga automatizados para o contrato inteligente NodeHealthMonitor dentre outros, utilizando o framework Hyperledger Caliper sobre uma rede permissionada baseada em Hyperledger Besu.

---

## ⚙️ Requisitos

- **Node.js** versão 18 (utilizando NVM)
- **Docker** e **Docker Compose**
- **Rede Blockchain Besu operacional**
  - Você pode utilizar uma rede própria **ou** basear-se no tutorial:  
    🔗 [besu-qbft-network](https://github.com/Freitasthur1/besu-qbft-network)
- **Contratos Inteligentes implantados** na rede
  - Use:  
    🔗 [contracts-node-health-monitor](https://github.com/Freitasthur1/contracts-node-health-monitor)

Após a implantação dos contratos, será possível extrair os **endereços de cada contrato** e inseri-los no arquivo de configuração do Caliper para os testes de desempenho.

---

## Instalação do Ambiente de Testes

### 1. Instalação do Node.js com NVM
```
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.3/install.sh | bash
nvm install 18
```

### 2. Instalação do Caliper CLI
```
npm install --only=prod @hyperledger/caliper-cli@0.5.0
```
### 3. Verificação da instalação

```
npx caliper --version
```
### 4. Bind do Caliper com Hyperledger Besu

```
npx caliper bind --caliper-bind-sut besu:latest
```
## Configuração dos Arquivos de Teste
### Arquivo networkconfig.json
Esse arquivo define os parâmetros de conexão com a rede Besu:

```
{
  "caliper": {
    "blockchain": "ethereum",
    "command": {}
  },
  "ethereum": {
    "url": "ws://localhost:8545",
    "fromAddress": "CARTEIRA_PUBLICA_ADM",
    "fromAddressPrivateKey": "CHAVE_PRIVADA_ADM",
    "transactionConfirmationBlocks": 10,
    "contracts": {
      "NodeHealthMonitor": {
        "address": "0x... ENDEREÇO DO CONTRATO",
        "estimateGas": true,
        "gas": {
          "reportStatus": 800000
        },
        "abi": [
          // ABI DO CONTRATO AQUI
        ]
      }
    }
  }
}

## Execução de Testes
### Execução Única

### NodeHealthMonitor
```
npx caliper launch manager \
  --caliper-workspace ./ \
  --caliper-benchconfig benchmarks/scenario-monitoring/NodeHealthMonitor/config-reportStatus.yaml \
  --caliper-networkconfig ./networks/besu/networkconfig.json \
  --caliper-bind-sut besu:latest \
  --caliper-flow-skip-install
``` 

### Simple
```
npx caliper launch manager \
  --caliper-workspace ./ \
  --caliper-benchconfig benchmarks/scenario-monitoring/Simple/config.yaml \
  --caliper-networkconfig ./networks/besu/networkconfig.json \
  --caliper-bind-sut besu:latest \
  --caliper-flow-skip-install
``` 

### ERC721 (fazer deploy do contrato correto)
```
npx caliper launch manager \
  --caliper-workspace ./ \
  --caliper-benchconfig benchmarks/scenario-monitoring/ERC721/config.yaml \
  --caliper-networkconfig ./networks/besu/networkconfig.json \
  --caliper-bind-sut besu:latest \
  --caliper-flow-skip-install
``` 

## Execução Automatizada (Scripts)

IMPORTANTE: O script run_testes_simple.py agora inclui:
- Verificacao automatica de conectividade com a rede Besu
- Implantacao automatica do contrato Simple antes dos testes
- Atualizacao automatica do networkconfig.json com o endereco do novo contrato
- Tempo de estabilizacao adicional (15 segundos) apos deploy do contrato

### 1. Executar uma bateria completa de testes

```
python3 run_testes_simple.py
```
Este script executa todos os testes definidos, gerando relatorios em HTML para cada rodada de iteracao.

O script realiza automaticamente:
1. Verificacao de conectividade com a rede Besu
2. Deploy do contrato Simple (se a rede foi reiniciada)
3. Aguardo de estabilizacao (15 segundos)
4. Execucao dos benchmarks para cada funcao (open, query, transfer)
5. Geracao de relatorios HTML e CSV

### 2. Extração de Resultados para Análise
a. Extrair métricas

```
python3 extract_csv.py
```

## Visualização de Resultados
```
python3 analise.py
```
