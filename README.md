# 🖨️ Monitor Pro - Gestão de Ativos de Impressão (SNMP)

![Python](https://img.shields.io/badge/python-3.12%2B-blue)
![Status](https://img.shields.io/badge/status-stable-green)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

> Uma ferramenta CLI (Interface de Linha de Comando) desenvolvida para departamentos de TI monitorarem, auditarem e gerenciarem parques de impressão corporativos em tempo real.

## 📖 Sobre o Projeto

O **Monitor Pro** automatiza a coleta de dados técnicos de impressoras de rede utilizando o protocolo **SNMP**. Diferente de soluções proprietárias pesadas, este script é leve, assíncrono e focado na agilidade do suporte técnico e na auditoria de contratos de outsourcing (contagem de páginas).

Foi desenhado para rodar em servidores Linux ou estações de trabalho de SysAdmins, permitindo uma visão unificada de suprimentos e hardware.

*![alt text](/Img/image.png)*

## 🚀 Funcionalidades Principais

* **Dashboard em Terminal:** Monitoramento em tempo real com indicadores visuais de status (🟢 Online / 🔴 Offline) e níveis de toner.
* **Filtros por Setor:** Capacidade de visualizar o parque completo ou filtrar impressoras por departamento (ex: *RH, Marketing, Financeiro*).
* **Relatórios de Auditoria (PDF):** Geração automática de arquivos PDF formatados com Data/Hora, contadores totais (*Life Count*), Serial Number e Nível de Suprimentos.
* **Gestão de Inventário:** Leitura automática de Modelo (Firmware), Número de Série e Memória RAM instalada.
* **Alta Performance:** Utiliza `asyncio` para consultar dezenas de impressoras simultaneamente sem travar a interface.
* **Configuração Dinâmica:** Menu integrado para Adicionar/Remover impressoras, salvando os dados em um arquivo JSON local.

## 🛠️ Tecnologias Utilizadas

* **Python 3.12+**
* **PySNMP v7:** Para comunicação de rede via protocolo SNMP v1/v2c.
* **ReportLab:** Para geração programática de relatórios em PDF.
* **AsyncIO:** Para execução paralela e não-bloqueante de tarefas de rede.

## ⚙️ Pré-requisitos

1.  **Acesso de Rede:** O computador onde o script roda deve ter acesso às impressoras (ping).
2.  **Porta 161 (UDP):** Deve estar liberada no Firewall.
3.  **SNMP Habilitado:** As impressoras devem estar com SNMP ativo e comunidade definida como `public` (padrão do script).
4.  **Nota sobre USB:** Impressoras conectadas apenas via USB **não** são suportadas.

## 📦 Instalação e Execução

### Opção 1: Executável (Windows)
Para usuários que não possuem Python instalado, baixe a versão compilada na aba **[Releases](https://github.com/Saguicangaceiro/projeto_antigo/releases)** deste repositório.

### Opção 2: Via Código Fonte (Desenvolvedor)
1.  **Clone o repositório:**
    ```bash
    git clone [https://github.com/Saguicangaceiro/projeto_antigo.git](https://github.com/Saguicangaceiro/projeto_antigo.git)
    cd projeto_antigo
    ```

2.  **Ambiente Virtual e Dependências:**
    ```bash
    python -m venv venv
    # Ative o venv (Windows: .\venv\Scripts\activate | Linux: source venv/bin/activate)
    pip install -r requirements.txt
    ```

3.  **Executar:**
    ```bash
    python monitor_pro.py
    ```

## ✒️ Créditos e Licença

Este projeto está sob a licença MIT.

* **Ícone do Aplicativo:** Criado por [Eucalyp](https://www.flaticon.com/br/autores/eucalyp) - [Flaticon](https://www.flaticon.com/br/icone-gratis/impressora-multifuncoes_1547967).
* **Desenvolvedor:** [Saguicangaceiro](https://github.com/Saguicangaceiro)

---
