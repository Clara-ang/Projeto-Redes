import socket
import threading
import json
from datetime import datetime

class Servidor:
    def __init__(self, host="0.0.0.0", port=5551):
        self.host = host
        self.port = port
        self.socket_servidor = None
        self.clients = {}
        self.executando = True
        self.lock = threading.Lock()

    def handle_client(self, cliente_socket, addr):
        try:
            print(f"\nConexão de {addr} estabelecida.")
        
        # Configurar timeout
            cliente_socket.settimeout(20)
        
        # Receber dados iniciais
            initial_data = cliente_socket.recv(4096)
            if not initial_data:
                raise ConnectionError("Sem dados iniciais")
            
            client_data = json.loads(initial_data.decode('utf-8'))
        
        # Registrar cliente
            with self.lock:
                self.clients[addr[0]] = {
                    'info': client_data,
                    'socket': cliente_socket,
                    'last_update': datetime.now()
                }
                print(f"Cliente {addr[0]} registrado. Host: {client_data.get('host', '?')}")
        
        # Loop de comunicação
            while self.executando:
                try:
                # Solicitar dados atualizados
                    cliente_socket.sendall(b'REQUEST_DATA')
                
                # Receber resposta
                    data = cliente_socket.recv(4096)
                    if not data:
                        break
                    
                # Processar dados
                    updated_data = json.loads(data.decode('utf-8'))
                    with self.lock:
                        if addr[0] in self.clients:
                            self.clients[addr[0]]['info'] = updated_data
                            self.clients[addr[0]]['last_update'] = datetime.now()
                
                # Intervalo entre solicitações
                    time.sleep(10)
                
                except socket.timeout:
                    continue
                except Exception as e:
                    print(f"Erro na comunicação: {e}")
                    break
                
        except Exception as e:
            print(f"Erro na conexão: {e}")
        finally:
            with self.lock:
                if addr[0] in self.clients:
                    del self.clients[addr[0]]
            cliente_socket.close()
            print(f"Conexão com {addr[0]} encerrada\n")

    def listar_clientes(self):
        with self.lock:
            if not self.clients:
                return "Nenhum cliente conectado"
            
            lista = "\nClientes conectados:\n"
            for i, (ip, data) in enumerate(self.clients.items(), 1):
                lista += f"{i}. {ip} (Host: {data['info'].get('host', '?')})\n"
            return lista

    def detalhar_cliente(self, ip):
        with self.lock:
            if ip not in self.clients:
                return f"\nCliente {ip} não encontrado"
            
            info = self.clients[ip]['info']
            detalhes = (
                f"\nDetalhes do cliente {ip}:\n"
                f"Host: {info.get('host', '?')}\n"
                f"Última atualização: {self.clients[ip]['last_update']}\n\n"
                f"Processadores:\n"
                f"  Núcleos físicos: {info.get('cpu_cores', 'N/A')}\n"
                f"  Núcleos lógicos: {info.get('cpu_count', 'N/A')}\n\n"
                f"Memória RAM:\n"
                
                f"  Livre: {info.get('memory', {}).get('free', 'N/A')} GB\n"
               
                f"Disco:\n"
              
                f"  Livre: {info.get('disks', {}).get('free', 'N/A')} GB\n"
              
                f"Interfaces de Rede:\n"
            )
            
            for interface, ips in info.get('network', {}).get('interfaces', {}).items():
                detalhes += f"  {interface}: {', '.join(ips)}\n"
            
            if info.get('network', {}).get('disabled_interfaces'):
                detalhes += f"\nInterfaces Desativadas:\n  " + ", ".join(info['network']['disabled_interfaces']) + "\n"
            
            detalhes += (
                f"\nPortas Abertas:\n"
                f"  TCP: {', '.join(map(str, info.get('network', {}).get('tcp_ports', [])))}\n"
                f"  UDP: {', '.join(map(str, info.get('network', {}).get('udp_ports', [])))}\n"
            )
            
            return detalhes

    def calcular_medias(self):
        with self.lock:
            if not self.clients:
                return None
            
            medias = {
                'cpu_cores': 0,
                'memory_free': 0,
                'disk_free': 0,
                'total_clients': len(self.clients)
            }
        
            for ip, client in self.clients.items():
            # Usar info diretamente em vez de data[-1]
                info = client['info']
                medias['cpu_cores'] += info.get('cpu_cores', 0)
                medias['memory_free'] += info.get('memory', {}).get('free', 0)
                medias['disk_free'] += info.get('disks', {}).get('free', 0)
        
            if medias['total_clients'] > 0:
                medias['cpu_cores'] /= medias['total_clients']
                medias['memory_free'] /= medias['total_clients']
                medias['disk_free'] /= medias['total_clients']
        
            return medias


    def menu_interativo(self):
        while self.executando:
            try:
                print("\n--- Menu do Servidor ---")
                print("1. Listar clientes conectados")
                print("2. Detalhar um cliente")
                print("3. Mostrar médias dos dados")
                print("4. Parar servidor")

                opcao = input("Escolha uma opção: ").strip()
                
                if opcao == "1":
                    print(self.listar_clientes())
                elif opcao == "2":
                    print(self.listar_clientes())
                    ip = input("Digite o IP do cliente: ").strip()
                    print(self.detalhar_cliente(ip))
                elif opcao == "3":
                    medias = self.calcular_medias()
                    if medias:
                        print(f"\nMédias dos dados:")
                        print(f"Núcleos de CPU: {medias['cpu_cores']:.1f}")
                        print(f"Memória RAM livre: {medias['memory_free']:.1f} GB")
                        print(f"Espaço em disco livre: {medias['disk_free']:.1f} GB")
                        print(f"Total de clientes: {medias['total_clients']}")
                    else:
                        print("Nenhum cliente conectado para calcular médias")
                elif opcao == "4":
                    self.parar_servidor()
                    break
                else:
                    print("Opção inválida")
                    
            except Exception as e:
                print(f"Erro no menu: {str(e)}")

    def iniciar_servidor(self):
        self.socket_servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket_servidor.bind((self.host, self.port))
        self.socket_servidor.listen(5)
        print(f"\nServidor iniciado em {self.host}:{self.port}")

        threading.Thread(target=self.menu_interativo, daemon=True).start()
        
        while self.executando:
            try:
                cliente_socket, addr = self.socket_servidor.accept()
                threading.Thread(target=self.handle_client, args=(cliente_socket, addr)).start()
            except OSError:
                break

        print("Servidor encerrado")

    def parar_servidor(self):
        print("\nEncerrando servidor...")
        self.executando = False
        with self.lock:
            for client in self.clients.values():
                if 'socket' in client:
                    client['socket'].close()
        self.socket_servidor.close()

if __name__ == "__main__":
    import time
    servidor = Servidor()
    try:
        servidor.iniciar_servidor()
    except KeyboardInterrupt:
        servidor.parar_servidor()