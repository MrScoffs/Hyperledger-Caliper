import os
import subprocess
import time
from datetime import datetime
import sys

num_testes = 5
# Caminhos para cada configuração de função
BENCHMARK_FILES = {
     "open": "benchmarks/scenario-monitoring/Simple/config-open.yaml",
     "query": "benchmarks/scenario-monitoring/Simple/config-query.yaml",
     "transfer": "benchmarks/scenario-monitoring/Simple/config-transfer.yaml",
    #"simple": "benchmarks/scenario-monitoring/Simple/config.yaml",
    #"getLatestStatus": 'benchmarks/scenario-monitoring/NodeHealthMonitor/config-getLatestStatus.yaml',
    #"reportStatus": 'benchmarks/scenario-monitoring/NodeHealthMonitor/config-reportStatus.yaml',
    #"statusReports": 'benchmarks/scenario-monitoring/NodeHealthMonitor/config-statusReports.yaml'
}

TPS_LIST_OPEN = [60, 80, 100, 120, 140, 160, 180] #open
TPS_LIST_QUERY = [100, 200, 300, 400, 500, 600, 700] # query
TPS_LIST_TRANSFER = [70, 80, 90, 100, 110] # transfer
TPS_LIST = [10]

# Atualiza o valor de TPS no arquivo de benchmark YAML
def update_tps_in_file(file_path, tps):
    with open(file_path, 'r') as file:
        lines = file.readlines()

    new_lines = []
    for line in lines:
        if line.strip().startswith("tps:"):
            new_lines.append(f"          tps: {tps}\n")
        else:
            new_lines.append(line)

    with open(file_path, 'w') as file:
        file.writelines(new_lines)

# Verifica conectividade com a rede Besu
def check_network_connection():
    print("Verificando conectividade com a rede Besu...")
    for i in range(10):
        try:
            result = subprocess.run(
                ['curl', '-s', '-X', 'POST', '--data',
                 '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}',
                 'http://127.0.0.1:8545'],
                capture_output=True,
                timeout=5
            )
            if result.returncode == 0:
                print(f"Rede Besu acessivel (tentativa {i+1}/10)")
                return True
        except:
            pass
        print(f"Tentativa {i+1}/10 falhou, aguardando 3s...")
        time.sleep(3)
    print("ERRO: Rede Besu nao esta acessivel")
    return False

# Implanta o contrato Simple na rede
def deploy_simple_contract():
    print("\n" + "="*50)
    print("Implantando contrato Simple na rede...")
    print("="*50)

    if not check_network_connection():
        print("ERRO: Nao foi possivel conectar na rede Besu")
        return False

    # Aguardar estabilizacao adicional
    print("Aguardando estabilizacao adicional (15 segundos)...")
    time.sleep(15)

    # Caminho para o diretório Hardhat
    hardhat_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../Hardhat-contracts'))

    if not os.path.exists(hardhat_dir):
        print(f"ERRO: Diretorio Hardhat-contracts nao encontrado em {hardhat_dir}")
        return False

    # Deploy usando Hardhat Ignition
    print(f"Executando deploy no diretorio: {hardhat_dir}")
    try:
        result = subprocess.run(
            ['npx', 'hardhat', 'ignition', 'deploy', './ignition/modules/Simple.ts',
             '--network', 'besu', '--reset'],
            cwd=hardhat_dir,
            capture_output=True,
            text=True,
            timeout=120,
            input='y\ny\n'  # Confirma automaticamente (duas vezes: deploy e reset)
        )

        if result.returncode != 0:
            print(f"ERRO ao implantar contrato: {result.stderr}")
            return False

        # Extrair endereco do contrato
        import re
        match = re.search(r'simple#simple - (0x[a-fA-F0-9]{40})', result.stdout)
        if not match:
            print("ERRO: Nao foi possivel extrair o endereco do contrato")
            print(result.stdout)
            return False

        contract_address = match.group(1)
        print(f"Contrato Simple implantado em: {contract_address}")

        # Atualizar networkconfig.json
        networkconfig_path = os.path.join(os.path.dirname(__file__),
                                          'networks/besu/networkconfig.json')

        if not os.path.exists(networkconfig_path):
            print(f"ERRO: networkconfig.json nao encontrado em {networkconfig_path}")
            return False

        # Ler arquivo JSON
        import json
        with open(networkconfig_path, 'r') as f:
            config = json.load(f)

        # Atualizar endereco do contrato
        config['ethereum']['contracts']['simple']['address'] = contract_address

        # Salvar arquivo JSON
        with open(networkconfig_path, 'w') as f:
            json.dump(config, f, indent=4)

        print(f"networkconfig.json atualizado com novo endereco")
        print("="*50)
        print("Contrato Simple implantado com sucesso!")
        print("="*50 + "\n")
        return True

    except subprocess.TimeoutExpired:
        print("ERRO: Timeout ao executar deploy do contrato")
        return False
    except Exception as e:
        print(f"ERRO inesperado ao implantar contrato: {e}")
        return False

