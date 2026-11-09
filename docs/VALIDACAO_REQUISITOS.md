# Validação dos requisitos

Conferência de cada exigência do PROJETO (Tarefas 1 a 3) e da orientação da MAPA (Tópicos 1 a 5) com o que está implementado neste repositório.

Legenda: **OK** atendido · **Adaptado** atendido com o equivalente em Python · **Atenção** ponto que depende de decisão do autor

Autor: Antonio Santos

## Decisão de linguagem

O PROJETO pede Java. Por decisão do autor, a implementação foi feita em Python. Cada recurso do Java exigido no enunciado tem um equivalente direto em Python, indicado na tabela. O risco de a correção exigir Java ao pé da letra foi assumido pelo autor.

## Tarefa 1: Modelagem conceitual

| Requisito | Situação | Onde |
|---|---|---|
| Superclasse abstrata `Veiculo` | OK | `telemetria/modelo.py`, `class Veiculo(ABC)` |
| Subclasses concretas `VanEletrica` e `BicicletaEletrica` | OK | `telemetria/modelo.py` |
| `idVeiculo` int protected | Adaptado | `self._id_veiculo` (um sublinhado, convenção de protegido) |
| `modelo` String protected | Adaptado | `self._modelo` |
| `capacidadeCarga` double protected | Adaptado | `self._capacidade_carga` |
| `autonomiaBateria` double private | Adaptado | `self.__autonomia_bateria` (dois sublinhados, *name mangling*) |
| `placaIdentificacao` String private | Adaptado | `self.__placa_identificacao` |
| `limiteVelocidadeAssistida` double private | Adaptado | `self.__limite_velocidade_assistida` |
| Justificativa da classe abstrata | OK | relatório, Tarefa 1 |
| Explicação de protected e private | OK | relatório, Tarefa 1 |

## Tarefa 2: Implementação

| Requisito | Situação | Onde |
|---|---|---|
| Pacote `telemetria` | OK | pasta `telemetria/` |
| `Veiculo` declarada abstrata | Adaptado | herda de `abc.ABC`; `Veiculo()` gera `TypeError` (teste `test_modelo`) |
| Construtor sem parâmetros com 0, 0.0 e texto vazio | OK | `Veiculo.__init__(self)` |
| `getAutonomiaBateria()` público | Adaptado | `get_autonomia_bateria()` |
| `setAutonomiaBateria(double bateria)` com a condicional | Adaptado | `set_autonomia_bateria(bateria)`: fora de 0.0 a 100.0 grava 0.0 |
| Método abstrato `registrarViagem(double distancia)` | Adaptado | `@abstractmethod registrar_viagem(distancia)` |
| Subclasses herdam com `extends` | Adaptado | `class VanEletrica(Veiculo)` |
| Construtor das subclasses inicializa os protegidos e usa o setter para a bateria | OK | `__init__` de cada subclasse |
| `@Override` em `registrarViagem` | Adaptado | `@override` (`typing.override`) |
| Van consome 0.5 por km; bicicleta 0.2 por km | OK | `TAXA_CONSUMO`; testes `test_modelo` |
| Novo nível calculado com o getter e gravado com o setter | OK | `registrar_viagem` |
| Mensagem no console com distância e bateria resultante | OK | `print` dentro de `registrar_viagem` |
| `Main` com `main`, instancia os dois, 100.0 de bateria, viagem de 50.0 km, mostra o nível final | Adaptado | `telemetria/demo.py`, função `main()`: resultado 75.0% e 90.0% |
| Código testado antes do envio | OK | 46 testes automáticos e GitHub Actions |

## Tarefa 3: Justificativa

| Requisito | Situação | Onde |
|---|---|---|
| Texto de 10 a 20 linhas sobre o setter, a organização dos atributos, `registrarViagem` e o construtor | OK | relatório, Tarefa 3 (o gerador confere o tamanho) |

## Produto final

| Requisito | Situação | Onde |
|---|---|---|
| Arquivo único com Identificação (nome, RA), Tarefas 1, 2 e 3 | OK | `relatorio/gerar_relatorio.py` gera o .docx |
| Nome e RA fora do repositório público | OK | ficam só em `relatorio/identificacao.local.txt`, ignorado pelo Git |
| Código organizado e indentado | OK | o código entra no relatório direto dos arquivos-fonte |
| Autoria registrada apenas como Antonio Santos | OK | código, README e relatório |

## Orientação da MAPA (Parte II)

| Requisito | Situação | Onde |
|---|---|---|
| Tópico 1: paradigma funcional, imutabilidade, funções puras, avaliação preguiçosa, ordem superior | OK | relatório, Tópico 1 |
| Tópico 2: comparação com o imperativo, vantagens e desvantagens no cenário | OK | relatório, Tópico 2 |
| Tópico 3: exemplo prático com MAP, FILTER e REDUCE, linguagem apresentada, explicação e onde está cada conceito | OK | pasta `processamento/` e relatório, Tópico 3 |
| Tópico 4: aplicabilidade ao cenário (paralelismo, volume, pipeline, efeitos colaterais, previsibilidade) | OK | relatório, Tópico 4 |
| Tópico 5: conclusão crítica (desempenho, manutenção, equipe, curva de aprendizado, adequação) | OK | relatório, Tópico 5 |
| Código com a assinatura de Antonio Santos | OK | cabeçalho de cada arquivo |
| Teste em ambiente remoto e gratuito | OK | GitHub Actions (`.github/workflows/testes.yml`) |
| Repositório no GitHub de Santossan2210 | OK | `Santossan2210/paradigmas-mapa-54-2026` |
| Referência ao livro da disciplina, sem cópia literal | OK | relatório, Referências |

## Pontos de atenção

1. **Linguagem.** O PROJETO pede Java e a "Execução em ambiente compatível com Java". A entrega está em Python.
2. **Nomes.** O enunciado pede conferir se os nomes de classes, atributos e métodos correspondem aos definidos. As classes têm os mesmos nomes; atributos e métodos seguem o padrão do Python (`set_autonomia_bateria` em vez de `setAutonomiaBateria`). O relatório traz a tabela de correspondência.
3. **Classe Main.** Em Python não há classe obrigatória para o ponto de entrada. O papel da `Main` é feito pela função `main()` do módulo `telemetria/demo.py`.
