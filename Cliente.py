import socket
import psutil
import json
import time
from datetime import datetime

class Cliente:
    def __init__(self, server_host='127.0.0.1', server_port=5551, intervalo=30):
        self.server_host = server_host
        self.server_port = server_port
        self.intervalo = intervalo # Intervalo de envio de dados
        self.executando = False # Controle do loop de monitoramento


    def coletar_dados(self):
        try:
            # Coleta de dados do sistema
            memoria = psutil.virtual_memory()
            disco = psutil.disk_usage("C:\\")
            
            # Coleta de informações de rede
            interfaces = psutil.net_if_addrs() # Status das interfaces
            stats = psutil.net_if_stats() # Status das interfaces
            interfaces_ativas = {}
            interfaces_desativadas = []
            
             # Filtra interfaces ativas (com IP e status UP)
            for interface, addrs in interfaces.items():
                ips = [addr.address for addr in addrs if addr.family == socket.AF_INET]
                if stats[interface].isup and ips:
                    interfaces_ativas[interface] = ips
                else:
                    interfaces_desativadas.append(interface)
            
            # Coleta de portas abertas
            conexoes = psutil.net_connections()
            portas_tcp = {conn.laddr.port for conn in conexoes 
                         if conn.status == 'LISTEN' and conn.type == socket.SOCK_STREAM}
            portas_udp = {conn.laddr.port for conn in conexoes 
                         if conn.status == 'LISTEN' and conn.type == socket.SOCK_DGRAM}

            return {
                "host": socket.gethostname(),
                "cpu_count": psutil.cpu_count(logical=True),
                "cpu_cores": psutil.cpu_count(logical=False),
                "memory": {
                    
                    "free": memoria.available // (1024 ** 3),
                    
                },
                "disks": {
                    
                    "free": disco.free // (1024 ** 3),  
                },
                "network": {
                    "interfaces": interfaces_ativas,
                    "disabled_interfaces": interfaces_desativadas,
                    "tcp_ports": list(portas_tcp),
                    "udp_ports": list(portas_udp)
                },
                "timestamp": datetime.now().isoformat() # Data/hora da coleta
            }
        except Exception as e:
            print(f"Erro ao coletar dados: {e}")
            return None

    def enviar_dados(self, dados):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(15)  # Timeout de 15s para evitar travamentos
                s.connect((self.server_host, self.server_port)) # Conecta ao servidor
            
                # Enviar dados iniciais
                s.sendall(json.dumps(dados).encode('utf-8'))
            
                # Mantém conexão ativa para responder a solicitações do servidor
                while self.executando:
                    try:
                        data = s.recv(1024)
                        if data == b'REQUEST_DATA':
                            # Enviar dados atualizados
                            novos_dados = self.coletar_dados()
                            s.sendall(json.dumps(novos_dados).encode('utf-8'))
                        elif not data:
                            break
                        
                    except socket.timeout:
                    # Timeout normal, continuar aguardando
                        continue
                    except Exception as e:
                        print(f"Erro na comunicação: {e}")
                        break
            
            return True
            
        except Exception as e:
            print(f"Erro de conexão: {e}")
            return False
    def iniciar_monitoramento(self):
        self.executando = True
        print("Iniciando monitoramento...")
        
        while self.executando:
            dados = self.coletar_dados()
            if dados:
                print(f"Enviando dados em {datetime.now().strftime('%H:%M:%S')}...")
                if not self.enviar_dados(dados):
                    print("Tentando novamente em 5 segundos...")
                    time.sleep(5)
                    continue
            
            time.sleep(self.intervalo)

    def parar_monitoramento(self):
        self.executando = False
        print("Monitoramento encerrado")

if __name__ == "__main__":
    try:
        cliente = Cliente(server_host='127.0.0.1', server_port=5551, intervalo=30)
        cliente.iniciar_monitoramento()
    except KeyboardInterrupt: # Se usuário pressionar Ctrl+C
        cliente.parar_monitoramento()