# Executa o Caliper para uma função e TPS
def run_test(tps, function_name, benchmark_file):
    update_tps_in_file(benchmark_file, tps)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    report_dir = f"reports_htmls/{function_name}"
    os.makedirs(report_dir, exist_ok=True)
    report_path = os.path.join(report_dir, f"{function_name}_report_{tps}_{timestamp}.html")

    cmd = [
        'npx', 'caliper', 'launch', 'manager',
        '--caliper-workspace', './',
        '--caliper-benchconfig', benchmark_file,
        '--caliper-networkconfig', 'networks/besu/networkconfig.json',
        '--caliper-bind-sut', 'besu:latest',
        '--caliper-flow-skip-install'
    ]

    subprocess.run(cmd)

    if os.path.exists('report.html'):
        os.rename('report.html', report_path)
        print(f"✅ Relatório salvo em {report_path}")
    else:
        print(f"Relatorio nao encontrado para {function_name} @ {tps} TPS.")

    # Aguarda para permitir que as conexões WebSocket sejam fechadas
    print(f"Aguardando 10 segundos antes do proximo teste...")
    time.sleep(10)

# Executa todos os testes
if __name__ == "__main__":
    print("\n" + "="*70)
    print("INICIANDO BATERIAS DE TESTES DO CONTRATO SIMPLE")
    print("="*70)
    print(f"Numero de testes por configuracao: {num_testes}")
    print(f"Funcoes a serem testadas: {list(BENCHMARK_FILES.keys())}")
    print("="*70 + "\n")

    # Verificar se a rede esta acessivel antes de iniciar
    if not check_network_connection():
        print("\nERRO CRITICO: Rede Besu nao esta acessivel!")
        print("Por favor, inicie a rede Besu antes de executar os testes.")
        sys.exit(1)

    # Implantar contrato Simple uma vez antes dos testes
    print("\nImplantando contrato Simple antes de iniciar os testes...")
    if not deploy_simple_contract():
        print("\nERRO CRITICO: Falha ao implantar contrato Simple!")
        print("Os testes nao podem continuar sem o contrato implantado.")
        sys.exit(1)

    # Aguardar tempo adicional para estabilizacao
    print("\nAguardando 15 segundos adicionais para estabilizacao da rede...")
    time.sleep(15)

    for i in range(num_testes):
        for function_name, benchmark_file in BENCHMARK_FILES.items():
            match(function_name):
                case "open":
                    TPS_LIST=TPS_LIST_OPEN
                case "query":
                    TPS_LIST=TPS_LIST_QUERY
                case "transfer":
                    TPS_LIST=TPS_LIST_TRANSFER

            print(f"\nIniciando testes para funcao: {function_name}")
            for tps in TPS_LIST:
                run_test(tps, function_name, benchmark_file)

    print("\nConvertendo relatorios HTML para CSV...")
    subprocess.run(["python3", "extract_csv.py"])
    print("Conversao concluida! CSVs gerados em ./reports_csv/")

    print("\n" + "="*70)
    print("TESTES CONCLUIDOS COM SUCESSO!")
    print("="*70)
