# 🚨 Plataforma de Análise Preditiva de Crimes – PE / MVI

> **Projeto Acadêmico - Entrega 1**  
> Disciplina: Plataforma de Análise Preditiva de Crimes  
> **MVP Supervisionado para Predição de Risco Alto de MVI**

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Entrega%201%20✅-success.svg)]()

## 📋 Sumário Executivo

Este projeto implementa um **sistema de alerta preditivo** para identificar municípios com alto risco de **Mortes Violentas Intencionais (MVI)** no próximo mês, utilizando dados reais da **PCPE/SDS-PE** (Polícia Civil de Pernambuco/Secretaria de Defesa Social).

### 🎯 Objetivo Principal
Desenvolver um modelo de machine learning capaz de **classificar se o mês seguinte terá alto risco de MVI** em cada município de Pernambuco, baseado em padrões históricos e sazonais.

### 🔍 Definição do Problema
- **Rótulo**: `alto_risco_mvi_next = 1` se MVI_{t+1} ≥ percentil 75 do histórico do próprio município
- **Granularidade**: Agregação mensal por município
- **Cobertura**: 185 municípios de Pernambuco (2004-2025)

---

## 📊 Dados e Metodologia

### 📁 Fonte dos Dados
- **Origem**: Planilha oficial da PCPE/SDS-PE (arquivo `.xlsx`)
- **Período**: Janeiro/2004 a Julho/2025 (varia por município)
- **Granularidade**: Microdados agregados por mês × município

### 🏗️ Features Engineering
O dataset processado (`data/processed/mvi_pe_features.csv`) contém:

| Categoria | Features | Descrição |
|-----------|----------|-----------|
| **Identificação** | `municipio`, `date`, `ano`, `mes` | Metadados temporais e geográficos |
| **Histórico** | `lag1`, `ma3`, `ma6`, `chg` | Lag 1 mês, médias móveis (3 e 6 meses), variação m/m-1 |
| **Sazonalidade** | `mes_sin`, `mes_cos` | Componentes cíclicos mensais |
| **Alvo** | `alto_risco_mvi_next` | Rótulo binário (0/1) |

### 🔒 Conformidade LGPD
- ✅ Trabalhamos apenas com **contagens agregadas** por mês/município
- ✅ **Nenhuma informação pessoal** é coletada ou exposta
- ✅ Dados originais ficam em `data/raw/` (ignorado pelo Git)

---

## 🗂️ Estrutura do Projeto

```
crime-pe-entrega1/
├── 📁 data/
│   ├── raw/                    
│   └── processed/              # 📊 mvi_pe_features.csv (gerado)
├── 📁 notebooks/
│   ├── 01_eda.ipynb           # 📈 Análise exploratória
│   └── 02_modelagem.ipynb     # 🤖 Baseline + modelos + métricas
├── 📁 reports/
│   ├── figuras/               # 📊 Gráficos e matrizes
│   ├── metrics.json           # 📋 Tabela de métricas finais
│   └── classif_report_*.txt   # 📄 Relatórios detalhados
├── 📁 src/
│   └── ingest_pcpe_mvi.py     # 🔄 Pipeline de ingestão
├── requirements.txt           # 📦 Dependências
└── README.md                  # 📖 Este arquivo
```

---

## ⚙️ Configuração do Ambiente

### Pré-requisitos
- Python 3.8+
- pip (gerenciador de pacotes)

### 🚀 Instalação

```bash
# 1. Clone o repositório
git clone <[url-do-repositorio](https://github.com/luisgabrieltech/crime-pe-entrega1.git)>
cd crime-pe-entrega1

# 2. Crie e ative o ambiente virtual
python -m venv .venv

# Windows (PowerShell)
.\.venv\Scripts\activate

# Linux/macOS
source .venv/bin/activate

# 3. Instale as dependências
pip install -r requirements.txt
```

### 📦 Dependências Principais
- `pandas>=2.0` - Manipulação de dados
- `numpy>=1.24` - Computação numérica
- `scikit-learn>=1.3` - Machine Learning
- `matplotlib>=3.7` - Visualizações
- `openpyxl>=3.1` - Leitura de arquivos Excel
- `notebook>=7.0` - Jupyter notebooks

---

## ▶️ Como Reproduzir os Resultados

### 1️⃣ Preparação dos Dados
```bash
# Coloque o arquivo XLSX oficial em data/raw/
# Exemplo: MICRODADOS_DE_MVI_JAN_2004_A_JUL_2025.xlsx

# Execute o pipeline de ingestão
python src/ingest_pcpe_mvi.py
```

**Saída**: `data/processed/mvi_pe_features.csv`

