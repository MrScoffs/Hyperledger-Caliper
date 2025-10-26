#  NodeHealthMonitor Performance Evaluation using Hyperledger Caliper

Este repositório apresenta uma estrutura de testes de carga automatizados para o contrato inteligente NodeHealthMonitor, utilizando o framework Hyperledger Caliper sobre uma rede permissionada baseada em Hyperledger Besu.

---

##  Requisitos

- **Node.js** versão 18 (utilizando NVM)
- **Docker** e **Docker Compose**
- **Rede Blockchain Besu operacional**
  - Você pode utilizar uma rede própria **ou** basear-se no tutorial:  
     [besu-production-docker](https://github.com/jeffsonsousa/besu-production-docker)
- **Contratos Inteligentes implantados** na rede
  - Use:  
     [contracts-node-health-monitor](https://github.com/jeffsonsousa/contracts-node-health-monitor)

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
    "url": "ws://localhost:8546",
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
```
### Arquivo de Benchmark (exemplo config-createDid.yaml)
```
simpleArgs: &simple-args
  reportStatus:
    [
      "2",
      "0xd49c718fabf7b90f17542e2e0989e3de8a2e1241c05d03e53abe6a1b2bdb197d",
      "Problema Detectado"
    ]
  numberOfAccounts: &number-of-accounts 5
  timeOfTest: &time-of-test 20

test:
  name: NodeHealthMonitor Load Test
  description: Avalia o desempenho do contrato NodeHealthMonitor.
  workers:
    number: 1
  rounds:
    - label: reportStatus
      txDuration: *time-of-test
      rateControl:
        type: fixed-rate
        opts:
          tps: 200
      workload:
        module: benchmarks/scenario-monitoring/NodeHealthMonitor/reportStatus.js
        arguments: *simple-args

monitors:
  resource:
    - module: docker
      options:
        interval: 5
        cpuUsageNormalization: true
        containers:
          - /node1
          - /node2
          - /node3
          - /node4
          - /node5
          - /node6
        stats:
          memory:
            max: true
            avg: true
          cpu:
            max: true
            avg: true
          networkIO:
            enabled: true
          diskIO:
            enabled: true
        charting:
          bar:
            metrics: [Memory(avg), CPU%(avg)]
          polar:
            metrics: [all]

observer:
  type: local
  interval: 5


```

## Execução de Testes
### Execução Única

```
npx caliper launch manager \
  --caliper-workspace ./ \
  --caliper-benchconfig benchmarks/scenario-monitoring/NodeHealthMonitor/config-reportStatus.yaml \
  --caliper-networkconfig ./networks/besu/networkconfig.json \
  --caliper-bind-sut besu:latest \
  --caliper-flow-skip-install
``` 
## Execução Automatizada (Scripts)
### 1. Executar uma bateria completa de testes
```
python run_test_local.py
```
Este script executa todos os testes definidos, gerando relatórios em HTML para cada rodada de iteração.

### 2. Extração de Resultados para Análise
a. Extrair métricas agregadas (TPS, Latência, Taxa de Sucesso)

```
cd src/
python extract_report_to_csv.py
```

b. Extrair métricas de recursos (CPU, memória, disco, rede)
```
python extract_resource_to_csv.py
```

## Visualização de Resultados
Os notebooks Jupyter permitem a visualização gráfica dos resultados:
### Gráficos de Uso de Recursos (CPU, Memória)
```
jupyter notebook plot_resources.ipynb
```
### Gráficos de Desempenho (TPS, Latência)
```
jupyter notebook plot_summary.ipynb
```
## Considerações Finais

Este projeto permite testes de carga no contrato NodeHealthMonitor, medindo desempenho funcional e impacto computacional. Ideal para:

* Monitoramento descentralizado em blockchain
* Benchmark de infraestrutura de rede
* Avaliação de escalabilidade e resiliência

Para contribuições, dúvidas ou extensões, sinta-se à vontade para entrar em contato comigo por email: jeffson.celeiro@gmail.com, jcsousa@cpqd.com.br e jeffson.sousa@icen.ufpa.br. 

