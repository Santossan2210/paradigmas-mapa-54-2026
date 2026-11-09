# Telemetria da Frota EcoFleet

Sistema de telemetria para a frota de **vans e bicicletas elétricas** da EcoFleet Solutions S.A. (empresa fictícia de um trabalho acadêmico da disciplina Paradigmas de Linguagens de Programação, MAPA 54/2026).

Autor: **Antonio Santos**

## O que o sistema faz

- Cadastra veículos (van elétrica ou bicicleta elétrica) com modelo, capacidade de carga e bateria atual.
- Registra viagens: informa a distância e o sistema desconta a bateria conforme o tipo do veículo.
- Mostra um painel com a bateria de cada veículo, a autonomia estimada em km e os alertas de bateria crítica (abaixo de 20%).
- Permite ajustar a bateria após uma recarga.
- Guarda o histórico de viagens, com filtro por veículo e por viagens críticas.
- Os dados ficam salvos em um banco SQLite local (`dados/telemetria.db`), que não é enviado ao GitHub.

## Regras de negócio

| Regra | Descrição |
|---|---|
| Validação da bateria | Fora da faixa de 0 a 100, o nível é inválido e fica em **0,0%**. Os limites 0 e 100 são válidos. |
| Consumo da van | 0,5 ponto percentual por km |
| Consumo da bicicleta | 0,2 ponto percentual por km |
| Nova bateria | bateria atual − distância × taxa, gravada sempre pela validação. Se a viagem esgotar a bateria, ela fica em 0,0%. |
| Bateria crítica | abaixo de 20% |

## Como usar

Requisito: **Python 3.10 ou mais recente**. Não é preciso instalar nenhuma biblioteca.

**No Windows:** dê dois cliques em `iniciar.bat`. O navegador abre sozinho no painel do sistema.

**Pelo terminal**, na pasta do projeto:

```
python -m telemetria
```

O sistema abre em `http://127.0.0.1:8000/`. Se a porta estiver ocupada, ele usa a próxima livre. Para encerrar, feche a janela do terminal ou pressione Ctrl+C.

Opções:

```
python -m telemetria --porta 8080        # outra porta
python -m telemetria --sem-navegador     # não abre o navegador
python -m telemetria --banco outro.db    # outro arquivo de dados
```

Primeiro uso: no painel vazio, clique em **Carregar exemplo** para cadastrar a van e a bicicleta do enunciado, ou em **Cadastrar veículo**.

## Demonstração do enunciado (terminal)

Uma van e uma bicicleta saem com 100% de bateria e fazem 50 km cada:

```
python -m telemetria.demo
```

Resultado esperado: van com **75.0%** e bicicleta com **90.0%**.

## Processamento funcional (Parte II da MAPA)

A pasta `processamento/` tem o exemplo de programação funcional: um lote de viagens simuladas passa por `map` (cálculo do consumo), `filter` (viagens críticas) e `reduce` (totais por tipo de veículo). O mesmo pipeline roda em sequência e em paralelo (vários processos), e o programa confere que os totais são idênticos.

```
python -m processamento
```

## Relatório

O relatório da MAPA (.docx) é montado a partir dos textos de `relatorio/conteudo/`, do código-fonte e das saídas guardadas em `relatorio/saidas/`. Nome e RA ficam em `relatorio/identificacao.local.txt`, que não vai para o GitHub.

```
pip install -r relatorio/requirements.txt
copy relatorio\identificacao.exemplo.txt relatorio\identificacao.local.txt
python relatorio/gerar_relatorio.py
```

O arquivo sai em `relatorio/gerado/`. A conferência de cada requisito está em [docs/VALIDACAO_REQUISITOS.md](docs/VALIDACAO_REQUISITOS.md).

## Testes

```
python -m unittest discover -s tests -t . -v
```

Os testes também rodam automaticamente no GitHub Actions a cada envio.

## Estrutura

```
telemetria/
  modelo.py        Veiculo (abstrata), VanEletrica e BicicletaEletrica
  servico.py       operações: cadastro, viagens, ajuste de bateria, histórico, painel
  repositorio.py   gravação em SQLite
  web.py           servidor web local (somente 127.0.0.1)
  paginas.py       páginas HTML
  static/          estilo e script da interface
  demo.py          demonstração do enunciado no terminal
processamento/     exemplo funcional: dados imutáveis, funções puras, map/filter/reduce, paralelismo
relatorio/         gerador do relatório .docx e textos de cada tarefa e tópico
docs/              validação dos requisitos
tests/             testes automáticos (unittest)
```

### Orientação a objetos no modelo

- `Veiculo` é **abstrata** (`abc.ABC`): não pode ser instanciada e obriga cada subclasse a implementar `registrar_viagem`.
- `_id_veiculo`, `_modelo` e `_capacidade_carga` são **protegidos** (um sublinhado).
- `__autonomia_bateria` é **privado** (dois sublinhados): só é lido por `get_autonomia_bateria()` e alterado por `set_autonomia_bateria()`, que aplica a validação.
- `VanEletrica` e `BicicletaEletrica` **herdam** de `Veiculo` e **sobrescrevem** `registrar_viagem` com a sua taxa de consumo (polimorfismo).