### 2️⃣ Análise Exploratória (EDA)
```bash
# Abra e execute o notebook
jupyter notebook notebooks/01_eda.ipynb
```

**Gera**: 
- `reports/figuras/serie_mensal_pe.png`
- `reports/figuras/heatmap_ano_mes.png`
- `reports/figuras/top10_municipios.png`
- `reports/figuras/distribuicao_alvo.png`

### 3️⃣ Modelagem e Avaliação
```bash
# Abra e execute o notebook
jupyter notebook notebooks/02_modelagem.ipynb
```

**Gera**:
- `reports/metrics.json`
- `reports/figuras/*.png` (matrizes de confusão)
- `reports/classif_report_*.txt`

---

## 📈 Resultados dos Modelos

### 🎯 Métricas de Performance (Teste 2023+)

| Modelo | Accuracy | F1-macro |
|--------|----------|----------|
| **Baseline** | 0.617 | 0.382 |
| **LogisticRegression** | 0.694 | 0.660 |
| **RandomForest (tuned)** | 0.659 | 0.624 |
| **LogisticRegression @0.48** | 0.688 | 0.662 |

### 📊 Principais Descobertas

1. **Regressão Logística** apresenta melhor performance geral
2. **Ajuste de threshold** (≈0.48) melhora levemente o F1-score
3. **Erros concentrados** em Falsos Negativos (meses de alto risco não detectados)
4. **Sazonalidade** e **histórico recente** são features importantes

### 🔍 Validação Temporal
- **Treino**: ≤ 2022
- **Teste**: ≥ 2023
- **Métrica principal**: F1-macro (classes desbalanceadas)

---

## 🔧 Pipeline Técnico

### 📥 Ingestão (`src/ingest_pcpe_mvi.py`)
```python
# Funcionalidades robustas:
✅ Varre múltiplas abas do XLSX
✅ Detecta cabeçalho automaticamente
✅ Normaliza nomes de colunas
✅ Agrega dados mês × município
✅ Gera features de histórico e sazonalidade
✅ Cria rótulo baseado no percentil 75
```

### 🛠️ Pré-processamento
- **StandardScaler** para features numéricas
- **OneHotEncoder** para município
- **Validação temporal** (evita vazamento de dados)

### 🎲 Reprodutibilidade
- **Seed fixa**: 42
- **Cutoff temporal**: 2023-01-01
- **Dependências**: `requirements.txt`

---

## 🚨 Análise de Impacto

### 📍 Cobertura Geográfica
- **185 municípios** de Pernambuco
- **Cobertura temporal** variável por município
- **Dados mais recentes**: Julho/2025

### 🎯 Aplicabilidade
- **Sistema de alerta** para gestores públicos
- **Alocação de recursos** de segurança
- **Planejamento preventivo** por município

---

## 📚 Documentação Adicional

### 📖 Relatórios Gerados
- `reports/classif_report_*.txt` - Relatórios detalhados por modelo
- `reports/metrics.json` - Métricas consolidadas
- `reports/figuras/` - Visualizações e matrizes de confusão

### 📊 Análises Específicas
- `reports/cobertura_municipios.csv` - Cobertura temporal por município
- `reports/municipios_maior_proporcao_alto_risco.csv` - Municípios críticos
- `reports/municipios_menor_proporcao_alto_risco.csv` - Municípios estáveis

---

## 🤝 Contribuição

### 📋 Checklist da Entrega 1
- [x] **Problema + storytelling** (notebook e slides)
- [x] **Dataset real + EDA** completo
- [x] **Pipeline de pré-processamento** robusto
- [x] **Baseline + 2 modelos** com métricas
- [x] **Avaliação** (F1-macro, matrizes, análise de erros)
- [x] **Reprodutibilidade** (seed, cutoff, requirements, estrutura)
- [x] **LGPD/Ética** documentado
- [x] **Slides** com gráficos e resultados

---

## 📞 Contato e Suporte

### 👥 Equipe do Projeto
- **Disciplina**: Plataforma de Análise Preditiva de Crimes
- **Instituição**: [Faculdade Senac Pernambuco]
- **Período**: [2025.2]

---

## 📄 Licença

Este projeto é desenvolvido para fins acadêmicos. Os dados originais pertencem à **PCPE/SDS-PE** e devem ser utilizados conforme as políticas de uso da instituição.

---

<div align="center">

**🚨 Plataforma de Análise Preditiva de Crimes – PE / MVI**  
*Entrega 1 - MVP Supervisionado*

[⬆️ Voltar ao topo](#-plataforma-de-análise-preditiva-de-crimes--pe--mvi)

</div>
